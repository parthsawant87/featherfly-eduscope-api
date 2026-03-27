# api_server_eduscope.py — EduScope FastAPI Server
# Endpoints: /identify /ask-tutor /quiz /practical-record /stream /latest /health /spc
# Run: gunicorn api_server_eduscope:app --workers 1 --bind 0.0.0.0:8001
# NOTE: gunicorn --workers 1 is intentional for RPi Zero 2W (512MB RAM)
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import numpy as np, io, time, os, json, asyncio
from PIL import Image
import config as cfg
from eduscope_rca import identify
from eduscope_claude import (explain_specimen, answer_student_question,
                               generate_quiz, generate_practical_record)
from db_logger import log_prediction
from active_learner import flag_if_uncertain

app = FastAPI(title="Featherfly EduScope API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ── Model loading ─────────────────────────────────────────────────────────────
_TFLITE = os.path.join(cfg.EXPORT_DIR, cfg.TFLITE_MODEL_NAME)
try:
    import tflite_runtime.interpreter as _tflite_lib
except:
    import tensorflow.lite as _tflite_lib
_interp = _tflite_lib.Interpreter(model_path=_TFLITE)
_interp.allocate_tensors()
_IN  = _interp.get_input_details()[0]
_OUT = _interp.get_output_details()[0]
_latest: dict = {}                          # stores last inference result for /latest and SSE
_sse_subscribers: list = []                 # list of async queues for SSE clients


def preprocess(img: Image.Image) -> np.ndarray:
    """Resize image, normalise with ImageNet mean/std, quantise to INT8."""
    # ← fixed: original was missing the resize + numpy steps
    img_resized = img.resize((cfg.IMG_SIZE, cfg.IMG_SIZE))
    arr = np.array(img_resized, dtype=np.float32) / 255.0
    arr = (arr - np.array(cfg.IMG_MEAN)) / np.array(cfg.IMG_STD)
    arr = np.transpose(arr, (2, 0, 1))    # HWC → CHW
    arr = arr[np.newaxis]                  # [1, 3, 224, 224]
    in_sc, in_zp = _IN["quantization"]
    return (arr / in_sc + in_zp).astype(np.int8)


def run_inference(img: Image.Image):
    """Run TFLite inference. Returns (class_name, confidence, probabilities_dict)."""
    inp = preprocess(img)
    _interp.set_tensor(_IN["index"], inp)
    _interp.invoke()
    out_sc, out_zp = _OUT["quantization"]
    q      = _interp.get_tensor(_OUT["index"])[0]
    logits = (q.astype(np.float32) - out_zp) * out_sc   # ← fixed: was used before definition
    probs  = np.exp(logits) / np.exp(logits).sum()
    pi     = int(probs.argmax())
    cls    = cfg.CLASS_NAMES[pi]
    conf   = float(probs[pi])
    probs_dict = {cfg.CLASS_NAMES[i]: float(probs[i]) for i in range(cfg.NUM_CLASSES)}
    return cls, conf, probs_dict


async def _notify_sse_subscribers(result: dict):
    """Push result to all connected SSE clients immediately."""
    dead = []
    for q in _sse_subscribers:
        try:
            await q.put(result)
        except:
            dead.append(q)
    for q in dead:
        _sse_subscribers.remove(q)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.post("/identify")
async def identify_specimen(file: UploadFile = File(...)):
    """Identify a microscope specimen from an uploaded image."""
    global _latest
    try:
        data = await file.read()
        img  = Image.open(io.BytesIO(data)).convert("RGB")
        cls, conf, probs = run_inference(img)
        bio         = identify(cls, conf)
        explanation = explain_specimen(bio)
        result = {
            "specimen":       cls,
            "common_name":    bio.common_name,
            "confidence":     round(conf, 4),
            "cbse_chapter":   bio.cbse_chapter,
            "what_you_see":   bio.what_you_see,
            "stain":          bio.stain,
            "magnification":  bio.magnification,
            "key_structures": bio.key_structures,
            "fun_fact":       bio.fun_fact,
            "explanation":    explanation,
            "low_confidence": bio.low_confidence,
            "probabilities":  probs,
            "timestamp":      time.time(),
        }
        _latest = result
        log_prediction(result, module="eduscope")
        flag_if_uncertain(result)
        # Push to SSE subscribers — instant update to dashboard
        await _notify_sse_subscribers(result)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(500, str(e))


class TutorRequest(BaseModel):
    question: str
    specimen: str = ""
    history:  list = []

@app.post("/ask-tutor")
async def ask_tutor(req: TutorRequest):
    sp  = req.specimen or _latest.get("specimen", "ONION_CELL")
    bio = identify(sp, 1.0)
    answer = answer_student_question(req.question, bio, req.history)
    return {"answer": answer, "specimen": sp}


class QuizRequest(BaseModel):
    specimen:      str = ""
    num_questions: int = 4

@app.post("/quiz")
async def get_quiz(req: QuizRequest):
    sp  = req.specimen or _latest.get("specimen", "ONION_CELL")
    bio = identify(sp, 1.0)
    qs  = generate_quiz(bio, req.num_questions)
    return {"specimen": sp, "common_name": bio.common_name, "questions": qs}


class PracticalRequest(BaseModel):
    student_name: str
    school_name:  str
    specimen:     str = ""

@app.post("/practical-record")
async def practical_record(req: PracticalRequest):
    sp   = req.specimen or _latest.get("specimen", "ONION_CELL")
    bio  = identify(sp, 1.0)
    text = generate_practical_record(bio, req.student_name, req.school_name)
    return {"record": text, "specimen": sp, "common_name": bio.common_name}


@app.get("/stream")
async def sse_stream():
    """Server-Sent Events endpoint.
    Dashboard connects once and receives instant push when specimen is identified.
    Replaces setInterval polling — latency drops from 2–3s to ~50ms.

    Usage (JavaScript):
        const es = new EventSource(API + '/stream');
        es.onmessage = (e) => {
            const data = JSON.parse(e.data);
            showResult(data.specimen, data.confidence);
        };
    """
    queue = asyncio.Queue()
    _sse_subscribers.append(queue)

    async def event_generator():
        # Send initial heartbeat so client knows connection is live
        yield ": heartbeat\n\n"
        if _latest:
            yield f"data: {json.dumps(_latest)}\n\n"
        try:
            while True:
                try:
                    # Wait for new result, send heartbeat every 15s to keep connection alive
                    result = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(result)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"   # keepalive comment — not a data event
        except asyncio.CancelledError:
            _sse_subscribers.remove(queue)
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering if proxied
        }
    )


@app.get("/latest")
def latest():
    """Returns last inference result. Used as SSE fallback and for polling."""
    if not _latest:
        return {"status": "no_result_yet"}
    return JSONResponse(_latest)


@app.get("/health")
def health():
    return {
        "status":   "ok",
        "model":   "eduscope-tflite-int8",
        "classes": cfg.NUM_CLASSES,
        "version": "1.0.0",
    }
# api_server_eduscope.py — EduScope FastAPI Server
# Endpoints: /identify /ask-tutor /quiz /practical-record /stream /latest /health /spc
# Run: gunicorn api_server_eduscope:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
# NOTE: ONNX inference runs on WhiteMouse Pod (RPi Zero 2W) — NOT on Render.
#       Render hosts only the Claude tutor, quiz, practical-record, SSE, and health endpoints.
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import numpy as np, io, time, os, json, asyncio
from PIL import Image
import eduscope_config as cfg
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

# ── Model loading (RPi only — stubbed on Render) ──────────────────────────────
# ONNX inference runs on the WhiteMouse Pod hardware.
# On Render (cloud), _interp is None and /identify returns 503.
_interp = None
_IN     = None
_OUT    = None

try:
    import onnxruntime as ort
    
    _ONNX_PATH = os.path.join(cfg.EXPORT_DIR, "eduscope_mobilenet_int8.onnx")
    if os.path.exists(_ONNX_PATH):
        _interp = ort.InferenceSession(_ONNX_PATH)
        _IN  = _interp.get_inputs()[0]
        _OUT = _interp.get_outputs()[0]
        print(f"[model] ✓ ONNX model loaded from {_ONNX_PATH}")
        print(f"[model]   Input:  {_IN.name}, shape={_IN.shape}, dtype={_IN.type}")
        print(f"[model]   Output: {_OUT.name}, shape={_OUT.shape}, dtype={_OUT.type}")
    else:
        print(f"[model] ⚠ Model file not found: {_ONNX_PATH} — inference disabled (cloud mode)")
except Exception as e:
    print(f"[model] ⚠ ONNX runtime not available — inference disabled (cloud mode): {e}")

_latest: dict = {}          # stores last inference result for /latest and SSE
_sse_subscribers: list = [] # list of async queues for SSE clients


def preprocess(img: Image.Image) -> np.ndarray:
    """Resize image, normalize with ImageNet mean/std, return FLOAT32 for ONNX."""
    img_resized = img.resize((cfg.IMG_SIZE, cfg.IMG_SIZE))
    arr = np.array(img_resized, dtype=np.float32) / 255.0
    arr = (arr - np.array(cfg.IMG_MEAN)) / np.array(cfg.IMG_STD)
    arr = np.transpose(arr, (2, 0, 1))    # HWC → CHW
    arr = arr[np.newaxis]                  # [1, 3, 224, 224]
    return arr.astype(np.float32)


def run_inference(img: Image.Image):
    """Run ONNX inference. Returns (class_name, confidence, probabilities_dict)."""
    if _interp is None:
        raise RuntimeError("ONNX model not available on this server — run on WhiteMouse Pod")
    
    inp = preprocess(img)
    
    # Run ONNX inference
    outputs = _interp.run([_OUT.name], {_IN.name: inp})
    logits = outputs[0][0]  # Shape: [num_classes]
    
    # Convert logits to probabilities
    probs = np.exp(logits) / np.exp(logits).sum()
    pi = int(probs.argmax())
    cls = cfg.CLASS_NAMES[pi]
    conf = float(probs[pi])
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
    """Identify a microscope specimen from an uploaded image.
    Only works when running on WhiteMouse Pod with ONNX model present.
    Returns 503 on Render (cloud) — inference is edge-only.
    """
    if _interp is None:
        raise HTTPException(
            status_code=503,
            detail="Inference not available on cloud server — connect WhiteMouse Pod for local inference"
        )
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
    Replaces setInterval polling — latency drops from 2-3s to ~50ms.

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
        yield ": heartbeat\n\n"
        if _latest:
            yield f"data: {json.dumps(_latest)}\n\n"
        try:
            while True:
                try:
                    result = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(result)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            if queue in _sse_subscribers:
                _sse_subscribers.remove(queue)
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
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
        "status":        "ok",
        "model":         "eduscope-onnx-int8",
        "inference":     "available" if _interp else "cloud-mode (RPi only)",
        "classes":       cfg.NUM_CLASSES,
        "version":       "1.0.0",
    }
# eduscope_claude.py — EduScope Claude Biology Tutor
# Uses claude-haiku-4-5-20251001 for all 4 functions.
# Cost: ~₹0.008 per call. Budget capped at 20 calls/device/day via db_logger.
import anthropic, os, json
from eduscope_rca import BioResult
from db_logger import can_call_claude, record_claude_call

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL  = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are EduScope, an AI biology lab assistant for Indian school students (Classes 8–12, NCERT curriculum).
Your personality:
- Friendly, encouraging, curious — you love biology
- Explain things clearly for a 14–17 year old student
- Always connect observations to NCERT chapters
- Use relatable analogies (Indian context where possible)
- Keep explanations under 120 words unless asked for more
- For quiz questions, always give CBSE-style questions with one correct answer
- Never use jargon without explaining it
- End explanations with one interesting fact to spark curiosity
You are speaking directly to a student looking at a microscope slide right now.
"""


def explain_specimen(bio: BioResult) -> str:
    """Generate a friendly student-facing explanation of the identified specimen."""
    if not can_call_claude():
        return (f"You are looking at {bio.common_name}. "
                f"{bio.fun_fact} NCERT: {bio.cbse_chapter}. "
                f"Key structures: {', '.join(bio.key_structures[:3])}.")
    conf_note = (" Note: confidence below 55% — ask teacher to verify."
                 if bio.low_confidence else "")
    prompt = (f"I am looking at: {bio.common_name} (confidence {bio.confidence*100:.0f}%).{conf_note}\n"
              f"NCERT: {bio.cbse_chapter}\n"
              f"What I should see: {bio.what_you_see}\n"
              f"Key structures: {', '.join(bio.key_structures[:4])}\n"
              "Explain: 1) What am I looking at? 2) Most important structures? 3) Why important in biology?\n"
              "Friendly, under 120 words, end with a surprising fact.")
    resp = client.messages.create(model=MODEL, max_tokens=240,
                                   system=SYSTEM_PROMPT,
                                   messages=[{"role": "user", "content": prompt}])
    record_claude_call()
    return resp.content[0].text


def answer_student_question(question: str, bio: BioResult, history: list = None) -> str:
    """Answer a student's biology question in the context of their current specimen.
    Supports multi-turn conversation via history list.
    """
    if not can_call_claude():
        return "Daily AI question limit reached. Ask your teacher or check your NCERT textbook!"
    context = (f"Current specimen: {bio.common_name}\n"
               f"NCERT Chapter: {bio.cbse_chapter}\n"
               f"Key structures: {', '.join(bio.key_structures)}\n"
               f"NCERT points: {'; '.join(bio.ncert_points[:3])}")
    msgs = (history or [])[-8:] + [{
        "role": "user",
        "content": f"Lab context:\n{context}\n\nMy question: {question}"
    }]
    resp = client.messages.create(model=MODEL, max_tokens=280,
                                   system=SYSTEM_PROMPT, messages=msgs)
    record_claude_call()
    return resp.content[0].text


def generate_quiz(bio: BioResult, num_questions: int = 4) -> list:
    """Generate CBSE-style MCQ quiz on the identified specimen.
    Returns list of {question, options, correct, explanation}.
    Falls back to static KB questions if Claude budget is exhausted.
    """
    if not can_call_claude():
        return [{"question": q["q"], "correct_answer": q["a"], "options": None}
                for q in bio.quiz_questions[:num_questions]]
    prompt = (f"Generate {num_questions} CBSE-style MCQ questions about {bio.common_name}.\n"
              f"NCERT Chapter: {bio.cbse_chapter}\n"
              f"Key concepts: {'; '.join(bio.ncert_points)}\n"
              "Rules:\n"
              "- Exactly 4 options (A, B, C, D)\n"
              "- One correct answer per question\n"
              "- Brief explanation (1 sentence) of correct answer\n"
              "- Mix of easy (Class 9) and medium (Class 11–12) difficulty\n"
              "Return ONLY valid JSON array, no other text:\n"
              '[{"question":"...","options":{"A":"...","B":"...","C":"...","D":"..."},"correct":"A","explanation":"..."}]')
    resp = client.messages.create(
        model=MODEL, max_tokens=800,
        system="You are a CBSE biology question setter. Return ONLY valid JSON, nothing else.",
        messages=[{"role": "user", "content": prompt}])
    record_claude_call()
    try:
        text = resp.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return [{"question": q["q"], "correct_answer": q["a"], "options": None}
                for q in bio.quiz_questions[:num_questions]]


# ── STATIC PRACTICAL RECORD TEMPLATES ────────────────────────────────────────
# All 9 specimens. Used as fallback when Claude budget is exhausted.
# Also used as the base prompt context for Claude generation.
PRACTICAL_TEMPLATES = {
    "ONION_CELL": """AIM: To prepare a temporary stained mount of onion peel and observe plant cell structure.
MATERIALS REQUIRED: Onion, forceps, iodine solution, glass slide, coverslip, microscope, dropper, blotting paper.
PROCEDURE:
1. Cut a small piece of onion and peel the thin transparent layer from the inner concave surface.
2. Place the peeled layer on a clean glass slide.
3. Add 1–2 drops of iodine solution.
4. Gently lower a coverslip to avoid air bubbles.
5. Blot excess stain with blotting paper.
6. Observe under low power (10×), then high power (40×).
OBSERVATION: Brick-like rectangular cells arranged in a single layer. Cell wall (thick outer boundary), cell membrane, large central vacuole, and nucleus (stained brown) visible at periphery.
RESULT: Onion peel cells show a distinct cell wall, large central vacuole, and nucleus pushed to the periphery — confirming plant cell structure.
PRECAUTIONS: (1) Peel should be thin — single cell layer. (2) Avoid air bubbles under coverslip. (3) Do not over-stain.""",

    "CHEEK_CELL": """AIM: To prepare a temporary stained mount of human cheek cells and observe animal cell structure.
MATERIALS REQUIRED: Clean toothpick, methylene blue solution (0.1%), glass slide, coverslip, microscope, dropper, blotting paper.
PROCEDURE:
1. Rinse mouth with water to remove food particles.
2. Gently scrape the inner surface of the cheek with a clean toothpick.
3. Smear the scraping on the centre of a clean glass slide.
4. Add 1–2 drops of methylene blue solution.
5. Wait 30 seconds, then rinse excess stain gently.
6. Place coverslip. Observe under 10×, then 40×.
OBSERVATION: Large, irregular, flat polygon-shaped cells. Distinct oval nucleus stained dark blue (central position). Cell membrane visible as outer boundary. No cell wall. No chloroplasts.
RESULT: Cheek cells confirm animal cell structure — no cell wall, no chloroplasts, nucleus present.
PRECAUTIONS: (1) Scrape gently — do not press hard. (2) View within 20 minutes. (3) Stain for only 30 seconds to avoid over-staining.""",

    "STOMATA": """AIM: To prepare a temporary mount of leaf epidermis and observe stomata and guard cells.
MATERIALS REQUIRED: Leaf (spider plant or balsam), forceps, safranin, glass slide, coverslip, microscope, water, blotting paper.
PROCEDURE:
1. Select a fresh leaf and observe its lower surface (more stomata).
2. Using forceps, carefully peel a thin strip of lower epidermis from the leaf.
3. Place the peeled strip on a glass slide with a drop of water.
4. Add 1 drop of safranin stain. Wait 30 seconds.
5. Rinse excess stain and add coverslip.
6. Observe under 10×, then 40×.
OBSERVATION: Pairs of kidney-shaped (bean-shaped) guard cells with a pore (stoma) between them. Chloroplasts (green) visible inside guard cells. Surrounding epidermal cells are larger and lack chloroplasts.
RESULT: Stomata consist of two guard cells enclosing a pore. Guard cells contain chloroplasts; other epidermal cells do not.
PRECAUTIONS: (1) Use lower epidermis — has more stomata. (2) Peel must be thin. (3) View within 30 minutes.""",

    "AMOEBA": """AIM: To observe Amoeba proteus under a microscope and identify its characteristic structures.
MATERIALS REQUIRED: Pond water sample (bottom layer), dropper, glass slide, coverslip, microscope, iodine solution (optional).
PROCEDURE:
1. Collect pond water with a little aquatic vegetation.
2. Allow to settle for 5 minutes. Use a dropper to collect from the bottom layer.
3. Place one drop on a clean glass slide.
4. Gently lower the coverslip to avoid air bubbles.
5. Observe under 10× first to locate the organism, then switch to 40×.
6. Optional: add one drop of dilute iodine to stain nucleus brown (kills the organism).
OBSERVATION: Irregular, ever-changing shape. Pseudopodia (false feet) extending outward. Granular cytoplasm. Single large nucleus (visible when stained). Food vacuoles may be visible. Contractile vacuole (clear, pulsating circle).
RESULT: Amoeba is a unicellular protozoan showing movement by pseudopodia and visible nucleus in stained preparation.
PRECAUTIONS: (1) Use fresh pond water — view within 10 minutes. (2) Collect from bottom layer where Amoeba settles. (3) Move slowly when adjusting slide — sudden movements disperse organism.""",

    "BACTERIA": """AIM: To prepare a bacterial smear from yogurt and observe bacterial shapes using methylene blue stain.
MATERIALS REQUIRED: Fresh yogurt, distilled water, methylene blue solution (1%), glass slide, inoculation loop or toothpick, spirit lamp, microscope, blotting paper.
PROCEDURE:
1. Place one drop of distilled water on a clean glass slide.
2. Using a clean toothpick, pick a tiny amount of yogurt.
3. Mix with the water drop to make a thin, even smear.
4. Allow to air-dry completely (5 minutes).
5. Heat-fix: pass slide through flame 3 times quickly (bacteria attach to glass).
6. Flood slide with methylene blue for 1 minute.
7. Rinse gently with water, air-dry, observe under 40×.
OBSERVATION: Tiny (1–5 µm) blue-stained rod-shaped (bacillus) cells. Cells arranged in pairs or short chains. No nucleus visible (prokaryote). Cell wall and cell membrane not distinguishable at school magnification.
RESULT: Bacteria from yogurt are rod-shaped (Lactobacillus). Prokaryotic — no visible nucleus.
PRECAUTIONS: (1) Heat-fix properly — bacteria must adhere. (2) Rinse gently — do not wash cells off. (3) Observe within 30 minutes. (4) Do not use harmful bacteria — yogurt bacteria are safe.""",

    "BLOOD_SMEAR": """AIM: To observe the different types of blood cells in a prepared blood smear under a microscope.
MATERIALS REQUIRED: Prepared and stained blood smear slide (Leishman stain, commercial), microscope, immersion oil (for 100× oil objective), lens paper.
PROCEDURE:
1. Use a commercially prepared Leishman-stained human blood smear slide.
2. Place slide on microscope stage.
3. Focus under 10× first to locate the thin region of the smear.
4. Switch to 40× to observe cells in detail.
5. For WBC differentiation, use 100× oil objective with one drop of immersion oil.
OBSERVATION:
- RBC (erythrocytes): Abundant, small pink biconcave discs, NO nucleus, ~7µm diameter.
- WBC (leukocytes): Fewer, larger cells with dark-staining nucleus (purple/blue). Different WBC types visible: neutrophils (lobed nucleus), lymphocytes (large round nucleus), monocytes (kidney-shaped nucleus).
- Platelets (thrombocytes): Very small irregular fragments, 2–3µm, scattered between cells.
RESULT: Human blood contains three formed elements — RBCs (no nucleus), WBCs (with nucleus, 5 types), and platelets (fragments).
PRECAUTIONS: (1) Use commercially prepared slides ONLY — do not prepare fresh blood smears in school. (2) Clean lens with lens paper after using immersion oil. (3) Handle glass slides carefully.""",

    "YEAST": """AIM: To observe yeast cells and the process of budding under a microscope.
MATERIALS REQUIRED: Baker's yeast (dry, 1g), 5% glucose solution (5mL), glass slide, coverslip, methylene blue solution, dropper, microscope, water bath at 30°C (or warm place).
PROCEDURE:
1. Mix 1g baker's yeast with 5mL warm glucose solution (30°C).
2. Keep in a warm place for 15–20 minutes to activate.
3. Place one drop of yeast suspension on a clean glass slide.
4. Optional: add one drop of methylene blue (dead cells stain blue, live cells remain colourless).
5. Gently lower coverslip.
6. Observe under 40× magnification.
OBSERVATION: Oval to spherical yeast cells, ~5–10µm. Many cells show a smaller bud (daughter cell) attached to the parent. Bud scar visible on some parent cells. Vacuole visible inside cells. Dead cells stain blue with methylene blue; live cells remain colourless.
RESULT: Yeast reproduces asexually by budding. Live cells appear colourless; dead cells stain blue.
PRECAUTIONS: (1) Use warm (not hot) glucose solution — above 45°C kills yeast. (2) Allow 15+ minutes for budding to begin. (3) View within 30 minutes for active budding.""",

    "POLLEN": """AIM: To observe pollen grains from a flowering plant under a microscope and study their structure.
MATERIALS REQUIRED: Fresh flower (hibiscus, mustard, or marigold), glass slide, coverslip, acetocarmine stain or water, dropper, microscope, forceps.
PROCEDURE:
1. Select a mature flower with visible yellow anthers.
2. Tap the anther gently over a clean glass slide so pollen falls directly onto it.
3. Add 1 drop of acetocarmine stain (or plain water for unstained view).
4. Place coverslip gently.
5. Observe under 10× first, then 40×.
6. Repeat with a second flower species and compare pollen shapes.
OBSERVATION: Round to oval pollen grains, 10–100µm depending on species. Outer exine wall often shows surface texture — smooth, spiny, or ridged. Germination pores (colpi) visible at 400× on some species. Acetocarmine stains inner generative cell red/pink.
RESULT: Pollen grains from [flower species] are [shape] shaped with [surface texture] exine. Each grain contains vegetative cell and generative cell.
PRECAUTIONS: (1) Use fresh, open flowers. (2) Do not blow — disperse gently by tapping. (3) Note flower species in record.""",

    "FUNGI_HYPHAE": """AIM: To observe fungal hyphae and sporangia of Rhizopus (bread mold) under a microscope.
MATERIALS REQUIRED: Moist bread with black mold growth (Rhizopus), glass slide, coverslip, cotton blue in lactic acid (or water), inoculation loop or toothpick, dropper, microscope.
PROCEDURE:
1. Leave moist bread at room temperature (25–30°C) for 3–4 days until black mold appears.
2. Using a clean toothpick, tease a tiny amount of mold from the surface.
3. Place in a drop of cotton blue on a glass slide.
4. Tease apart gently with two toothpicks to separate hyphae.
5. Place coverslip carefully.
6. Observe under 4× first to see hyphal network, then 10× and 40× for sporangia detail.
OBSERVATION: Long, thread-like hyphae (filaments) forming a tangled network. No cross-walls visible in hyphae (coenocytic — multinucleate). Black spherical sporangia (spore cases) visible at tips of upright stalks (sporangiophores). Rhizoids (anchoring root-like structures) at base.
RESULT: Bread mold (Rhizopus) shows coenocytic hyphae with terminal black sporangia. Fungal body = mycelium (mass of hyphae).
PRECAUTIONS: (1) Handle mold carefully — wear gloves. (2) Tease gently — hyphae break easily. (3) Use minimal material for clear view. (4) Dispose of mold-contaminated bread hygienically.""",
}


def generate_practical_record(bio: BioResult, student_name: str, school_name: str) -> str:
    """Generate a complete CBSE practical record entry.
    Uses static template as base, enhances with Claude if budget allows.
    """
    # Get the static template for this specimen
    static_template = PRACTICAL_TEMPLATES.get(bio.specimen, PRACTICAL_TEMPLATES["ONION_CELL"])

    # Add student header to static template
    header = (
        f"BIOLOGY PRACTICAL RECORD\n"
        f"Student: {student_name}  |  School: {school_name}\n"
        f"Specimen: {bio.common_name}  |  NCERT: {bio.cbse_chapter}\n"
        f"Stain: {bio.stain}  |  Magnification: {bio.magnification}\n"    # ← fixed: was bio.key_structures
        f"{'─' * 50}\n\n"
    )

    if not can_call_claude():
        return header + static_template

    # Claude enhancement — personalise and polish the static template
    prompt = (f"Polish this biology practical record for:\n"
              f"Student: {student_name} | School: {school_name}\n"
              f"Specimen: {bio.common_name} | Chapter: {bio.cbse_chapter}\n"
              f"Stain: {bio.stain} | Magnification: {bio.magnification}\n\n"
              f"Base record:\n{static_template}\n\n"
              "Improve it slightly — make observation section more detailed and specific. "
              "Keep all section headings. Under 400 words total. CBSE format.")
    resp = client.messages.create(model=MODEL, max_tokens=600,
                                   system=SYSTEM_PROMPT,
                                   messages=[{"role": "user", "content": prompt}])
    record_claude_call()
    return header + resp.content[0].text
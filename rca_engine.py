# eduscope_rca.py — EduScope Biology Knowledge Base
# Contains full NCERT data for all 9 specimens.
# Used by api_server_eduscope.py and eduscope_claude.py
from dataclasses import dataclass
from typing import List
import config as cfg

BIO_KB = {
    "AMOEBA": {
        "common_name":    "Amoeba (Amoeba proteus)",
        "classification": "Kingdom Protista — Protozoa",
        "cbse_chapter":   "Class 8 Ch.2 — Microorganisms: Friend and Foe",
        "what_you_see":   "Irregular, ever-changing shape. Pseudopodia (false feet) extending outward for movement. Granular cytoplasm. Single large nucleus. Food vacuoles if fed recently.",
        "stain":          "Unstained for live observation. Iodine solution stains nucleus dark brown.",
        "magnification":  "100× to 400×. Start at 100× to locate, zoom to 400× for detail.",
        "key_structures": ["Pseudopodia", "Cell membrane", "Nucleus", "Food vacuoles", "Contractile vacuole"],
        "ncert_points": [
            "Amoeba moves using pseudopodia — cytoplasm streams into extensions",
            "Reproduces asexually by binary fission",
            "Engulfs food by phagocytosis",
            "Contractile vacuole regulates water balance (osmoregulation)",
            "Kingdom Protista — eukaryotic, unicellular",
        ],
        "fun_fact":       "Amoeba has no fixed shape! It changes shape every few seconds as pseudopodia extend and retract.",
        "quiz_questions": [
            {"q": "What are pseudopodia?", "a": "Temporary cytoplasmic projections used for movement and engulfing food"},
            {"q": "How does Amoeba reproduce?", "a": "Asexually by binary fission"},
            {"q": "What kingdom does Amoeba belong to?", "a": "Kingdom Protista"},
            {"q": "Function of contractile vacuole?", "a": "Expels excess water — osmoregulation"},
        ],
        "practical_tip":  "Collect pond water. Amoeba settles on bottom — use dropper from bottom layer. View within 10 minutes.",
    },
    "BACTERIA": {
        "common_name":    "Bacteria (mixed gram stain / methylene blue smear)",
        "classification": "Kingdom Monera — Prokaryote",
        "cbse_chapter":   "Class 8 Ch.2 — Microorganisms; Class 11 Ch.2 — Biological Classification",
        "what_you_see":   "Tiny (1–5 µm) coloured dots, rods, or spirals. No visible nucleus. Gram+ = purple, Gram- = pink. Methylene blue stains all cells blue.",
        "stain":          "Methylene blue (simple, school-appropriate). Gram stain for differentiation.",
        "magnification":  "1000× with oil immersion. 400× shows shapes.",
        "key_structures": ["Cell wall", "Cell membrane", "Nucleoid (no true nucleus)", "Flagella", "Pili"],
        "ncert_points": [
            "Bacteria are prokaryotes — no membrane-bound nucleus",
            "Shapes: coccus, bacillus, spirillum, vibrio",
            "Reproduce by binary fission — can double every 20 minutes",
            "Some beneficial (nitrogen fixation), some cause disease",
        ],
        "fun_fact":       "One bacterium can become 2 billion in 8 hours! Your gut has more bacterial cells than human cells.",
        "quiz_questions": [
            {"q": "Name the four shapes of bacteria", "a": "Coccus, Bacillus, Spirillum, Vibrio"},
            {"q": "Which bacteria helps in nitrogen fixation?", "a": "Rhizobium (root nodules of legumes)"},
            {"q": "How do bacteria reproduce?", "a": "Binary fission"},
        ],
        "practical_tip":  "Dilute yogurt in water, heat-fix on slide, stain methylene blue 1 min, wash, dry, view.",
    },
    "BLOOD_SMEAR": {
        "common_name":    "Human Blood Smear",
        "classification": "Human tissue — connective tissue",
        "cbse_chapter":   "Class 11 Ch.18 — Body Fluids and Circulation",
        "what_you_see":   "Abundant pink biconcave discs (RBC, no nucleus). Larger dark cells with nucleus (WBC). Tiny fragments (platelets). Pink background = plasma proteins.",
        "stain":          "Leishman stain (standard). Wright stain. Giemsa stain.",
        "magnification":  "400× for overview. 1000× (oil) for WBC identification.",
        "key_structures": ["Erythrocytes / RBC (biconcave, no nucleus)", "Leukocytes / WBC (has nucleus)", "Thrombocytes / Platelets"],
        "ncert_points": [
            "RBC — biconcave, no nucleus, carries oxygen via haemoglobin",
            "WBC — 5 types: neutrophil, eosinophil, basophil, monocyte, lymphocyte",
            "Platelets — cell fragments, help in blood clotting",
            "Normal RBC: 4.5–5.5 million/µL. WBC: 4,000–11,000/µL",
        ],
        "fun_fact":       "RBCs have no nucleus to maximise haemoglobin space. Each RBC carries ~270 million haemoglobin molecules.",
        "quiz_questions": [
            {"q": "Why do mature RBCs have no nucleus?", "a": "To maximise haemoglobin for oxygen transport"},
            {"q": "Name the 5 types of WBCs", "a": "Neutrophil, Eosinophil, Basophil, Monocyte, Lymphocyte"},
            {"q": "Role of platelets?", "a": "Blood clotting — aggregate at injury site"},
            {"q": "What gives RBC its biconcave shape?", "a": "Protein spectrin in cell membrane — increases surface area for gas exchange"},
        ],
        "practical_tip":  "Use prepared commercial slides (₹30–50). Do NOT make fresh blood smears in school without supervision.",
    },
    "CHEEK_CELL": {
        "common_name":    "Human Buccal (Cheek) Epithelial Cells",
        "classification": "Human tissue — squamous epithelium",
        "cbse_chapter":   "Class 9 Ch.5 — The Fundamental Unit of Life",
        "what_you_see":   "Large flat polygon-shaped cells, ~50µm. Dark oval nucleus in centre. Cell membrane visible. Pale cytoplasm with methylene blue. Cells often overlap.",
        "stain":          "Methylene blue (0.1% solution) — nucleus dark blue, cytoplasm light blue.",
        "magnification":  "100× to 400×.",
        "key_structures": ["Cell membrane", "Cytoplasm", "Nucleus", "Nuclear membrane"],
        "ncert_points": [
            "Nucleus contains chromosomes with DNA — control centre",
            "Buccal cells are squamous epithelium",
            "Eukaryotic cell — has membrane-bound nucleus",
        ],
        "fun_fact":       "You lose and replace the entire lining of your mouth every 3–5 days!",
        "quiz_questions": [
            {"q": "Why does a cheek cell have no cell wall?", "a": "Animal cells lack cell wall"},
            {"q": "Function of the nucleus?", "a": "Controls all cell activities; contains DNA"},
            {"q": "Why does methylene blue stain nucleus darker?", "a": "DNA is acidic, has affinity for basic dyes"},
        ],
        "practical_tip":  "Gently scrape inner cheek with clean toothpick. Smear on slide. Add methylene blue. Cover. View within 20 min.",
    },
    "FUNGI_HYPHAE": {
        "common_name":    "Fungal Hyphae (Rhizopus stolonifer — bread mold)",
        "classification": "Kingdom Fungi — Zygomycota",
        "cbse_chapter":   "Class 10 Ch.8 — How Do Organisms Reproduce; Class 11 Ch.2 — Biological Classification",
        "what_you_see":   "Thread-like hyphae forming tangled network. Dark round sporangia at tips. No cross-walls (coenocytic). Rhizoids anchoring to substrate.",
        "stain":          "Cotton blue in lactic acid. Unstained also works. Iodine shows starch reserves.",
        "magnification":  "40–100× for full network. 400× for sporangia detail.",
        "key_structures": ["Hyphae (thread-like filaments)", "Sporangium (spore case)", "Sporangiophore (stalk)", "Rhizoids", "Columella"],
        "ncert_points": [
            "Fungi body = mycelium — mass of thread-like hyphae",
            "Rhizopus is saprophytic — decomposes dead organic matter",
            "Reproduces asexually by sporangiospores",
            "Cell wall made of chitin (not cellulose)",
        ],
        "fun_fact":       "The world's largest living organism is a honey fungus in Oregon covering 8.9 km²!",
        "quiz_questions": [
            {"q": "What is mycelium?", "a": "Mass of thread-like hyphae forming the main body of a fungus"},
            {"q": "Function of sporangia in Rhizopus?", "a": "Produce and release asexual spores"},
            {"q": "What makes up fungal cell walls?", "a": "Chitin — nitrogen-containing polysaccharide"},
        ],
        "practical_tip":  "Leave moist bread in covered box 3–4 days (25–30°C). Tease small piece in cotton blue on slide. View 40× first.",
    },
    "ONION_CELL": {
        "common_name":    "Onion Epidermal Cells (Allium cepa)",
        "classification": "Plant tissue — simple epithelium",
        "cbse_chapter":   "Class 9 Ch.5 — The Fundamental Unit of Life",
        "what_you_see":   "Regular brick-like rectangular cells in single layer. Thick cell wall visible. Large central vacuole. Oval nucleus pressed to one side. No chloroplasts.",
        "stain":          "Iodine solution (nucleus yellow-brown). Safranin (cell wall and nucleus red).",
        "magnification":  "100× to 400×.",
        "key_structures": ["Cell wall (cellulose)", "Cell membrane", "Cytoplasm", "Nucleus", "Large central vacuole"],
        "ncert_points": [
            "Plant cells have cell wall (cellulose) — provides rigidity",
            "Large central vacuole maintains turgor pressure",
            "No chloroplasts — scale leaves not exposed to light",
            "Nucleus pushed to periphery by large vacuole",
        ],
        "fun_fact":       "Onion cells are the classic NCERT specimen — epidermis peels in perfect single-cell-thick layer!",
        "quiz_questions": [
            {"q": "Why is no chloroplast seen in onion cells?", "a": "Scale leaves underground — no sunlight"},
            {"q": "Function of large central vacuole?", "a": "Storage; maintains turgor pressure"},
            {"q": "Cell wall composition in plants?", "a": "Cellulose — a complex carbohydrate"},
        ],
        "practical_tip":  "Peel thin layer from inner surface — transparent single sheet. Add iodine, cover. Easiest specimen for beginners.",
    },
    "POLLEN": {
        "common_name":    "Pollen Grains (various flowering plants)",
        "classification": "Plant reproductive structure — male gametophyte",
        "cbse_chapter":   "Class 12 Ch.2 — Sexual Reproduction in Flowering Plants",
        "what_you_see":   "Round, oval, or elongated grains 10–100µm. Outer exine has distinctive texture — smooth, spiky, or ridged. Species-specific. Germination pores visible at 400×.",
        "stain":          "Acetocarmine (stains red). Unstained pollen often colourful (yellow, orange).",
        "magnification":  "100× to 400×. Surface texture at 400×.",
        "key_structures": ["Exine (outer wall — sporopollenin)", "Intine (inner wall — cellulose)", "Vegetative cell", "Generative cell", "Pores/colpi"],
        "ncert_points": [
            "Pollen grain = male gametophyte — produced in anther",
            "Exine made of sporopollenin — most resistant biological substance",
            "Mature pollen contains 2 cells: vegetative + generative",
            "Each species has unique pollen shape — palynology",
        ],
        "fun_fact":       "Pollen survives 10,000 years in ice cores — used to identify plants from the Ice Age!",
        "quiz_questions": [
            {"q": "Where is pollen produced?", "a": "In the anther — terminal part of stamen"},
            {"q": "What makes exine resistant?", "a": "Sporopollenin — not degraded by any enzyme"},
            {"q": "How many cells in mature pollen?", "a": "Two — vegetative cell and generative cell"},
        ],
        "practical_tip":  "Tap hibiscus/mustard onto slide — pollen falls directly. Add water or acetocarmine, cover, view.",
    },
    "STOMATA": {
        "common_name":    "Stomata with Guard Cells (leaf epidermis)",
        "classification": "Plant tissue — specialised epidermal cells",
        "cbse_chapter":   "Class 11 Ch.11 — Transport in Plants; Class 10 Ch.6 — Life Processes",
        "what_you_see":   "Kidney-shaped pair of guard cells with pore between them. Surrounding epidermal cells larger, no chloroplasts. Guard cells have visible green chloroplasts.",
        "stain":          "Nail varnish peel method OR peel lower epidermis directly. Safranin stain works.",
        "magnification":  "100× to 400×.",
        "key_structures": ["Guard cells (pair)", "Stoma (pore)", "Chloroplasts in guard cells", "Subsidiary cells", "Epidermal cells"],
        "ncert_points": [
            "Stomata regulate gas exchange and transpiration",
            "Guard cells open/close by turgor pressure",
            "In light: K+ enters guard cells → water follows → cells swell → pore opens",
            "Guard cells are the only epidermal cells with chloroplasts",
        ],
        "fun_fact":       "A single corn leaf has ~156 million stomata — each opens and closes independently!",
        "quiz_questions": [
            {"q": "What opens and closes the stomata?", "a": "Guard cells — turgor pressure via K+ ion movement"},
            {"q": "Why do guard cells have chloroplasts?", "a": "Need ATP from photosynthesis to pump K+ ions"},
            {"q": "When do stomata open?", "a": "During day — light triggers K+ influx; close at night or water stress"},
        ],
        "practical_tip":  "Use spider plant lower epidermis — peels easily. Or nail varnish method on any leaf. Always use lower surface.",
    },
    "YEAST": {
        "common_name":    "Yeast (Saccharomyces cerevisiae)",
        "classification": "Kingdom Fungi — Ascomycota",
        "cbse_chapter":   "Class 11 Ch.2 — Biological Classification; Class 10 Ch.8 — How Do Organisms Reproduce",
        "what_you_see":   "Oval yeast cells with smaller bud attached (daughter cell forming). Some cells show bud scar. Vacuole visible. Random jiggling = Brownian motion.",
        "stain":          "Methylene blue — dead cells stain blue, live cells remain colourless. Iodine shows cell wall.",
        "magnification":  "400×. Budding visible at 400×.",
        "key_structures": ["Cell wall (chitin + glucan)", "Bud (daughter cell)", "Bud scar", "Vacuole"],
        "ncert_points": [
            "Reproduces asexually by budding",
            "Facultative anaerobe — respires with or without oxygen",
            "Fermentation: glucose → ethanol + CO2 — bread, beer, wine",
            "Unicellular fungus — eukaryote",
        ],
        "fun_fact":       "Yeast has been baking bread and brewing beer for 7,000 years!",
        "quiz_questions": [
            {"q": "How does yeast reproduce asexually?", "a": "Budding — outgrowth forms, grows, separates"},
            {"q": "What is fermentation?", "a": "Anaerobic breakdown of glucose to ethanol + CO2"},
            {"q": "Why does bread rise with yeast?", "a": "CO2 from fermentation makes dough expand"},
        ],
        "practical_tip":  "Mix 1g baker's yeast in 5mL warm sugar water. Wait 15 min. View 400×. Look for cells with buds attached.",
    },
}


@dataclass
class BioResult:
    # ← FIXED: was 'what_you_see"' — stray quote caused SyntaxError on import
    specimen:       str
    confidence:     float
    common_name:    str
    cbse_chapter:   str
    what_you_see:   str   # ← fixed field name (no stray quote)
    stain:          str
    magnification:  str
    key_structures: List[str]
    ncert_points:   List[str]
    fun_fact:       str
    quiz_questions: List[dict]
    practical_tip:  str
    low_confidence: bool


def identify(specimen: str, confidence: float) -> BioResult:
    """Look up specimen in knowledge base and return a BioResult."""
    kb = BIO_KB.get(specimen, BIO_KB["ONION_CELL"])   # fallback to onion cell
    return BioResult(
        specimen       = specimen,
        confidence     = confidence,
        common_name    = kb["common_name"],
        cbse_chapter   = kb["cbse_chapter"],
        what_you_see   = kb["what_you_see"],
        stain          = kb["stain"],
        magnification  = kb["magnification"],
        key_structures = kb["key_structures"],
        ncert_points   = kb["ncert_points"],
        fun_fact       = kb["fun_fact"],
        quiz_questions = kb["quiz_questions"],
        practical_tip  = kb["practical_tip"],
        low_confidence = confidence < cfg.CONFIDENCE_THRESHOLD,   # ← fixed: was 'confidence 0.55'
    )
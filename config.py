# eduscope_config.py — EduScope Central Configuration
# Change BASE_DIR to your actual path. Everything else inherits from it.
import os
from pathlib import Path

BASE_DIR       = "/content/drive/MyDrive/EDUSCOPE"   # ← CHANGE THIS
DATA_DIR       = os.path.join(BASE_DIR, "data")
DATASET_RAW    = os.path.join(DATA_DIR, "dataset_raw")
DATASET_SPLIT  = os.path.join(DATA_DIR, "dataset_split")
CHECKPOINT_DIR = os.path.join(BASE_DIR, "checkpoints")
EXPORT_DIR     = os.path.join(BASE_DIR, "exports")
LOG_DIR        = os.path.join(BASE_DIR, "logs")
RESULTS_DIR    = os.path.join(BASE_DIR, "results")
DB_PATH        = os.path.join(BASE_DIR, "eduscope_results.db")

# 9 NCERT biology specimens — must match dataset_raw folder names exactly
CLASS_NAMES = [
    "AMOEBA",       # 0 — Class 8 unicellular
    "BACTERIA",     # 1 — Class 8/11 microorganism
    "BLOOD_SMEAR",  # 2 — Class 11 body fluids
    "CHEEK_CELL",   # 3 — Class 9 cell biology
    "FUNGI_HYPHAE", # 4 — Class 10 reproduction
    "ONION_CELL",   # 5 — Class 9 cell biology
    "POLLEN",       # 6 — Class 12 plant reproduction
    "STOMATA",      # 7 — Class 11 transport
    "YEAST",        # 8 — Class 11 classification
]
NUM_CLASSES  = len(CLASS_NAMES)
CLASS_TO_IDX = {n: i for i, n in enumerate(CLASS_NAMES)}
IDX_TO_CLASS = {v: k for k, v in CLASS_TO_IDX.items()}

IMG_SIZE = 224
IMG_MEAN = (0.485, 0.456, 0.406)
IMG_STD  = (0.229, 0.224, 0.225)

BATCH_SIZE          = 32
NUM_WORKERS         = 4
PHASE1_EPOCHS       = 10
PHASE1_LR           = 1e-3
PHASE2_EPOCHS       = 20
PHASE2_LR           = 1e-4
WEIGHT_DECAY        = 1e-4
LABEL_SMOOTHING     = 0.1
EARLY_STOP_PATIENCE = 5
TRAIN_RATIO         = 0.70
VAL_RATIO           = 0.15
TEST_RATIO          = 0.15
RANDOM_SEED         = 42

BACKBONE              = "mobilenet_v3_large"
PRETRAINED            = True
DROPOUT               = 0.3
CONFIDENCE_THRESHOLD  = 0.55  # lower than SENTINEL — bio images more varied

FP32_MODEL_NAME   = "eduscope_fp32.pth"
TFLITE_MODEL_NAME = "eduscope_int8.tflite"
ONNX_MODEL_NAME   = "eduscope_mobilenet.onnx"
CALIB_SAMPLES     = 200

API_HOST = "0.0.0.0"
API_PORT = 8001   # different from SENTINEL (8000) so both can run simultaneously

def create_dirs():
    for d in [DATASET_SPLIT, CHECKPOINT_DIR, EXPORT_DIR, LOG_DIR, RESULTS_DIR]:
        os.makedirs(d, exist_ok=True)

if __name__ == "__main__":
    create_dirs()
    print(f"[config] ✓ EduScope dirs created")
    print(f"[config] Classes: {CLASS_NAMES}")
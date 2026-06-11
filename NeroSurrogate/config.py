import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / os.getenv("DATA_DIR", "data")
OUTPUT_DIR    = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
LOG_DIR       = BASE_DIR / os.getenv("LOG_DIR", "logs")

RAW_DIR       = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DEM_DIR       = DATA_DIR / "dems"
SCENARIO_DIR  = DATA_DIR / "scenarios"

MODELS_DIR    = OUTPUT_DIR / "models"
EVAL_DIR      = OUTPUT_DIR / "eval"
DATASET_DIR   = OUTPUT_DIR / "datasets"

NORM_STATS_PATH = DATASET_DIR / "norm_stats.json"
BEST_CKPT_PATH  = MODELS_DIR  / "best.pt"
ONNX_MODEL_PATH = MODELS_DIR  / "nerosurrogate.onnx"
CPP_HEADER_PATH = MODELS_DIR  / "nerosurrogate.h"

FLOOD_ENGINE_HOST = os.getenv("FLOOD_ENGINE_HOST", "localhost")
FLOOD_ENGINE_PORT = int(os.getenv("FLOOD_ENGINE_PORT", "5050"))
DLL_PATH = os.getenv("FLOOD_ENGINE_DLL", "")

N_SCENARIOS = 1000
N_JOBS      = 4
LHS_SEED    = 42

PARAM_RANGES = {
    "rainfall_mm_hr": (10.0,  150.0),
    "duration_hr":    (1.0,   72.0),
    "manning_n":      (0.01,  0.15),
    "Ks":             (1.0,   50.0),
    "psi":            (50.0,  300.0),
    "dTheta":         (0.1,   0.6),
    "cell_size_m":    (10.0,  90.0),
}

CHANNELS = [
    "dem",
    "slope",
    "flow_accumulation",
    "rainfall",
    "soil_moisture",
    "manning_n",
]
N_CHANNELS = len(CHANNELS)

UNET_BASE_FILTERS = 32
UNET_DEPTH        = 4
DROPOUT           = 0.1

DEVICE       = os.getenv("DEVICE", "cpu")
BATCH_SIZE   = 8
NUM_EPOCHS   = 100
LR           = 1e-3
LR_MIN       = 1e-6
WARMUP_EPOCHS = 5
WEIGHT_DECAY  = 1e-4
VAL_SPLIT     = 0.15
TEST_SPLIT    = 0.10

LOSS_MSE_WEIGHT  = 0.7
LOSS_IOU_WEIGHT  = 0.3
FLOOD_THRESHOLD  = 0.01

INFERENCE_TIMEOUT_MS = 50


def ensure_dirs():
    for d in [RAW_DIR, PROCESSED_DIR, DEM_DIR, SCENARIO_DIR,
              MODELS_DIR, EVAL_DIR, DATASET_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)


ensure_dirs()
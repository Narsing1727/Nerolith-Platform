import json
import numpy as np
import torch
from loguru import logger
from config import EVAL_DIR, NORM_STATS_PATH, ONNX_MODEL_PATH, DEM_DIR
from dataset_generator.terrain_sampler import TERRAIN_TYPES
from inference.surrogate_runner import SurrogateRunner
from model.metrics import compute_all
from engine_bridge.grid_io import load_grid


def run_generalization_test(rows=64, cols=64, n_per_type=5,
                             rainfall=50.0, duration=6.0,
                             dTheta=0.3, manning_n=0.035) -> dict:
    try:
        from engine_bridge.dll_caller import FloodEngineDLL
        dll_available = True
    except Exception:
        dll_available = False
        logger.warning("DLL not available — skipping physics comparison")

    runner  = SurrogateRunner(ONNX_MODEL_PATH, NORM_STATS_PATH)
    results = {}

    for terrain_type, fn in TERRAIN_TYPES.items():
        preds, tgts = [], []
        for i in range(n_per_type):
            dem = fn(rows, cols, seed=i + 100)
            pred = runner.predict(dem, rainfall, duration, dTheta, manning_n)

            if dll_available:
                with FloodEngineDLL() as eng:
                    flood = eng.run_scenario(dem, rainfall, duration,
                                             manning_n, 6.8, 166.8, dTheta)
                preds.append(torch.from_numpy(pred).unsqueeze(0))
                tgts.append(torch.from_numpy(np.clip(flood.astype(np.float32), 0, None)).unsqueeze(0))

        if preds:
            m = compute_all(torch.stack(preds), torch.stack(tgts))
            results[terrain_type] = m
            logger.info(f"[{terrain_type}] rmse={m['rmse_m']:.4f}m iou={m['iou']:.4f}")
        else:
            results[terrain_type] = {"note": "DLL not available"}

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVAL_DIR / "generalization_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return results

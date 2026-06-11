import json
import torch
import numpy as np
from pathlib import Path
from loguru import logger
from config import RAW_DIR, EVAL_DIR, NORM_STATS_PATH, ONNX_MODEL_PATH
from preprocessing.dataset import split_scenarios
from preprocessing.normalizer import ChannelNormalizer
from preprocessing.channel_builder import build_channels, channels_to_tensor, target_to_tensor
from engine_bridge.grid_io import load_grid
from dataset_generator.param_sampler import load_scenario_params
from model.metrics import compute_all
from inference.surrogate_runner import SurrogateRunner


def run_benchmark(raw_dir=RAW_DIR, n_samples=50) -> dict:
    _, _, test_dirs = split_scenarios(raw_dir)
    test_dirs       = test_dirs[:n_samples]

    runner = SurrogateRunner(ONNX_MODEL_PATH, NORM_STATS_PATH)
    norm   = ChannelNormalizer.from_file(NORM_STATS_PATH)

    all_pred, all_tgt = [], []
    times             = []

    import time
    for d in test_dirs:
        try:
            dem    = load_grid(d / "dem.bin").astype(np.float64)
            flood  = load_grid(d / "flood.bin")
            params = load_scenario_params(d)

            t0    = time.perf_counter()
            pred  = runner.predict(dem, params.rainfall_mm_hr, params.duration_hr,
                                   params.dTheta, params.manning_n, params.cell_size_m)
            times.append((time.perf_counter() - t0) * 1000)

            all_pred.append(torch.from_numpy(pred).unsqueeze(0))
            all_tgt.append(torch.from_numpy(np.clip(flood, 0, None)).unsqueeze(0))
        except Exception as e:
            logger.warning(f"Skipping {d.name}: {e}")

    metrics = compute_all(torch.stack(all_pred), torch.stack(all_tgt))
    metrics["avg_inference_ms"] = round(float(np.mean(times)), 2)
    metrics["n_evaluated"]      = len(all_pred)

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVAL_DIR / "benchmark_results.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Benchmark: {metrics}")
    return metrics

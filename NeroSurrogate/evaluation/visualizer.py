import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from loguru import logger
from config import EVAL_DIR, NORM_STATS_PATH, ONNX_MODEL_PATH
from inference.surrogate_runner import SurrogateRunner
from engine_bridge.grid_io import load_grid
from dataset_generator.param_sampler import load_scenario_params


def visualize_prediction(scenario_dir: Path, save=True) -> plt.Figure:
    runner = SurrogateRunner(ONNX_MODEL_PATH, NORM_STATS_PATH)
    dem    = load_grid(scenario_dir / "dem.bin").astype(np.float64)
    flood  = load_grid(scenario_dir / "flood.bin")
    params = load_scenario_params(scenario_dir)

    pred   = runner.predict(dem, params.rainfall_mm_hr, params.duration_hr,
                            params.dTheta, params.manning_n, params.cell_size_m)
    error  = pred - np.clip(flood, 0, None)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    vmax = max(flood.max(), pred.max(), 0.01)

    axes[0].imshow(flood, cmap="Blues", vmin=0, vmax=vmax)
    axes[0].set_title("DLL Ground Truth")
    axes[0].axis("off")

    axes[1].imshow(pred, cmap="Blues", vmin=0, vmax=vmax)
    axes[1].set_title("Surrogate Prediction")
    axes[1].axis("off")

    im = axes[2].imshow(error, cmap="RdBu_r",
                        vmin=-vmax/2, vmax=vmax/2)
    axes[2].set_title("Error (Pred - Truth)")
    axes[2].axis("off")
    plt.colorbar(im, ax=axes[2], label="metres")

    fig.suptitle(f"Scenario {scenario_dir.name} | "
                 f"rain={params.rainfall_mm_hr:.0f}mm/hr dur={params.duration_hr:.0f}h",
                 fontsize=11)
    plt.tight_layout()

    if save:
        out = EVAL_DIR / "visualizations"
        out.mkdir(parents=True, exist_ok=True)
        fig.savefig(out / f"{scenario_dir.name}.png", dpi=120, bbox_inches="tight")
        logger.info(f"Saved visualization → {out / scenario_dir.name}.png")

    return fig


def visualize_batch(raw_dir: Path, n=5):
    dirs = sorted([d for d in raw_dir.iterdir()
                   if d.is_dir() and (d / "flood.bin").exists()])[:n]
    for d in dirs:
        try:
            visualize_prediction(d)
        except Exception as e:
            logger.warning(f"Failed {d.name}: {e}")

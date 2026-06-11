import json
import time
import traceback
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from loguru import logger
from tqdm import tqdm

from config import RAW_DIR, DEM_DIR, N_JOBS, N_SCENARIOS
from engine_bridge.dll_caller import FloodEngineDLL
from engine_bridge.grid_io import save_scenario, load_grid, grid_exists
from engine_bridge.engine_schema import SimulationInput, SimulationOutput
from dataset_generator.param_sampler import (
    build_simulation_inputs, save_scenario_params, available_dem_paths
)


def _synthetic_dem(rows: int = 64, cols: int = 64) -> np.ndarray:
    rng  = np.random.default_rng()
    x    = np.linspace(100.0, 50.0, cols)
    dem  = np.outer(np.ones(rows), x)
    dem += rng.uniform(-2.0, 2.0, (rows, cols))
    return dem.astype(np.float64)


def _synthetic_flood(dem: np.ndarray, rainfall: float) -> np.ndarray:
    rows, cols = dem.shape
    norm_rain  = (rainfall - 10.0) / 140.0
    min_elev   = dem.min()
    depth      = np.clip((min_elev + 5.0 - dem) * norm_rain * 0.3, 0, None)
    return depth.astype(np.float64)


def _run_one(sim_input: SimulationInput) -> SimulationOutput | None:
    scenario_dir = RAW_DIR / sim_input.scenario_id
    if (scenario_dir / "flood.bin").exists():
        return None
    try:
        dem = load_grid(sim_input.dem_path) if sim_input.dem_path and grid_exists(sim_input.dem_path) \
              else _synthetic_dem()

        try:
            with FloodEngineDLL() as engine:
                t0    = time.perf_counter()
                flood = engine.run_scenario(
                    dem       = dem,
                    rainfall  = sim_input.rainfall_mm_hr,
                    duration  = sim_input.duration_hr,
                    manning_n = sim_input.manning_n,
                    Ks        = sim_input.Ks,
                    psi       = sim_input.psi,
                    dTheta    = sim_input.dTheta,
                    cell_size = sim_input.cell_size_m,
                    blended   = sim_input.blended,
                )
                elapsed = time.perf_counter() - t0
        except FileNotFoundError:
            logger.warning(f"[{sim_input.scenario_id}] DLL not found — using synthetic flood")
            t0      = time.perf_counter()
            flood   = _synthetic_flood(dem, sim_input.rainfall_mm_hr)
            elapsed = time.perf_counter() - t0

        rows, cols = flood.shape
        save_scenario(scenario_dir, dem, flood)
        save_scenario_params(sim_input, scenario_dir)

        with open(scenario_dir / "metadata.json", "w") as f:
            json.dump({
                "scenario_id": sim_input.scenario_id,
                "rows": rows, "cols": cols,
                "cell_size_m": sim_input.cell_size_m,
                "dem_min": float(dem.min()), "dem_max": float(dem.max()),
                "elapsed_sec": round(elapsed, 4),
            }, f, indent=2)

        flooded = flood > 0.01
        return SimulationOutput(
            scenario_id       = sim_input.scenario_id,
            rows              = rows, cols=cols,
            max_depth_m       = float(flood.max()),
            mean_depth_m      = float(flood[flooded].mean()) if flooded.any() else 0.0,
            flooded_fraction  = float(flooded.sum()) / (rows * cols),
            high_risk_cells   = int((flood > 0.5).sum()),
            medium_risk_cells = int(((flood > 0.08) & (flood <= 0.5)).sum()),
            flood_path        = str(scenario_dir / "flood.bin"),
        )
    except Exception as e:
        logger.error(f"[{sim_input.scenario_id}] FAILED: {e}")
        return None


def run_scenarios(n: int = N_SCENARIOS, n_jobs: int = N_JOBS,
                  dem_paths: list[str] | None = None, seed: int = 42) -> list[SimulationOutput]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if dem_paths is None:
        dem_paths = available_dem_paths(DEM_DIR)
        if not dem_paths:
            logger.warning("No cached DEMs found — using synthetic DEMs")

    inputs  = build_simulation_inputs(n, dem_paths, seed)
    outputs = []
    skipped = 0
    t0      = time.perf_counter()

    if n_jobs == 1:
        for inp in tqdm(inputs, desc="Generating"):
            out = _run_one(inp)
            if out is None: skipped += 1
            else:           outputs.append(out)
    else:
        with ProcessPoolExecutor(max_workers=n_jobs) as pool:
            futures = {pool.submit(_run_one, inp): inp for inp in inputs}
            with tqdm(total=n, desc="Generating") as pbar:
                for fut in as_completed(futures):
                    out = fut.result()
                    if out is None: skipped += 1
                    else:           outputs.append(out)
                    pbar.update(1)

    elapsed = time.perf_counter() - t0
    logger.info(f"Done: {len(outputs)} success | {skipped} skipped | {elapsed:.1f}s")

    with open(RAW_DIR / "run_summary.json", "w") as f:
        json.dump({"n_success": len(outputs), "n_skipped": skipped,
                   "elapsed_sec": round(elapsed, 2)}, f, indent=2)
    return outputs
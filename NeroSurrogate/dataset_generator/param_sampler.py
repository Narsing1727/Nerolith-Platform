import json
import uuid
import numpy as np
from pathlib import Path
from config import PARAM_RANGES, LHS_SEED, DEM_DIR
from engine_bridge.engine_schema import SimulationInput


def latin_hypercube_sample(n: int, ranges: dict, seed: int = LHS_SEED) -> list[dict]:
    rng    = np.random.default_rng(seed)
    params = list(ranges.keys())
    n_dims = len(params)
    samples = np.zeros((n, n_dims))
    for d in range(n_dims):
        perm          = rng.permutation(n)
        samples[:, d] = (perm + rng.uniform(size=n)) / n
    result = []
    for i in range(n):
        row = {}
        for d, name in enumerate(params):
            lo, hi   = ranges[name]
            row[name] = lo + samples[i, d] * (hi - lo)
        result.append(row)
    return result


def build_simulation_inputs(n: int, dem_paths: list[str] | None = None,
                             seed: int = LHS_SEED) -> list[SimulationInput]:
    raw     = latin_hypercube_sample(n, PARAM_RANGES, seed)
    rng     = np.random.default_rng(seed + 1)
    inputs  = []
    for s in raw:
        dem_path = str(rng.choice(dem_paths)) if dem_paths else ""
        inputs.append(SimulationInput(
            scenario_id    = str(uuid.uuid4())[:8],
            rainfall_mm_hr = round(s["rainfall_mm_hr"], 3),
            duration_hr    = round(s["duration_hr"],    3),
            manning_n      = round(s["manning_n"],      5),
            Ks             = round(s["Ks"],             3),
            psi            = round(s["psi"],            3),
            dTheta         = round(s["dTheta"],         4),
            cell_size_m    = round(s["cell_size_m"],    2),
            dem_path       = dem_path,
            blended        = False,
        ))
    return inputs


def save_scenario_params(sim_input: SimulationInput, scenario_dir: Path):
    scenario_dir.mkdir(parents=True, exist_ok=True)
    with open(scenario_dir / "input.json", "w") as f:
        json.dump(sim_input.model_dump(), f, indent=2)


def load_scenario_params(scenario_dir: Path) -> SimulationInput:
    with open(scenario_dir / "input.json") as f:
        return SimulationInput(**json.load(f))


def available_dem_paths(dem_dir: Path = DEM_DIR) -> list[str]:
    return [str(p) for p in Path(dem_dir).glob("*.bin")]

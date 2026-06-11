import numpy as np
from pathlib import Path
from loguru import logger
from engine_bridge.grid_io import save_grid, load_grid
from config import DEM_DIR


def flat_dem(rows=64, cols=64, seed=None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    dem = np.full((rows, cols), 50.0)
    dem += rng.uniform(-1, 1, (rows, cols))
    return dem.astype(np.float64)


def sloped_dem(rows=64, cols=64, slope_pct=0.02, seed=None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x   = np.linspace(100, 100 - slope_pct * cols * 30, cols)
    dem = np.outer(np.ones(rows), x)
    dem += rng.uniform(-2, 2, (rows, cols))
    return dem.astype(np.float64)


def valley_dem(rows=64, cols=64, seed=None) -> np.ndarray:
    rng    = np.random.default_rng(seed)
    x      = np.linspace(-1, 1, cols)
    valley = (x ** 2) * 30
    dem    = np.outer(np.ones(rows), valley) + np.linspace(80, 50, rows)[:, None]
    dem   += rng.uniform(-1, 1, (rows, cols))
    return dem.astype(np.float64)


def ridge_dem(rows=64, cols=64, seed=None) -> np.ndarray:
    rng   = np.random.default_rng(seed)
    x     = np.linspace(-1, 1, cols)
    ridge = -(x ** 2) * 30 + 100
    dem   = np.outer(np.ones(rows), ridge)
    dem  += rng.uniform(-1, 1, (rows, cols))
    return dem.astype(np.float64)


def urban_dem(rows=64, cols=64, seed=None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    dem = sloped_dem(rows, cols, seed=seed)
    n_buildings = rng.integers(5, 20)
    for _ in range(n_buildings):
        r  = rng.integers(2, rows - 10)
        c  = rng.integers(2, cols - 10)
        h  = rng.uniform(2, 8)
        rw = rng.integers(2, 6)
        cw = rng.integers(2, 6)
        dem[r:r+rw, c:c+cw] += h
    return dem


TERRAIN_TYPES = {
    "flat":   flat_dem,
    "sloped": sloped_dem,
    "valley": valley_dem,
    "ridge":  ridge_dem,
    "urban":  urban_dem,
}


def generate_synthetic_dem_library(n_per_type: int = 20,
                                   rows: int = 64,
                                   cols: int = 64,
                                   save: bool = True) -> list[str]:
    saved = []
    DEM_DIR.mkdir(parents=True, exist_ok=True)
    for terrain_type, fn in TERRAIN_TYPES.items():
        for i in range(n_per_type):
            dem  = fn(rows, cols, seed=i)
            name = f"{terrain_type}_{i:03d}.bin"
            path = DEM_DIR / name
            if save:
                save_grid(dem, path)
                saved.append(str(path))
    logger.info(f"Generated {len(saved)} synthetic DEMs in {DEM_DIR}")
    return saved


def load_dem_by_type(terrain_type: str, idx: int = 0) -> np.ndarray:
    path = DEM_DIR / f"{terrain_type}_{idx:03d}.bin"
    return load_grid(path).astype(np.float64)

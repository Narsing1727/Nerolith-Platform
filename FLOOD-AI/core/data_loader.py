"""
Loads static terrain data: DEM, river network, road network, watershed boundaries.
Used during agent initialization to give each agent spatial context.
"""
import os
import json
import numpy as np
from typing import Optional
from loguru import logger

from core.region_registry import registry
from services.region_clusterer import cluster_from_boundaries, cluster_uniform_grid
from config import settings


def load(
    grid_rows: Optional[int] = None,
    grid_cols: Optional[int] = None
):
    registry.clear()

    boundary_path = os.path.join(settings.data_dir, "boundaries", "watershed.npy")
    dem_path = os.path.join(settings.data_dir, "dem", "elevation.npy")

    if os.path.exists(boundary_path):
        logger.info("Loading regions from watershed boundary data.")
        boundary_map = np.load(boundary_path)
        elevation = np.load(dem_path) if os.path.exists(dem_path) else None
        regions = cluster_from_boundaries(boundary_map, elevation_grid=elevation)
    elif grid_rows and grid_cols:
        logger.warning("No boundary data found. Falling back to uniform grid clustering.")
        n_splits = max(1, int(np.sqrt(min(settings.max_regions, grid_rows * grid_cols / 100))))
        regions = cluster_uniform_grid(grid_rows, grid_cols, n_splits, n_splits)
    else:
        logger.error("No boundary data and no grid dimensions provided. Registry will be empty.")
        return

    for region in regions[:settings.max_regions]:
        registry.register(region)

    logger.info(f"Loaded {registry.count()} regions into registry.")


def load_from_json(path: str):
    if not os.path.exists(path):
        logger.error(f"Region config file not found: {path}")
        return

    with open(path) as f:
        data = json.load(f)

    from core.schemas import RegionConfig
    registry.clear()
    for item in data:
        registry.register(RegionConfig(**item))

    logger.info(f"Loaded {registry.count()} regions from {path}.")
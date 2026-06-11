"""
Parses raw 2D grid data from the engine into Python numpy arrays.
Handles coordinate transforms between engine grid indices and real-world lat/lon.
"""
import numpy as np
from typing import Tuple
from engine_bridge.engine_schema import FloodGridSnapshot, FlowGridSnapshot, RainfallGridSnapshot


def parse_flood_grid(snapshot: FloodGridSnapshot) -> np.ndarray:
    return np.array(snapshot.data, dtype=np.float64)


def parse_flow_grid(snapshot: FlowGridSnapshot) -> np.ndarray:
    return np.array(snapshot.data, dtype=np.float64)


def parse_rainfall_grid(snapshot: RainfallGridSnapshot) -> np.ndarray:
    return np.array(snapshot.data, dtype=np.float64)


def extract_region_slice(
    grid: np.ndarray,
    row_start: int,
    row_end: int,
    col_start: int,
    col_end: int
) -> np.ndarray:
    return grid[row_start:row_end, col_start:col_end]


def compute_region_stats(region_grid: np.ndarray) -> dict:
    nonzero = region_grid[region_grid > 0]
    return {
        "mean": float(np.mean(region_grid)),
        "max": float(np.max(region_grid)),
        "min": float(np.min(region_grid)),
        "flooded_cells": int(np.sum(region_grid > 0)),
        "mean_nonzero": float(np.mean(nonzero)) if len(nonzero) > 0 else 0.0,
        "total_cells": int(region_grid.size)
    }


def grid_to_flat(grid: np.ndarray) -> Tuple[list, int, int]:
    return grid.flatten().tolist(), grid.shape[0], grid.shape[1]
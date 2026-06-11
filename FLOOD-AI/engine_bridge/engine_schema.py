"""
Pydantic models for engine output data structures.
FloodGridSnapshot, FlowSnapshot, RainfallSnapshot, etc.
"""
from pydantic import BaseModel
from typing import List
import numpy as np


class GridSnapshot(BaseModel):
    timestep: int
    rows: int
    cols: int
    cell_size_m: float
    data: List[List[float]]

    class Config:
        arbitrary_types_allowed = True


class FloodGridSnapshot(GridSnapshot):
    max_depth_m: float
    flooded_cell_count: int


class FlowGridSnapshot(GridSnapshot):
    max_velocity_ms: float


class RainfallGridSnapshot(GridSnapshot):
    total_rainfall_mm: float


class EngineTickPayload(BaseModel):
    timestep: int
    elapsed_seconds: float
    flood: FloodGridSnapshot
    flow: FlowGridSnapshot
    rainfall: RainfallGridSnapshot
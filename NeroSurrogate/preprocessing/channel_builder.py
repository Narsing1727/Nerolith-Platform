import numpy as np
import torch
from config import N_CHANNELS, CHANNELS
from engine_bridge.grid_io import load_grid
from preprocessing.flow_accumulation import compute_log_flow_accumulation


def compute_slope(dem: np.ndarray, cell_size_m: float = 30.0) -> np.ndarray:
    dz_dx = np.gradient(dem, cell_size_m, axis=1)
    dz_dy = np.gradient(dem, cell_size_m, axis=0)
    return np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))).astype(np.float32)


def broadcast_scalar(value: float, rows: int, cols: int) -> np.ndarray:
    return np.full((rows, cols), value, dtype=np.float32)


def build_channels(dem: np.ndarray, rainfall: float, dTheta: float,
                   manning_n: float, cell_size_m: float = 30.0,
                   flow_accum: np.ndarray | None = None) -> np.ndarray:
    rows, cols = dem.shape
    dem_f      = dem.astype(np.float32)
    slope      = compute_slope(dem_f, cell_size_m)
    fa         = flow_accum if flow_accum is not None \
                 else compute_log_flow_accumulation(dem_f)
    channels = np.stack([
        dem_f,
        slope,
        fa,
        broadcast_scalar(rainfall,  rows, cols),
        broadcast_scalar(dTheta,    rows, cols),
        broadcast_scalar(manning_n, rows, cols),
    ], axis=0)
    assert channels.shape[0] == N_CHANNELS
    return channels


def channels_to_tensor(channels: np.ndarray) -> torch.Tensor:
    return torch.from_numpy(channels.astype(np.float32))


def target_to_tensor(flood: np.ndarray) -> torch.Tensor:
    return torch.from_numpy(np.clip(flood.astype(np.float32), 0, None)).unsqueeze(0)


def channel_info() -> dict:
    return {i: name for i, name in enumerate(CHANNELS)}
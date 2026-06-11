import struct
from pathlib import Path
import numpy as np
import torch


def save_grid(grid: np.ndarray, path: str | Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows, cols = grid.shape
    with open(path, "wb") as f:
        f.write(struct.pack("<II", rows, cols))
        f.write(grid.astype(np.float32).ravel().tobytes())


def load_grid(path: str | Path) -> np.ndarray:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Grid not found: {path}")
    with open(path, "rb") as f:
        rows, cols = struct.unpack("<II", f.read(8))
        flat = np.frombuffer(f.read(rows * cols * 4), dtype=np.float32).copy()
    return flat.reshape(rows, cols)


def grid_exists(path: str | Path) -> bool:
    return Path(path).exists()


def grid_to_tensor(grid: np.ndarray) -> torch.Tensor:
    return torch.from_numpy(grid.astype(np.float32)).unsqueeze(0)


def tensor_to_grid(tensor: torch.Tensor) -> np.ndarray:
    return tensor.squeeze().detach().cpu().numpy()


def save_scenario(scenario_dir: str | Path, dem: np.ndarray, flood: np.ndarray):
    d = Path(scenario_dir)
    save_grid(dem,   d / "dem.bin")
    save_grid(flood, d / "flood.bin")


def load_scenario(scenario_dir: str | Path) -> tuple[np.ndarray, np.ndarray]:
    d = Path(scenario_dir)
    return load_grid(d / "dem.bin"), load_grid(d / "flood.bin")

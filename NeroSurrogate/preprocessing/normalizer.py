import json
import numpy as np
import torch
from pathlib import Path
from config import NORM_STATS_PATH, N_CHANNELS, CHANNELS


class ChannelNormalizer:
    def __init__(self):
        self.means:  np.ndarray | None = None
        self.stds:   np.ndarray | None = None
        self.fitted: bool              = False

    def fit(self, channel_arrays: list[np.ndarray]):
        C       = channel_arrays[0].shape[0]
        sums    = np.zeros(C, dtype=np.float64)
        sq_sums = np.zeros(C, dtype=np.float64)
        counts  = np.zeros(C, dtype=np.float64)
        for arr in channel_arrays:
            for c in range(C):
                vals        = arr[c].ravel().astype(np.float64)
                sums[c]    += vals.sum()
                sq_sums[c] += (vals ** 2).sum()
                counts[c]  += len(vals)
        self.means  = (sums / counts).astype(np.float32)
        variances   = sq_sums / counts - (sums / counts) ** 2
        self.stds   = np.sqrt(np.maximum(variances, 1e-8)).astype(np.float32)
        self.fitted = True

    def normalize(self, x):
        self._check()
        if isinstance(x, torch.Tensor):
            m = torch.tensor(self.means, dtype=x.dtype, device=x.device).view(-1, 1, 1)
            s = torch.tensor(self.stds,  dtype=x.dtype, device=x.device).view(-1, 1, 1)
            return (x - m) / s
        return ((x - self.means[:, None, None]) / self.stds[:, None, None]).astype(np.float32)

    def denormalize(self, x):
        self._check()
        if isinstance(x, torch.Tensor):
            m = torch.tensor(self.means, dtype=x.dtype, device=x.device).view(-1, 1, 1)
            s = torch.tensor(self.stds,  dtype=x.dtype, device=x.device).view(-1, 1, 1)
            return x * s + m
        return (x * self.stds[:, None, None] + self.means[:, None, None]).astype(np.float32)

    def normalize_target(self, y: torch.Tensor, max_depth: float = 10.0) -> torch.Tensor:
        return torch.clamp(y / max_depth, 0.0, 1.0)

    def denormalize_target(self, y: torch.Tensor, max_depth: float = 10.0) -> torch.Tensor:
        return y * max_depth

    def save(self, path: Path = NORM_STATS_PATH):
        self._check()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({"channels": CHANNELS,
                       "means": self.means.tolist(),
                       "stds":  self.stds.tolist()}, f, indent=2)

    def load(self, path: Path = NORM_STATS_PATH):
        with open(path) as f:
            s = json.load(f)
        self.means  = np.array(s["means"], dtype=np.float32)
        self.stds   = np.array(s["stds"],  dtype=np.float32)
        self.fitted = True
        return self

    def _check(self):
        if not self.fitted:
            raise RuntimeError("Normalizer not fitted. Call fit() or load().")

    @classmethod
    def from_file(cls, path: Path = NORM_STATS_PATH):
        return cls().load(path)

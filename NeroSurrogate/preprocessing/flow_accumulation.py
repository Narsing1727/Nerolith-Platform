import numpy as np
from pathlib import Path
from engine_bridge.grid_io import save_grid, load_grid

DR = np.array([0,  1, 1,  1, 0, -1, -1, -1])
DC = np.array([1,  1, 0, -1,-1, -1,  0,  1])


def d8_directions(dem: np.ndarray) -> np.ndarray:
    rows, cols = dem.shape
    dirs       = np.full((rows, cols), -1, dtype=np.int8)
    padded     = np.pad(dem, 1, mode="edge")

    best_drop  = np.zeros((rows, cols))
    for d in range(8):
        shifted = padded[1 + DR[d]: 1 + DR[d] + rows,
                         1 + DC[d]: 1 + DC[d] + cols]
        drop    = dem - shifted
        mask    = drop > best_drop
        dirs[mask]      = d
        best_drop[mask] = drop[mask]
    return dirs


def accumulate(dirs: np.ndarray) -> np.ndarray:
    rows, cols = dirs.shape
    in_deg     = np.zeros((rows, cols), dtype=np.int32)

    targets = {}
    for r in range(rows):
        for c in range(cols):
            d = dirs[r, c]
            if d >= 0:
                nr, nc = r + DR[d], c + DC[d]
                if 0 <= nr < rows and 0 <= nc < cols:
                    in_deg[nr, nc] += 1
                    targets[(r, c)] = (nr, nc)

    from collections import deque
    queue = deque((r, c) for r in range(rows) for c in range(cols) if in_deg[r, c] == 0)
    accum = np.ones((rows, cols), dtype=np.float32)

    while queue:
        rc = queue.popleft()
        if rc in targets:
            nr, nc = targets[rc]
            accum[nr, nc]  += accum[rc]
            in_deg[nr, nc] -= 1
            if in_deg[nr, nc] == 0:
                queue.append((nr, nc))
    return accum


def compute_log_flow_accumulation(dem: np.ndarray) -> np.ndarray:
    return np.log1p(accumulate(d8_directions(dem))).astype(np.float32)


def compute_and_cache(dem_path: str | Path, cache_path: str | Path) -> np.ndarray:
    cache_path = Path(cache_path)
    if cache_path.exists():
        return load_grid(cache_path)
    accum = compute_log_flow_accumulation(load_grid(dem_path).astype(np.float64))
    save_grid(accum, cache_path)
    return accum
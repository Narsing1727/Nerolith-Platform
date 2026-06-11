"""
Clusters grid cells into geographic regions using watershed boundaries.
Called once at simulation init to define RegionAgent territories.
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from core.schemas import RegionConfig, BoundingBox
import uuid


def cluster_from_boundaries(
    boundary_map: np.ndarray,
    cell_size_m: float = 30.0,
    elevation_grid: Optional[np.ndarray] = None
) -> List[RegionConfig]:
    region_ids_map: Dict[int, str] = {}
    regions: List[RegionConfig] = []

    unique_labels = np.unique(boundary_map)
    unique_labels = unique_labels[unique_labels > 0]

    for label in unique_labels:
        mask = boundary_map == label
        rows, cols = np.where(mask)

        if len(rows) == 0:
            continue

        bbox = BoundingBox(
            row_start=int(rows.min()),
            row_end=int(rows.max()) + 1,
            col_start=int(cols.min()),
            col_end=int(cols.max()) + 1
        )

        area = float(len(rows)) * (cell_size_m ** 2)

        elev_mean = None
        if elevation_grid is not None:
            elev_mean = float(np.mean(elevation_grid[mask]))

        region_id = str(uuid.uuid4())
        region_ids_map[int(label)] = region_id

        regions.append(RegionConfig(
            region_id=region_id,
            name=f"Region_{int(label):03d}",
            bbox=bbox,
            area_m2=area,
            elevation_mean_m=elev_mean
        ))

    _assign_flow_relationships(regions, boundary_map, region_ids_map)

    return regions


def _assign_flow_relationships(
    regions: List[RegionConfig],
    boundary_map: np.ndarray,
    label_to_id: Dict[int, str]
):
    rows, cols = boundary_map.shape
    adjacency: Dict[str, set] = {r.region_id: set() for r in regions}

    for r in regions:
        bb = r.bbox
        border_rows = list(range(bb.row_start, bb.row_end))
        border_cols = list(range(bb.col_start, bb.col_end))

        edge_cells: List[Tuple[int, int]] = []
        for row in [bb.row_start, bb.row_end - 1]:
            for col in border_cols:
                edge_cells.append((row, col))
        for col in [bb.col_start, bb.col_end - 1]:
            for row in border_rows:
                edge_cells.append((row, col))

        for row, col in edge_cells:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    neighbor_label = int(boundary_map[nr, nc])
                    neighbor_id = label_to_id.get(neighbor_label)
                    if neighbor_id and neighbor_id != r.region_id:
                        adjacency[r.region_id].add(neighbor_id)

    for r in regions:
        r.downstream_ids = list(adjacency[r.region_id])


def cluster_uniform_grid(
    grid_rows: int,
    grid_cols: int,
    n_row_splits: int,
    n_col_splits: int
) -> List[RegionConfig]:
    row_step = grid_rows // n_row_splits
    col_step = grid_cols // n_col_splits
    regions: List[RegionConfig] = []
    idx = 1

    for i in range(n_row_splits):
        for j in range(n_col_splits):
            r_start = i * row_step
            r_end = r_start + row_step if i < n_row_splits - 1 else grid_rows
            c_start = j * col_step
            c_end = c_start + col_step if j < n_col_splits - 1 else grid_cols

            regions.append(RegionConfig(
                region_id=str(uuid.uuid4()),
                name=f"Zone_{idx:03d}",
                bbox=BoundingBox(
                    row_start=r_start,
                    row_end=r_end,
                    col_start=c_start,
                    col_end=c_end
                )
            ))
            idx += 1

    _link_grid_neighbors(regions, n_row_splits, n_col_splits)
    return regions


def _link_grid_neighbors(regions: List[RegionConfig], n_rows: int, n_cols: int):
    for idx, region in enumerate(regions):
        row_idx = idx // n_cols
        col_idx = idx % n_cols
        neighbors = []

        if row_idx + 1 < n_rows:
            neighbors.append(regions[(row_idx + 1) * n_cols + col_idx].region_id)
        if col_idx + 1 < n_cols:
            neighbors.append(regions[row_idx * n_cols + col_idx + 1].region_id)

        region.downstream_ids = neighbors
"""
Builds a spatial knowledge graph from DEM and watershed data.
Nodes = regions/sub-catchments. Edges = flow connectivity.
Uses NetworkX as the graph backend.
"""
import networkx as nx
import numpy as np
from typing import Optional
from datetime import datetime, timezone

from core.region_registry import registry
from graph.graph_schema import TerrainNode, FlowEdge, WatershedCluster, TerrainGraph


def build_graph(flow_direction_grid: Optional[np.ndarray] = None) -> nx.DiGraph:
    G = nx.DiGraph()

    for region in registry.all():
        bb = region.bbox
        centroid_row = (bb.row_start + bb.row_end) / 2.0
        centroid_col = (bb.col_start + bb.col_end) / 2.0

        node = TerrainNode(
            region_id=region.region_id,
            name=region.name,
            centroid_row=centroid_row,
            centroid_col=centroid_col,
            elevation_mean_m=region.elevation_mean_m,
            area_m2=region.area_m2
        )
        G.add_node(region.region_id, data=node)

    for region in registry.all():
        for downstream_id in region.downstream_ids:
            if G.has_node(downstream_id):
                weight = _compute_flow_weight(region.region_id, downstream_id, flow_direction_grid)
                edge = FlowEdge(
                    source_id=region.region_id,
                    target_id=downstream_id,
                    flow_weight=weight
                )
                G.add_edge(region.region_id, downstream_id, data=edge, weight=weight)

    return G


def _compute_flow_weight(
    source_id: str,
    target_id: str,
    flow_grid: Optional[np.ndarray]
) -> float:
    if flow_grid is None:
        return 1.0

    source = registry.get(source_id)
    target = registry.get(target_id)
    if not source or not target:
        return 1.0

    sb = source.bbox
    tb = target.bbox

    source_cells = (sb.row_end - sb.row_start) * (sb.col_end - sb.col_start)
    target_cells = (tb.row_end - tb.row_start) * (tb.col_end - tb.col_start)

    if source_cells == 0:
        return 1.0

    return round(min(target_cells / source_cells, 5.0), 3)


def graph_to_schema(G: nx.DiGraph) -> TerrainGraph:
    nodes = [data["data"] for _, data in G.nodes(data=True) if "data" in data]
    edges = [data["data"] for _, _, data in G.edges(data=True) if "data" in data]

    return TerrainGraph(
        nodes=nodes,
        edges=edges,
        built_at=datetime.now(timezone.utc).isoformat()
    )
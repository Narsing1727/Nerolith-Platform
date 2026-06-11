"""
Persists and loads the terrain graph from JSON.
Supports incremental updates as simulation evolves.
"""
import json
import os
import networkx as nx
from typing import Optional

from graph.graph_schema import TerrainGraph, TerrainNode, FlowEdge
from config import settings


def save_graph(G: nx.DiGraph, run_id: Optional[str] = None):
    path = _graph_path(run_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = nx.node_link_data(G)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    _save_summary(G, run_id)


def load_graph(run_id: Optional[str] = None) -> Optional[nx.DiGraph]:
    path = _graph_path(run_id)
    if not os.path.exists(path):
        return None

    with open(path) as f:
        data = json.load(f)

    return nx.node_link_graph(data, directed=True)


def _save_summary(G: nx.DiGraph, run_id: Optional[str]):
    try:
        longest = max(
            (nx.dag_longest_path_length(G),), default=0
        )[0] if nx.is_directed_acyclic_graph(G) else -1
    except Exception:
        longest = -1

    summary = {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "longest_flow_path": longest
    }

    path = _graph_path(run_id).replace("graph.json", "graph_summary.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)


def _graph_path(run_id: Optional[str]) -> str:
    if run_id:
        return os.path.join(settings.output_dir, "runs", run_id, "graph", "graph.json")
    return os.path.join(settings.data_dir, "graph.json")
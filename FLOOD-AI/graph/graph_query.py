"""
Graph query facade.
get_upstream_regions(), get_downstream_regions(), get_flow_path(), etc.
Used by agents to understand spatial relationships.
"""
import networkx as nx
from typing import List, Optional


class GraphQuery:
    def __init__(self):
        self._G: Optional[nx.DiGraph] = None

    def load(self, G: nx.DiGraph):
        self._G = G

    def get_upstream(self, region_id: str, hops: int = 2) -> List[str]:
        if not self._G or region_id not in self._G:
            return []
        result = set()
        frontier = {region_id}
        for _ in range(hops):
            next_frontier = set()
            for node in frontier:
                preds = set(self._G.predecessors(node))
                next_frontier |= preds - result - {region_id}
            result |= next_frontier
            frontier = next_frontier
        return list(result)

    def get_downstream(self, region_id: str, hops: int = 2) -> List[str]:
        if not self._G or region_id not in self._G:
            return []
        result = set()
        frontier = {region_id}
        for _ in range(hops):
            next_frontier = set()
            for node in frontier:
                succs = set(self._G.successors(node))
                next_frontier |= succs - result - {region_id}
            result |= next_frontier
            frontier = next_frontier
        return list(result)

    def get_flow_path(self, source_id: str, target_id: str) -> List[str]:
        if not self._G:
            return []
        try:
            return nx.shortest_path(self._G, source_id, target_id, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_at_risk_downstream(self, region_id: str) -> List[str]:
        return self.get_downstream(region_id, hops=10)

    def has_node(self, region_id: str) -> bool:
        return self._G is not None and region_id in self._G

    def is_loaded(self) -> bool:
        return self._G is not None


graph_query = GraphQuery()
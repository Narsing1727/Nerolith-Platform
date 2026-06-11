"""
Pydantic models for graph nodes and edges.
TerrainNode, FlowEdge, WatershedCluster, etc.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid


class TerrainNode(BaseModel):
    region_id: str
    name: str
    centroid_row: float
    centroid_col: float
    elevation_mean_m: Optional[float] = None
    area_m2: Optional[float] = None
    catchment_id: Optional[str] = None


class FlowEdge(BaseModel):
    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: str
    flow_weight: float = 1.0
    connected_cells: int = 0


class WatershedCluster(BaseModel):
    catchment_id: str
    name: str
    region_ids: List[str] = []
    outlet_region_id: Optional[str] = None


class TerrainGraph(BaseModel):
    nodes: List[TerrainNode] = []
    edges: List[FlowEdge] = []
    clusters: List[WatershedCluster] = []
    built_at: Optional[str] = None
"""
Shared Pydantic models used across core, agents, and API.
Region, GridCell, RiskLevel, AlertEvent, SimulationRun, etc.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime
import uuid


class RiskLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class BoundingBox(BaseModel):
    row_start: int
    row_end: int
    col_start: int
    col_end: int


class RegionConfig(BaseModel):
    region_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    bbox: BoundingBox
    upstream_ids: List[str] = []
    downstream_ids: List[str] = []
    area_m2: Optional[float] = None
    elevation_mean_m: Optional[float] = None


class RegionObservation(BaseModel):
    region_id: str
    timestep: int
    flood_stats: Dict[str, float]
    flow_stats: Dict[str, float]
    rainfall_stats: Dict[str, float]
    risk_level: RiskLevel
    anomalies: List[str] = []
    observed_at: datetime = Field(default_factory=datetime.utcnow)


class AlertEvent(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    region_id: str
    severity: AlertSeverity
    message: str
    timestep: int
    acknowledged: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SimulationRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    region_count: int = 0
    total_timesteps: int = 0
    active: bool = False


class CoordinatorDecision(BaseModel):
    timestep: int
    global_risk: RiskLevel
    region_risks: Dict[str, RiskLevel]
    alerts_issued: List[AlertEvent] = []
    propagation_warnings: List[str] = []
    decided_at: datetime = Field(default_factory=datetime.utcnow)
"""
cascade_schemas.py
All data structures for the Cascade system.
CascadeNode, CascadeEvent, CascadeStatus, NodeState.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid


class CascadeNodeType(str, Enum):
    SLOPE_STABILITY  = "SlopeStability"
    RIVER_BLOCKAGE   = "RiverBlockage"
    DAM_BREACH       = "DamBreach"
    FLOOD_WAVE       = "FloodWave"


class CascadeNodeStatus(str, Enum):
    DORMANT   = "dormant"    # not yet watching
    WATCHING  = "watching"   # conditions being monitored
    TRIGGERED = "triggered"  # threshold crossed, node fired
    RESOLVED  = "resolved"   # event passed


class CascadeSeverity(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class NodeState(BaseModel):
    """
    Live state of a single cascade node.
    Updated every timestep by CascadeEngine.
    """
    node_type:        CascadeNodeType
    status:           CascadeNodeStatus = CascadeNodeStatus.DORMANT
    probability:      float = 0.0        # 0.0 → 1.0
    last_checked_at:  Optional[datetime] = None
    triggered_at:     Optional[datetime] = None
    trigger_count:    int = 0            # how many times fired this run


class CascadeEvent(BaseModel):
    """
    Emitted when a cascade node fires.
    Stored in CascadeStore. Qt polls for these.
    """
    event_id:    str = Field(default_factory=lambda: str(uuid.uuid4()))
    node:        CascadeNodeType
    severity:    CascadeSeverity
    probability: float
    region_id:   str
    timestep:    int
    fired_at:    datetime = Field(default_factory=datetime.utcnow)
    message:     str
    data:        Dict[str, Any] = {}     # node-specific payload
    acknowledged: bool = False


class CascadeStatus(BaseModel):
    """
    Full snapshot of cascade engine state.
    Returned by GET /cascade/status
    """
    run_id:          str
    timestep:        int
    active:          bool
    node_states:     Dict[str, NodeState]   # node_type → state
    total_events:    int
    last_event_at:   Optional[datetime]
    cascade_active:  bool                   # True if any node triggered
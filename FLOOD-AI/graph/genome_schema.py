"""
FloodGenome: per-watershed accumulated intelligence object.
Gets richer after every simulation run validated against reality.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone


@dataclass
class FloodEvent:
    run_id: str
    timestamp: str
    rainfall_mm: float
    max_flood_depth: float
    low_cells: int
    medium_cells: int
    high_cells: int
    high_ratio: float          # high_cells / total_cells
    validated: bool = False    # True once satellite loop confirms
    satellite_divergence: Optional[float] = None  # % divergence if validated


@dataclass
class FloodGenome:
    watershed_id: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Learned thresholds — updated after each event
    avg_rainfall_at_flood: float = 0.0      # mm that reliably produces high-risk
    avg_response_depth: float = 0.0         # mean max flood depth across events
    typical_high_ratio: float = 0.0         # fraction of grid that goes high-risk

    # Calibration params learned from validated events
    best_manning_n: float = 0.035           # default, improves with validation
    best_blend_alpha: float = 0.7           # physics/ML blend ratio

    # Confidence — how many events built this genome
    event_count: int = 0
    validated_event_count: int = 0
    confidence_score: float = 0.0           # 0.0 → 1.0

    # Full event archive
    events: List[FloodEvent] = field(default_factory=list)
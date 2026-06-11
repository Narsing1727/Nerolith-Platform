"""
Physics-grounded risk analysis service.
Takes flood depth + flow velocity + terrain slope â†’ risk score.
Rule-based thresholds combined with LLM interpretation.
NOT a replacement for physics â€” a layer on top of it.
"""
from core.schemas import RiskLevel


DEPTH_WEIGHT = 0.5
VELOCITY_WEIGHT = 0.3
RAINFALL_WEIGHT = 0.2

DEPTH_SCALE = 1.5
VELOCITY_SCALE = 2.0
RAINFALL_SCALE = 50.0


def composite_score(
    flood_depth_m: float,
    flow_velocity_ms: float,
    rainfall_mmph: float
) -> float:
    d = min(flood_depth_m / DEPTH_SCALE, 1.0)
    v = min(flow_velocity_ms / VELOCITY_SCALE, 1.0)
    r = min(rainfall_mmph / RAINFALL_SCALE, 1.0)
    return round(DEPTH_WEIGHT * d + VELOCITY_WEIGHT * v + RAINFALL_WEIGHT * r, 4)


def score_to_risk(score: float) -> RiskLevel:
    if score >= 0.75:
        return RiskLevel.CRITICAL
    elif score >= 0.50:
        return RiskLevel.HIGH
    elif score >= 0.25:
        return RiskLevel.MEDIUM
    elif score > 0.05:
        return RiskLevel.LOW
    return RiskLevel.NONE


def analyze_region(
    flood_stats: dict,
    flow_stats: dict,
    rainfall_stats: dict
) -> dict:
    depth = flood_stats.get("max", 0.0)
    velocity = flow_stats.get("max", 0.0)
    rainfall = rainfall_stats.get("mean", 0.0)

    score = composite_score(depth, velocity, rainfall)
    risk = score_to_risk(score)

    return {
        "composite_score": score,
        "risk_level": risk,
        "depth_contribution": round(DEPTH_WEIGHT * min(depth / DEPTH_SCALE, 1.0), 4),
        "velocity_contribution": round(VELOCITY_WEIGHT * min(velocity / VELOCITY_SCALE, 1.0), 4),
        "rainfall_contribution": round(RAINFALL_WEIGHT * min(rainfall / RAINFALL_SCALE, 1.0), 4)
    }
"""
RegionAgent: monitors one geographic region.
- Reads flood depth, flow velocity, and rainfall from engine_bridge
- Detects anomalies: rapid rise, threshold breach, accumulation hotspot
- Maintains short-term memory of recent timesteps for this region
- Reports local risk assessment to CoordinatorAgent
Inspired by MiroFish's individual agent with memory pattern,
adapted for physical spatial zones instead of social personas.
"""
from agents.base_agent import BaseFloodAgent
from agents.agent_memory import AgentMemory
from core.schemas import RegionConfig, RegionObservation, RiskLevel
from engine_bridge.engine_schema import EngineTickPayload
from engine_bridge.grid_parser import (
    parse_flood_grid,
    parse_flow_grid,
    parse_rainfall_grid,
    extract_region_slice,
    compute_region_stats
)
from typing import List, Any


DEPTH_THRESHOLDS = {
    RiskLevel.LOW: 0.1,
    RiskLevel.MEDIUM: 0.3,
    RiskLevel.HIGH: 0.6,
    RiskLevel.CRITICAL: 1.2
}

RISE_RATE_THRESHOLD = 0.08


class RegionAgent(BaseFloodAgent):
    def __init__(self, region: RegionConfig):
        super().__init__(region.region_id)
        self.region = region
        self.memory = AgentMemory(region.region_id)

    def observe(self, payload: EngineTickPayload) -> RegionObservation:
        bb = self.region.bbox

        flood_grid = parse_flood_grid(payload.flood)
        flow_grid = parse_flow_grid(payload.flow)
        rain_grid = parse_rainfall_grid(payload.rainfall)

        flood_slice = extract_region_slice(flood_grid, bb.row_start, bb.row_end, bb.col_start, bb.col_end)
        flow_slice = extract_region_slice(flow_grid, bb.row_start, bb.row_end, bb.col_start, bb.col_end)
        rain_slice = extract_region_slice(rain_grid, bb.row_start, bb.row_end, bb.col_start, bb.col_end)

        flood_stats = compute_region_stats(flood_slice)
        flow_stats = compute_region_stats(flow_slice)
        rainfall_stats = compute_region_stats(rain_slice)

        risk = self._score_risk(flood_stats)
        anomalies = self._detect_anomalies(flood_stats)

        return RegionObservation(
            region_id=self.region_id,
            timestep=payload.timestep,
            flood_stats=flood_stats,
            flow_stats=flow_stats,
            rainfall_stats=rainfall_stats,
            risk_level=risk,
            anomalies=anomalies
        )

    def analyze(self, observation: RegionObservation) -> dict:
        self.memory.push(observation)
        trend = self.memory.flood_trend()
        peak = self.memory.peak_risk()
        recent = self.memory.recent(3)

        rising_fast = trend == "rising" and observation.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

        return {
            "observation": observation,
            "trend": trend,
            "peak_risk": peak,
            "rising_fast": rising_fast,
            "recent_count": len(recent)
        }

    def decide(self, analysis: dict) -> dict:
        obs: RegionObservation = analysis["observation"]
        return {
            "region_id": self.region_id,
            "timestep": obs.timestep,
            "risk_level": obs.risk_level,
            "trend": analysis["trend"],
            "peak_risk": analysis["peak_risk"],
            "rising_fast": analysis["rising_fast"],
            "anomalies": obs.anomalies,
            "flood_max_m": obs.flood_stats.get("max", 0),
            "flood_mean_m": obs.flood_stats.get("mean", 0),
            "flooded_cells": obs.flood_stats.get("flooded_cells", 0),
            "total_cells": obs.flood_stats.get("total_cells", 0)
        }

    def _score_risk(self, flood_stats: dict) -> RiskLevel:
        max_depth = flood_stats.get("max", 0)
        if max_depth >= DEPTH_THRESHOLDS[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif max_depth >= DEPTH_THRESHOLDS[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif max_depth >= DEPTH_THRESHOLDS[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        elif max_depth >= DEPTH_THRESHOLDS[RiskLevel.LOW]:
            return RiskLevel.LOW
        return RiskLevel.NONE

    def _detect_anomalies(self, flood_stats: dict) -> List[str]:
        anomalies = []
        recent = self.memory.recent(2)

        if len(recent) >= 1:
            prev_mean = recent[-1].flood_stats.get("mean", 0)
            curr_mean = flood_stats.get("mean", 0)
            if curr_mean - prev_mean > RISE_RATE_THRESHOLD:
                anomalies.append(f"rapid_rise:{round(curr_mean - prev_mean, 3)}m_per_step")

        coverage = flood_stats.get("flooded_cells", 0) / max(flood_stats.get("total_cells", 1), 1)
        if coverage > 0.6:
            anomalies.append(f"high_coverage:{round(coverage * 100, 1)}pct")

        if flood_stats.get("max", 0) > 2.0:
            anomalies.append("extreme_depth_detected")

        return anomalies
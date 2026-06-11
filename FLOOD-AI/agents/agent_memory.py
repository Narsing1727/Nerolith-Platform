"""
AgentMemory: short-term and long-term memory for agents.
Short-term: sliding window of last N timestep observations (in-memory).
Long-term: persisted JSON snapshots of key events (threshold breaches, peaks).
Inspired by MiroFish's temporal memory update pattern.
"""
from collections import deque
from typing import List, Optional
from core.schemas import RegionObservation, RiskLevel
from config import settings
import json
import os
from datetime import datetime


class AgentMemory:
    def __init__(self, region_id: str):
        self.region_id = region_id
        self._short_term: deque[RegionObservation] = deque(maxlen=settings.agent_memory_window)
        self._long_term: List[dict] = []
        self._peak_risk: RiskLevel = RiskLevel.NONE

    def push(self, observation: RegionObservation):
        self._short_term.append(observation)
        self._update_peak(observation.risk_level)
        if observation.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            self._commit_to_long_term(observation)

    def _update_peak(self, level: RiskLevel):
        order = [RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        if order.index(level) > order.index(self._peak_risk):
            self._peak_risk = level

    def _commit_to_long_term(self, observation: RegionObservation):
        self._long_term.append({
            "timestep": observation.timestep,
            "risk_level": observation.risk_level,
            "max_flood_depth": observation.flood_stats.get("max", 0),
            "anomalies": observation.anomalies,
            "recorded_at": datetime.utcnow().isoformat()
        })

    def recent(self, n: int = 5) -> List[RegionObservation]:
        items = list(self._short_term)
        return items[-n:]

    def peak_risk(self) -> RiskLevel:
        return self._peak_risk

    def long_term_events(self) -> List[dict]:
        return self._long_term

    def flood_trend(self) -> str:
        recent = self.recent(5)
        if len(recent) < 2:
            return "insufficient_data"
        depths = [r.flood_stats.get("mean", 0) for r in recent]
        diffs = [depths[i+1] - depths[i] for i in range(len(depths)-1)]
        avg_diff = sum(diffs) / len(diffs)
        if avg_diff > 0.05:
            return "rising"
        elif avg_diff < -0.05:
            return "falling"
        return "stable"

    def save(self, run_id: str):
        path = os.path.join(settings.output_dir, "runs", run_id, "memory")
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, f"{self.region_id}.json"), "w") as f:
            json.dump({
                "region_id": self.region_id,
                "peak_risk": self._peak_risk,
                "long_term_events": self._long_term
            }, f, indent=2)

    def clear(self):
        self._short_term.clear()
        self._long_term.clear()
        self._peak_risk = RiskLevel.NONE
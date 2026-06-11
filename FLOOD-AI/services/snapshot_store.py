"""
Stores and retrieves per-timestep simulation snapshots.
Each snapshot: {timestep, flood_grid, agent_reports, alerts_issued}
Used by ReportAgent to reconstruct simulation history.
"""
from typing import List, Dict, Optional
from core.schemas import CoordinatorDecision
from config import settings
import json
import os


class SnapshotStore:
    def __init__(self):
        self._snapshots: List[dict] = []
        self._run_id: Optional[str] = None

    def set_run(self, run_id: str):
        self._run_id = run_id
        self._snapshots.clear()

    def save_snapshot(
        self,
        timestep: int,
        region_reports: List[dict],
        decision: CoordinatorDecision
    ):
        snapshot = {
            "timestep": timestep,
            "global_risk": decision.global_risk,
            "region_risks": decision.region_risks,
            "alerts_count": len(decision.alerts_issued),
            "propagation_warnings": decision.propagation_warnings,
            "region_reports": [
                {
                    "region_id": r["region_id"],
                    "risk_level": r["risk_level"],
                    "flood_max_m": r["flood_max_m"],
                    "flood_mean_m": r["flood_mean_m"],
                    "flooded_cells": r["flooded_cells"],
                    "trend": r["trend"],
                    "anomalies": r["anomalies"]
                }
                for r in region_reports
            ]
        }
        self._snapshots.append(snapshot)

        if self._run_id:
            self._write_snapshot(timestep, snapshot)

    def _write_snapshot(self, timestep: int, snapshot: dict):
        path = os.path.join(settings.output_dir, "runs", self._run_id, "snapshots")
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, f"t{timestep:06d}.json"), "w") as f:
            json.dump(snapshot, f, indent=2)

    def all(self) -> List[dict]:
        return self._snapshots

    def get(self, timestep: int) -> Optional[dict]:
        for s in self._snapshots:
            if s["timestep"] == timestep:
                return s
        return None

    def latest(self) -> Optional[dict]:
        return self._snapshots[-1] if self._snapshots else None

    def clear(self):
        self._snapshots.clear()
        self._run_id = None


snapshot_store = SnapshotStore()
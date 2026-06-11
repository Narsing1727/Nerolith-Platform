"""
SimulationSession: holds the current active simulation state.
Tracks which regions are registered, current timestep, run ID.
"""
from typing import Optional
from datetime import datetime
from core.schemas import SimulationRun
import uuid


class SimulationSession:
    def __init__(self):
        self._run: Optional[SimulationRun] = None
        self._current_timestep: int = 0

    def start(self) -> SimulationRun:
        self._run = SimulationRun(
            run_id=str(uuid.uuid4()),
            started_at=datetime.utcnow(),
            active=True
        )
        self._current_timestep = 0
        return self._run

    def stop(self):
        if self._run:
            self._run.active = False
            self._run.ended_at = datetime.utcnow()
            self._run.total_timesteps = self._current_timestep

    def tick(self):
        self._current_timestep += 1
        if self._run:
            self._run.total_timesteps = self._current_timestep

    def is_active(self) -> bool:
        return self._run is not None and self._run.active

    def current_timestep(self) -> int:
        return self._current_timestep

    def get_run(self) -> Optional[SimulationRun]:
        return self._run

    def set_region_count(self, count: int):
        if self._run:
            self._run.region_count = count


session = SimulationSession()
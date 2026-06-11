"""
BaseFloodAgent: abstract base class for all agents.
Defines the observe() -> analyze() -> decide() loop.
All agents inherit from this.
"""
from abc import ABC, abstractmethod
from typing import Any
from core.schemas import RegionObservation
from engine_bridge.engine_schema import EngineTickPayload


class BaseFloodAgent(ABC):
    def __init__(self, region_id: str):
        self.region_id = region_id
        self._active = True

    @abstractmethod
    def observe(self, payload: EngineTickPayload) -> RegionObservation:
        pass

    @abstractmethod
    def analyze(self, observation: RegionObservation) -> Any:
        pass

    @abstractmethod
    def decide(self, analysis: Any) -> Any:
        pass

    def run(self, payload: EngineTickPayload) -> Any:
        observation = self.observe(payload)
        analysis = self.analyze(observation)
        return self.decide(analysis)

    def deactivate(self):
        self._active = False

    def is_active(self) -> bool:
        return self._active
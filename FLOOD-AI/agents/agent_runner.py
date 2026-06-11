"""
AgentRunner: orchestrates the full agent cycle per timestep.
1. Trigger all RegionAgents to observe()
2. Collect their reports
3. Send to CoordinatorAgent for global analysis
4. Route alerts via AlertAgent
5. Store snapshot for ReportAgent
"""
from typing import Dict, List
from agents.region_agent import RegionAgent
from agents.coordinator_agent import coordinator
from agents.alert_agent import alert_agent
from core.schemas import CoordinatorDecision
from core.region_registry import registry
from engine_bridge.engine_schema import EngineTickPayload
from services.snapshot_store import snapshot_store
from loguru import logger


class AgentRunner:
    def __init__(self):
        self._region_agents: Dict[str, RegionAgent] = {}

    def build_agents(self):
        self._region_agents.clear()
        for region in registry.all():
            self._region_agents[region.region_id] = RegionAgent(region)
        logger.info(f"AgentRunner: built {len(self._region_agents)} region agents")

    def run_cycle(self, payload: EngineTickPayload) -> CoordinatorDecision:
        region_reports = []

        for region_id, agent in self._region_agents.items():
            if not agent.is_active():
                continue
            try:
                report = agent.run(payload)
                region_reports.append(report)
            except Exception as e:
                logger.error(f"RegionAgent {region_id} failed at timestep {payload.timestep}: {e}")

        decision = coordinator.process(payload.timestep, region_reports)

        alert_agent.dispatch(decision.alerts_issued)

        snapshot_store.save_snapshot(payload.timestep, region_reports, decision)

        return decision

    def get_agent(self, region_id: str) -> RegionAgent:
        return self._region_agents.get(region_id)

    def agent_count(self) -> int:
        return len(self._region_agents)

    def reset(self):
        self._region_agents.clear()


agent_runner = AgentRunner()
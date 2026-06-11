"""
cascade_agent.py
Plugs cascade engine into the existing MiroFish agent system.
Called by agent_runner each timestep alongside RegionAgents.
Extracts sim_state from region reports and feeds CascadeEngine.
"""
from typing import List, Dict, Any, Optional
from loguru import logger

from cascade.cascade_engine import cascade_engine
from cascade.cascade_schemas import CascadeEvent
from core.schemas import RiskLevel


class CascadeAgent:
    """
    Sits alongside CoordinatorAgent in the agent pipeline.
    Every timestep:
      1. Receives region reports from RegionAgents
      2. Extracts relevant state per high-risk region
      3. Feeds CascadeEngine.evaluate()
      4. Returns fired CascadeEvents (for logging/alert routing)

    Does NOT replace CoordinatorAgent — runs in parallel.
    """

    def __init__(self):
        self._initialized = False
        self._last_events: List[CascadeEvent] = []

    def init(self, run_id: str):
        cascade_engine.init_run(run_id)
        self._initialized = True
        logger.info(f"CascadeAgent initialized for run: {run_id}")

    def process(
        self,
        timestep: int,
        region_reports: List[dict],
        extra_state: Optional[Dict[str, Any]] = None
    ) -> List[CascadeEvent]:
        """
        Called every timestep by agent_runner.

        region_reports: list of dicts from RegionAgent.observe()
        extra_state: optional additional physics state from Qt/engine bridge
          e.g. {
            "soil_saturation": 0.82,
            "slope_angle_deg": 32.0,
            "lake_rise_rate_m_per_hr": 0.7,
            ...
          }
        """
        if not self._initialized:
            logger.warning("CascadeAgent not initialized — call init(run_id) first")
            return []

        all_fired: List[CascadeEvent] = []

        # Find the highest risk region to run cascade evaluation on
        # (cascade is a basin-level event — we pick the most at-risk region)
        critical_reports = [
            r for r in region_reports
            if r.get("risk_level") in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        ]

        if not critical_reports:
            return []

        # Sort by risk level descending
        critical_reports.sort(
            key=lambda r: (
                1 if r.get("risk_level") == RiskLevel.CRITICAL else 0
            ),
            reverse=True
        )

        # Evaluate cascade for the most critical region
        primary = critical_reports[0]
        region_id = primary.get("region_id", "unknown")

        # Build sim_state from region report + extra_state
        sim_state = self._build_sim_state(primary, extra_state or {})

        fired = cascade_engine.evaluate(timestep, region_id, sim_state)
        all_fired.extend(fired)

        if fired:
            logger.warning(
                f"CascadeAgent: {len(fired)} cascade events fired "
                f"at timestep={timestep} | region={region_id}"
            )

        self._last_events = all_fired
        return all_fired

    def get_status(self, timestep: int):
        return cascade_engine.get_status(timestep)

    def last_events(self) -> List[CascadeEvent]:
        return self._last_events

    def reset(self):
        cascade_engine.reset()
        self._last_events = []

    # ── PRIVATE ──────────────────────────────────────────────────────────────

    def _build_sim_state(
        self,
        report: dict,
        extra: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Maps region report fields to cascade engine sim_state keys.
        extra_state from Qt engine bridge overrides report values.
        """
        flood_stats    = report.get("flood_stats", {})
        flow_stats     = report.get("flow_stats", {})
        rainfall_stats = report.get("rainfall_stats", {})

        # Base state from region report
        state: Dict[str, Any] = {
            "rainfall_mm":       rainfall_stats.get("total_mm", 0.0),
            "upstream_flow_m3s": flow_stats.get("mean_velocity", 1.0) * 30.0 * 5.0,

            # Defaults — overridden by extra if available
            "soil_saturation":          0.0,
            "slope_angle_deg":          0.0,
            "slope_area_m2":            10000.0,
            "channel_width_m":          30.0,
            "channel_depth_m":          5.0,
            "lake_rise_rate_m_per_hr":  0.0,
            "channel_slope":            0.002,
            "manning_n":                0.035,
            "dam_height_m":             10.0,
        }

        # Derive soil saturation from flood + rainfall if not in extra
        # Simple heuristic: more rain + more flood = more saturated
        if "soil_saturation" not in extra:
            rain_intensity = rainfall_stats.get("total_mm", 0.0)
            flood_mean     = flood_stats.get("mean_depth_m", 0.0)
            # Rough saturation proxy
            state["soil_saturation"] = min(
                (rain_intensity / 200.0) * 0.6 +
                (flood_mean / 2.0) * 0.4,
                1.0
            )

        # Override with extra_state from Qt engine bridge
        state.update(extra)

        return state


# Singleton
cascade_agent = CascadeAgent()
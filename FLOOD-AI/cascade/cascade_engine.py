"""
cascade_engine.py
Orchestrates all four cascade nodes every timestep.
Receives simulation state, evaluates nodes in order,
pushes fired events to CascadeStore.
Called by CascadeAgent each timestep.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from cascade.cascade_nodes import (
    SlopeStabilityNode,
    RiverBlockageNode,
    DamBreachNode,
    FloodWaveNode,
)
from cascade.cascade_schemas import (
    CascadeEvent,
    CascadeStatus,
    CascadeNodeType,
)
from cascade.cascade_store import cascade_store
from core.region_registry import registry


class CascadeEngine:
    """
    Evaluates all cascade nodes in sequence each timestep.
    Nodes fire in order — each fired node enriches sim_state
    for the next node (SlopeStability output feeds RiverBlockage, etc.)
    """

    def __init__(self):
        self._nodes = {
            CascadeNodeType.SLOPE_STABILITY: SlopeStabilityNode(),
            CascadeNodeType.RIVER_BLOCKAGE:  RiverBlockageNode(),
            CascadeNodeType.DAM_BREACH:      DamBreachNode(),
            CascadeNodeType.FLOOD_WAVE:      FloodWaveNode(),
        }
        self._run_id: Optional[str] = None

        # Accumulated state carried forward between timesteps
        # Nodes enrich this as they fire
        self._carry: Dict[str, Any] = {
            "slope_stability_fired": False,
            "river_blockage_fired":  False,
            "dam_breach_fired":      False,
            "debris_volume_m3":      0.0,
            "blockage_ratio":        0.0,
            "peak_discharge_m3s":    0.0,
            "lake_volume_m3":        0.0,
            "dam_height_m":          10.0,
        }

    def init_run(self, run_id: str):
        self._run_id = run_id
        self._carry = {
            "slope_stability_fired": False,
            "river_blockage_fired":  False,
            "dam_breach_fired":      False,
            "debris_volume_m3":      0.0,
            "blockage_ratio":        0.0,
            "peak_discharge_m3s":    0.0,
            "lake_volume_m3":        0.0,
            "dam_height_m":          10.0,
        }
        cascade_store.set_run(run_id)
        logger.info(f"CascadeEngine initialized for run: {run_id}")

    def evaluate(
        self,
        timestep: int,
        region_id: str,
        sim_state: Dict[str, Any]
    ) -> List[CascadeEvent]:
        """
        Main entry point. Called every timestep by CascadeAgent.

        sim_state should contain:
          soil_saturation       float 0.0-1.0
          slope_angle_deg       float degrees
          slope_area_m2         float m²
          rainfall_mm           float mm
          channel_width_m       float m
          channel_depth_m       float m
          upstream_flow_m3s     float m³/s
          lake_rise_rate_m_per_hr float m/hr
          channel_slope         float m/m
          manning_n             float
          downstream_regions    list of {region_id, name, distance_m}
        """

        # Merge incoming state with carried forward state
        full_state = {**self._carry, **sim_state}
        full_state["timestep"]  = timestep
        full_state["region_id"] = region_id

        # Add downstream region configs from registry
        if "downstream_regions" not in full_state:
            downstream = registry.get_downstream(region_id)
            full_state["downstream_regions"] = [
                {
                    "region_id":  r.region_id,
                    "name":       r.name,
                    "distance_m": 10000.0  # default — override with real distance
                }
                for r in downstream
            ]

        fired_events: List[CascadeEvent] = []

        # ── NODE 1: SLOPE STABILITY ──────────────────────────────────────────
        slope_node = self._nodes[CascadeNodeType.SLOPE_STABILITY]
        slope_event = slope_node.evaluate(full_state)
        cascade_store.update_node_state(
            CascadeNodeType.SLOPE_STABILITY, slope_node.state
        )

        if slope_event:
            fired_events.append(slope_event)
            cascade_store.push(slope_event)
            # Carry forward for next node
            self._carry["slope_stability_fired"] = True
            self._carry["debris_volume_m3"] = slope_event.data.get(
                "debris_volume_m3", 0.0
            )
            full_state["slope_stability_fired"] = True
            full_state["debris_volume_m3"] = self._carry["debris_volume_m3"]

        # ── NODE 2: RIVER BLOCKAGE ───────────────────────────────────────────
        blockage_node = self._nodes[CascadeNodeType.RIVER_BLOCKAGE]
        blockage_event = blockage_node.evaluate(full_state)
        cascade_store.update_node_state(
            CascadeNodeType.RIVER_BLOCKAGE, blockage_node.state
        )

        if blockage_event:
            fired_events.append(blockage_event)
            cascade_store.push(blockage_event)
            self._carry["river_blockage_fired"] = True
            self._carry["blockage_ratio"] = blockage_event.data.get(
                "blockage_ratio", 0.0
            )
            # Estimate lake volume from blockage data
            lake_formation_hours = blockage_event.data.get("lake_formation_hours", 1.0)
            upstream_flow        = full_state.get("upstream_flow_m3s", 50.0)
            self._carry["lake_volume_m3"] = max(
    lake_formation_hours * 3600 * upstream_flow * 0.3,
    full_state.get("lake_volume_m3", 20000.0)
)
            full_state["river_blockage_fired"] = True
            full_state["blockage_ratio"]       = self._carry["blockage_ratio"]
            full_state["lake_volume_m3"]       = self._carry["lake_volume_m3"]

        # ── NODE 3: DAM BREACH ───────────────────────────────────────────────
        breach_node = self._nodes[CascadeNodeType.DAM_BREACH]
        breach_event = breach_node.evaluate(full_state)
        cascade_store.update_node_state(
            CascadeNodeType.DAM_BREACH, breach_node.state
        )

        if breach_event:
            fired_events.append(breach_event)
            cascade_store.push(breach_event)
            self._carry["dam_breach_fired"]    = True
            self._carry["peak_discharge_m3s"]  = breach_event.data.get(
                "peak_discharge_m3s", 0.0
            )
            full_state["dam_breach_fired"]   = True
            full_state["peak_discharge_m3s"] = self._carry["peak_discharge_m3s"]

        # ── NODE 4: FLOOD WAVE ───────────────────────────────────────────────
        wave_node = self._nodes[CascadeNodeType.FLOOD_WAVE]
        wave_event = wave_node.evaluate(full_state)
        cascade_store.update_node_state(
            CascadeNodeType.FLOOD_WAVE, wave_node.state
        )

        if wave_event:
            fired_events.append(wave_event)
            cascade_store.push(wave_event)

        if fired_events:
            logger.info(
                f"CascadeEngine: {len(fired_events)} nodes fired "
                f"at timestep {timestep} in region {region_id}"
            )

        return fired_events

    def get_status(self, timestep: int) -> CascadeStatus:
        return CascadeStatus(
            run_id         = self._run_id or "unknown",
            timestep       = timestep,
            active         = self._run_id is not None,
            node_states    = cascade_store.get_node_states(),
            total_events   = cascade_store.total_events(),
            last_event_at  = cascade_store.last_event_at(),
            cascade_active = cascade_store.cascade_active(),
        )

    def reset(self):
        self._carry = {
            "slope_stability_fired": False,
            "river_blockage_fired":  False,
            "dam_breach_fired":      False,
            "debris_volume_m3":      0.0,
            "blockage_ratio":        0.0,
            "peak_discharge_m3s":    0.0,
            "lake_volume_m3":        0.0,
            "dam_height_m":          10.0,
        }
        for node in self._nodes.values():
            node._dormant()


# Singleton
cascade_engine = CascadeEngine()
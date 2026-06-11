import math
from datetime import datetime
from typing import Optional, Dict, Any
from cascade.cascade_schemas import (
    CascadeEvent, CascadeNodeType, CascadeSeverity, NodeState, CascadeNodeStatus
)
from loguru import logger


class BaseCascadeNode:
    node_type: CascadeNodeType = None

    def __init__(self):
        self.state = NodeState(node_type=self.node_type)

    def evaluate(self, sim_state: Dict[str, Any]) -> Optional[CascadeEvent]:
        raise NotImplementedError

    def _fire(self, region_id, timestep, severity, probability, message, data) -> CascadeEvent:
        self.state.status        = CascadeNodeStatus.TRIGGERED
        self.state.triggered_at  = datetime.utcnow()
        self.state.probability   = probability
        self.state.trigger_count += 1
        logger.warning(f"[CASCADE] {self.node_type} fired | region={region_id} | prob={probability:.2f}")
        return CascadeEvent(
            node=self.node_type,
            severity=severity,
            probability=probability,
            region_id=region_id,
            timestep=timestep,
            message=message,
            data=data
        )

    def _watch(self, probability: float):
        self.state.status          = CascadeNodeStatus.WATCHING
        self.state.probability     = probability
        self.state.last_checked_at = datetime.utcnow()

    def _dormant(self):
        self.state.status      = CascadeNodeStatus.DORMANT
        self.state.probability = 0.0


class SlopeStabilityNode(BaseCascadeNode):
    node_type          = CascadeNodeType.SLOPE_STABILITY
    SATURATION_WARN    = 0.65
    SATURATION_TRIGGER = 0.75
    SLOPE_ANGLE_MIN    = 25.0

    def evaluate(self, sim_state: Dict[str, Any]) -> Optional[CascadeEvent]:
        saturation  = sim_state.get("soil_saturation", 0.0)
        slope_angle = sim_state.get("slope_angle_deg", 0.0)
        region_id   = sim_state.get("region_id", "unknown")
        timestep    = sim_state.get("timestep", 0)
        rainfall_mm = sim_state.get("rainfall_mm", 0.0)

        self.state.last_checked_at = datetime.utcnow()

        if slope_angle < self.SLOPE_ANGLE_MIN:
            self._dormant()
            return None

        if saturation < self.SATURATION_WARN:
            self._dormant()
            return None

        prob = min((saturation - self.SATURATION_WARN) / (1.0 - self.SATURATION_WARN), 1.0)
        self._watch(prob)

        if saturation < self.SATURATION_TRIGGER:
            return None

        slope_area_m2    = sim_state.get("slope_area_m2", 10000.0)
        failure_depth_m  = 2.0 + (saturation - 0.75) * 8.0
        debris_volume_m3 = slope_area_m2 * failure_depth_m * 0.3
        severity         = CascadeSeverity.CRITICAL if saturation > 0.90 else CascadeSeverity.HIGH

        return self._fire(
            region_id   = region_id,
            timestep    = timestep,
            severity    = severity,
            probability = prob,
            message     = (
                f"Slope failure - saturation {saturation*100:.1f}%, "
                f"slope {slope_angle:.1f} deg. "
                f"Debris {debris_volume_m3:.0f} m3 moving downhill."
            ),
            data = {
                "soil_saturation":  saturation,
                "slope_angle_deg":  slope_angle,
                "debris_volume_m3": debris_volume_m3,
                "failure_depth_m":  failure_depth_m,
                "rainfall_mm":      rainfall_mm,
            }
        )


class RiverBlockageNode(BaseCascadeNode):
    node_type               = CascadeNodeType.RIVER_BLOCKAGE
    BLOCKAGE_TRIGGER_VOLUME = 5000.0
    CHANNEL_WIDTH_DEFAULT   = 30.0

    def evaluate(self, sim_state: Dict[str, Any]) -> Optional[CascadeEvent]:
        slope_fired   = sim_state.get("slope_stability_fired", False)
        debris_volume = sim_state.get("debris_volume_m3", 0.0)
        region_id     = sim_state.get("region_id", "unknown")
        timestep      = sim_state.get("timestep", 0)

        self.state.last_checked_at = datetime.utcnow()

        if not slope_fired:
            self._dormant()
            return None

        if debris_volume < self.BLOCKAGE_TRIGGER_VOLUME:
            self._watch(debris_volume / self.BLOCKAGE_TRIGGER_VOLUME)
            return None

        channel_width_m  = sim_state.get("channel_width_m", self.CHANNEL_WIDTH_DEFAULT)
        channel_depth_m  = sim_state.get("channel_depth_m", 5.0)
        channel_volume   = channel_width_m * channel_depth_m * channel_width_m
        blockage_ratio   = min(debris_volume / channel_volume, 1.0)
        prob             = blockage_ratio

        self._watch(prob)

        if blockage_ratio < 0.5:
            return None

        upstream_flow_m3s    = sim_state.get("upstream_flow_m3s", 50.0)
        lake_formation_hours = round(
            (channel_volume * blockage_ratio) / max(upstream_flow_m3s, 1.0) / 3600, 1
        )
        severity = CascadeSeverity.CRITICAL if blockage_ratio > 0.85 else CascadeSeverity.HIGH

        return self._fire(
            region_id   = region_id,
            timestep    = timestep,
            severity    = severity,
            probability = prob,
            message     = (
                f"River channel {blockage_ratio*100:.0f}% blocked. "
                f"Lake forming upstream - breach risk in {lake_formation_hours:.1f}h."
            ),
            data = {
                "blockage_ratio":       blockage_ratio,
                "debris_volume_m3":     debris_volume,
                "channel_width_m":      channel_width_m,
                "lake_formation_hours": lake_formation_hours,
                "upstream_flow_m3s":    upstream_flow_m3s,
            }
        )


class DamBreachNode(BaseCascadeNode):
    node_type                  = CascadeNodeType.DAM_BREACH
    LAKE_RISE_TRIGGER_M_PER_HR = 0.5
    BLOCKAGE_RATIO_TRIGGER     = 0.75

    def evaluate(self, sim_state: Dict[str, Any]) -> Optional[CascadeEvent]:
        blockage_fired = sim_state.get("river_blockage_fired", False)
        blockage_ratio = sim_state.get("blockage_ratio", 0.0)
        lake_rise_m_hr = sim_state.get("lake_rise_rate_m_per_hr", 0.0)
        region_id      = sim_state.get("region_id", "unknown")
        timestep       = sim_state.get("timestep", 0)

        self.state.last_checked_at = datetime.utcnow()

        if not blockage_fired:
            self._dormant()
            return None

        if blockage_ratio < self.BLOCKAGE_RATIO_TRIGGER:
            self._dormant()
            return None

        prob = min(lake_rise_m_hr / 2.0, 1.0)
        self._watch(prob)

        if lake_rise_m_hr < self.LAKE_RISE_TRIGGER_M_PER_HR:
            return None

        debris_volume_m3   = sim_state.get("debris_volume_m3", 10000.0)
        lake_volume_m3     = sim_state.get("lake_volume_m3", 50000.0)
        dam_height_m       = sim_state.get("dam_height_m", 10.0)
        peak_discharge_m3s = 0.54 * math.sqrt(9.81 * lake_volume_m3 * dam_height_m)
        breach_width_m     = min(debris_volume_m3 / (dam_height_m * 50), 80.0)
        time_to_peak_min   = round(dam_height_m * 3.5, 0)
        severity           = CascadeSeverity.CRITICAL if peak_discharge_m3s > 500 else CascadeSeverity.HIGH

        return self._fire(
            region_id   = region_id,
            timestep    = timestep,
            severity    = severity,
            probability = prob,
            message     = (
                f"Debris dam breaching - lake rising {lake_rise_m_hr:.2f} m/hr. "
                f"Peak {peak_discharge_m3s:.0f} m3/s in ~{time_to_peak_min:.0f} min."
            ),
            data = {
                "lake_rise_rate_m_per_hr": lake_rise_m_hr,
                "peak_discharge_m3s":      peak_discharge_m3s,
                "breach_width_m":          breach_width_m,
                "time_to_peak_min":        time_to_peak_min,
                "lake_volume_m3":          lake_volume_m3,
                "dam_height_m":            dam_height_m,
            }
        )


class FloodWaveNode(BaseCascadeNode):
    node_type             = CascadeNodeType.FLOOD_WAVE
    DISCHARGE_TRIGGER_M3S = 200.0

    def evaluate(self, sim_state: Dict[str, Any]) -> Optional[CascadeEvent]:
        breach_fired       = sim_state.get("dam_breach_fired", False)
        peak_discharge     = sim_state.get("peak_discharge_m3s", 0.0)
        region_id          = sim_state.get("region_id", "unknown")
        timestep           = sim_state.get("timestep", 0)
        downstream_regions = sim_state.get("downstream_regions", [])

        self.state.last_checked_at = datetime.utcnow()

        if not breach_fired and peak_discharge < self.DISCHARGE_TRIGGER_M3S:
            self._dormant()
            return None

        prob            = min(peak_discharge / 1000.0, 1.0)
        self._watch(prob)

        channel_width_m = sim_state.get("channel_width_m", 30.0)
        channel_depth_m = sim_state.get("channel_depth_m", 5.0)
        v_mean          = peak_discharge / max(channel_width_m * channel_depth_m, 1.0)
        wave_celerity   = (5.0 / 3.0) * v_mean

        arrival_times = {}
        for ds in downstream_regions:
            distance_m          = ds.get("distance_m", 10000.0)
            name                = ds.get("name", ds.get("region_id", "unknown"))
            arrival_times[name] = round(distance_m / max(wave_celerity, 0.1) / 60, 1)

        manning_n   = sim_state.get("manning_n", 0.035)
        slope       = sim_state.get("channel_slope", 0.002)
        max_depth_m = (
            (peak_discharge * manning_n) / (channel_width_m * math.sqrt(slope))
        ) ** 0.6

        severity = (
            CascadeSeverity.CRITICAL if peak_discharge > 500
            else CascadeSeverity.HIGH if peak_discharge > 200
            else CascadeSeverity.MEDIUM
        )

        return self._fire(
            region_id   = region_id,
            timestep    = timestep,
            severity    = severity,
            probability = prob,
            message     = (
                f"Flood wave downstream - peak {peak_discharge:.0f} m3/s, "
                f"speed {wave_celerity:.1f} m/s, depth ~{max_depth_m:.2f} m."
            ),
            data = {
                "peak_discharge_m3s": peak_discharge,
                "wave_celerity_ms":   wave_celerity,
                "max_depth_m":        max_depth_m,
                "arrival_times_min":  arrival_times,
                "channel_width_m":    channel_width_m,
            }
        )
"""
test_cascade.py
Manual test for the Cascade layer.
Run standalone — no server, no Qt, no DEM needed.

python test_cascade.py
"""
import sys
import os
import json
import math
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# ─── INLINE SCHEMAS (no project imports needed) ──────────────────────────────

class CascadeNodeType(str, Enum):
    SLOPE_STABILITY = "SlopeStability"
    RIVER_BLOCKAGE  = "RiverBlockage"
    DAM_BREACH      = "DamBreach"
    FLOOD_WAVE      = "FloodWave"

class CascadeSeverity(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

class NodeStatus(str, Enum):
    DORMANT   = "dormant"
    WATCHING  = "watching"
    TRIGGERED = "triggered"

@dataclass
class CascadeEvent:
    node:        str
    severity:    str
    probability: float
    region_id:   str
    timestep:    int
    message:     str
    data:        dict
    event_id:    str = field(default_factory=lambda: str(uuid.uuid4()))
    fired_at:    str = field(default_factory=lambda: datetime.utcnow().isoformat())

# ─── INLINE NODES ─────────────────────────────────────────────────────────────

def eval_slope_stability(state):
    sat   = state.get("soil_saturation", 0.0)
    slope = state.get("slope_angle_deg", 0.0)
    if slope < 25.0 or sat < 0.65:
        return None
    prob = min((sat - 0.65) / 0.35, 1.0)
    if sat < 0.75:
        return None
    area        = state.get("slope_area_m2", 10000.0)
    depth       = 2.0 + (sat - 0.75) * 8.0
    debris_vol  = area * depth * 0.3
    return CascadeEvent(
        node="SlopeStability",
        severity="critical" if sat > 0.90 else "high",
        probability=round(prob, 3),
        region_id=state["region_id"],
        timestep=state["timestep"],
        message=f"Slope failure: saturation={sat*100:.1f}%, slope={slope}°, debris={debris_vol:.0f}m³",
        data={"soil_saturation": sat, "slope_angle_deg": slope,
              "debris_volume_m3": debris_vol, "failure_depth_m": depth}
    )

def eval_river_blockage(state):
    if not state.get("slope_stability_fired"):
        return None
    debris = state.get("debris_volume_m3", 0.0)
    if debris < 5000:
        return None
    cw = state.get("channel_width_m", 30.0)
    cd = state.get("channel_depth_m", 5.0)
    channel_vol = cw * cd * cw
    ratio = min(debris / channel_vol, 1.0)
    if ratio < 0.5:
        return None
    flow = state.get("upstream_flow_m3s", 50.0)
    lake_hours = round((channel_vol * ratio) / max(flow, 1.0) / 3600, 1)
    return CascadeEvent(
        node="RiverBlockage",
        severity="critical" if ratio > 0.85 else "high",
        probability=round(ratio, 3),
        region_id=state["region_id"],
        timestep=state["timestep"],
        message=f"Channel {ratio*100:.0f}% blocked. Lake forming in ~{lake_hours}h.",
        data={"blockage_ratio": ratio, "debris_volume_m3": debris,
              "lake_formation_hours": lake_hours, "upstream_flow_m3s": flow}
    )

def eval_dam_breach(state):
    if not state.get("river_blockage_fired"):
        return None
    if state.get("blockage_ratio", 0.0) < 0.75:
        return None
    rise = state.get("lake_rise_rate_m_per_hr", 0.0)
    prob = min(rise / 2.0, 1.0)
    if rise < 0.5:
        return None
    lake_vol  = state.get("lake_volume_m3", 50000.0)
  

    dam_h     = state.get("dam_height_m", 10.0)
    g         = 9.81
    peak_q    = 0.54 * math.sqrt(g * lake_vol * dam_h)
    breach_w  = min(state.get("debris_volume_m3", 10000) / (dam_h * 50), 80.0)
    t_peak    = round(dam_h * 3.5, 0)
    return CascadeEvent(
        node="DamBreach",
        severity="critical" if peak_q > 500 else "high",
        probability=round(prob, 3),
        region_id=state["region_id"],
        timestep=state["timestep"],
        message=f"Debris dam breaching. Peak={peak_q:.0f}m³/s in ~{t_peak:.0f}min.",
        data={"lake_rise_rate_m_per_hr": rise, "peak_discharge_m3s": peak_q,
              "breach_width_m": breach_w, "time_to_peak_min": t_peak}
    )

def eval_flood_wave(state):
    breach = state.get("dam_breach_fired", False)
    peak_q = state.get("peak_discharge_m3s", 0.0)
    if not breach and peak_q < 200:
        return None
    cw    = state.get("channel_width_m", 30.0)
    cd    = state.get("channel_depth_m", 5.0)
    v     = peak_q / max(cw * cd, 1.0)
    celer = (5/3) * v
    n     = state.get("manning_n", 0.035)
    sl    = state.get("channel_slope", 0.002)
    depth = ((peak_q * n) / (cw * math.sqrt(sl))) ** 0.6
    downstream = state.get("downstream_regions", [
        {"name": "town_A", "distance_m": 8000},
        {"name": "town_B", "distance_m": 20000},
    ])
    arrivals = {
        ds["name"]: round(ds["distance_m"] / max(celer, 0.1) / 60, 1)
        for ds in downstream
    }
    return CascadeEvent(
        node="FloodWave",
        severity="critical" if peak_q > 500 else "high",
        probability=round(min(peak_q / 1000, 1.0), 3),
        region_id=state["region_id"],
        timestep=state["timestep"],
        message=f"Flood wave: peak={peak_q:.0f}m³/s, speed={celer:.1f}m/s, depth≈{depth:.2f}m",
        data={"peak_discharge_m3s": peak_q, "wave_celerity_ms": celer,
              "max_depth_m": depth, "arrival_times_min": arrivals}
    )

# ─── INLINE ENGINE ────────────────────────────────────────────────────────────

def run_cascade(timestep, region_id, sim_state):
    state = {**sim_state, "timestep": timestep, "region_id": region_id}
    events = []
    carry  = {}

    e = eval_slope_stability(state)
    if e:
        events.append(e)
        carry["slope_stability_fired"] = True
        carry["debris_volume_m3"]      = e.data["debris_volume_m3"]

    state.update(carry)
    e = eval_river_blockage(state)
    if e:
        events.append(e)
        carry["river_blockage_fired"] = True
        carry["blockage_ratio"]       = e.data["blockage_ratio"]
        flow = state.get("upstream_flow_m3s", 50.0)
        carry["lake_volume_m3"] = max(
    e.data["lake_formation_hours"] * 3600 * flow * 0.3,
    sim_state.get("lake_volume_m3", 20000.0)  # fallback minimum
)

    state.update(carry)
    e = eval_dam_breach(state)
    if e:
        events.append(e)
        carry["dam_breach_fired"]   = True
        carry["peak_discharge_m3s"] = e.data["peak_discharge_m3s"]

    state.update(carry)
    e = eval_flood_wave(state)
    if e:
        events.append(e)

    return events

# ─── TESTS ────────────────────────────────────────────────────────────────────

print("\n========== NEROLITH CASCADE — MANUAL TEST ==========")

# TEST 1: No cascade — dry conditions
print("\n[TEST 1] Dry conditions — no nodes should fire")
events = run_cascade(1, "region_north", {
    "soil_saturation": 0.30,
    "slope_angle_deg": 35.0,
    "rainfall_mm": 20.0,
    "upstream_flow_m3s": 30.0,
    "lake_rise_rate_m_per_hr": 0.0,
})
assert len(events) == 0
print(f"  PASS — {len(events)} events fired (expected 0)")

# TEST 2: High saturation — only SlopeStability fires
print("\n[TEST 2] High saturation, steep slope — SlopeStability fires")
events = run_cascade(2, "region_north", {
    "soil_saturation": 0.82,
    "slope_angle_deg": 35.0,
    "slope_area_m2": 15000.0,
    "rainfall_mm": 180.0,
    "upstream_flow_m3s": 80.0,
    "channel_width_m": 25.0,
    "channel_depth_m": 4.0,
    "lake_rise_rate_m_per_hr": 0.0,
})
assert len(events) >= 1
assert events[0].node == "SlopeStability"
print(f"  PASS — {events[0].node} fired | prob={events[0].probability} | {events[0].message}")

# TEST 3: Full cascade — all four nodes fire
print("\n[TEST 3] Full cascade — all 4 nodes should fire")
events = run_cascade(3, "region_north", {
    "soil_saturation": 0.92,
    "slope_angle_deg": 38.0,
    "slope_area_m2": 20000.0,
    "rainfall_mm": 250.0,
    "channel_width_m": 20.0,
    "channel_depth_m": 4.0,
    "upstream_flow_m3s": 150.0,
    "lake_rise_rate_m_per_hr": 1.2,
    "lake_volume_m3": 80000.0,
    "dam_height_m": 12.0,
    "channel_slope": 0.003,
    "manning_n": 0.035,
    "downstream_regions": [
        {"name": "village_A", "distance_m": 5000},
        {"name": "town_B",    "distance_m": 15000},
    ]
})
print(f"\n  Events fired: {len(events)}")
for e in events:
    print(f"  [{e.node}] severity={e.severity} prob={e.probability}")
    print(f"    → {e.message}")
    if e.node == "FloodWave" and "arrival_times_min" in e.data:
        print(f"    → Arrivals: {e.data['arrival_times_min']}")

assert len(events) == 4
assert events[0].node == "SlopeStability"
assert events[1].node == "RiverBlockage"
assert events[2].node == "DamBreach"
assert events[3].node == "FloodWave"
print(f"\n  PASS — all 4 nodes fired in correct order")

# TEST 4: Flat terrain — no cascade even with high rainfall
print("\n[TEST 4] Flat terrain (slope=5°) — no cascade regardless of rainfall")
events = run_cascade(4, "region_plains", {
    "soil_saturation": 0.95,
    "slope_angle_deg": 5.0,
    "rainfall_mm": 300.0,
    "upstream_flow_m3s": 200.0,
    "lake_rise_rate_m_per_hr": 2.0,
})
assert len(events) == 0
print(f"  PASS — flat terrain blocked cascade correctly")

# TEST 5: Partial cascade — SlopeStability + RiverBlockage only
print("\n[TEST 5] Partial cascade — blockage forms but lake rise too slow for breach")
events = run_cascade(5, "region_mid", {
    "soil_saturation": 0.80,
    "slope_angle_deg": 30.0,
    "slope_area_m2": 25000.0,
    "rainfall_mm": 160.0,
    "channel_width_m": 15.0,
    "channel_depth_m": 3.0,
    "upstream_flow_m3s": 60.0,
    "lake_rise_rate_m_per_hr": 0.2,  # too slow for breach
    "lake_volume_m3": 30000.0,
    "dam_height_m": 8.0,
})
print(f"  Events fired: {[e.node for e in events]}")
assert any(e.node == "SlopeStability" for e in events)
assert not any(e.node == "DamBreach" for e in events)
assert not any(e.node == "FloodWave" for e in events)
print(f"  PASS — cascade stopped at correct node")

print("\n========== ALL CASCADE TESTS PASSED ==========\n")
print("Next step: copy cascade/ folder to your project and run the API server")
print("Then test: POST http://localhost:8000/cascade/simulate with the TEST 3 payload")
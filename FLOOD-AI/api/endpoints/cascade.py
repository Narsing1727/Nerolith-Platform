"""
api/endpoints/cascade.py
Cascade events API — Qt polls these endpoints every 2 seconds.
No WebSocket needed. Simple GET with since_event_id param.
"""
from fastapi import APIRouter, Query
from typing import Optional, List
from cascade.cascade_store import cascade_store
from cascade.cascade_agent import cascade_agent
from cascade.cascade_schemas import CascadeEvent, CascadeStatus

router = APIRouter(prefix="/cascade", tags=["cascade"])


@router.get("/events")
def get_events(
    since: Optional[str] = Query(
        None,
        description="Last event_id Qt received. Returns only newer events."
    )
):
    """
    Qt calls this every 2 seconds.
    Pass since=<last_event_id> to get only new events.
    First call: omit since to get all events.

    Qt usage:
        QString url = "http://localhost:8000/cascade/events";
        if (!lastEventId.isEmpty())
            url += "?since=" + lastEventId;
        netManager->get(QNetworkRequest(QUrl(url)));
    """
    events = cascade_store.get_events_since(since)

    return {
        "events": [e.dict() for e in events],
        "count":  len(events),
        "total":  cascade_store.total_events(),
    }


@router.get("/status")
def get_status(timestep: int = Query(0)):
    """
    Full cascade engine status — node states, event count, active flag.
    Qt can call this once on load to initialize the timeline panel.
    """
    status = cascade_agent.get_status(timestep)
    return status.dict()


@router.get("/events/all")
def get_all_events():
    """
    Returns complete event history for current run.
    Used by Qt to rebuild timeline panel after reconnect.
    """
    events = cascade_store.get_all_events()
    return {
        "events": [e.dict() for e in events],
        "count":  len(events),
    }


@router.post("/reset")
def reset_cascade():
    """
    Reset cascade state. Call when starting a new simulation run.
    """
    cascade_agent.reset()
    return {"status": "reset", "message": "Cascade engine reset"}


@router.post("/simulate")
def simulate_cascade(payload: dict):
    """
    Manual trigger for testing — inject sim_state directly.
    Used for testing without running full simulation.

    Body:
    {
        "timestep": 5,
        "region_id": "region_north",
        "soil_saturation": 0.82,
        "slope_angle_deg": 35.0,
        "slope_area_m2": 15000,
        "rainfall_mm": 180,
        "channel_width_m": 25,
        "channel_depth_m": 4,
        "upstream_flow_m3s": 120,
        "lake_rise_rate_m_per_hr": 0.8,
        "channel_slope": 0.003,
        "manning_n": 0.035
    }
    """
    from cascade.cascade_engine import cascade_engine
    from core.schemas import RiskLevel

    timestep  = payload.pop("timestep", 0)
    region_id = payload.pop("region_id", "test_region")

    # Make sure engine is initialized
    if not cascade_agent._initialized:
        cascade_agent.init("manual_test_run")

    # Run directly through cascade engine
    fired = cascade_engine.evaluate(timestep, region_id, payload)

    return {
        "fired_count": len(fired),
        "events": [e.dict() for e in fired],
    }
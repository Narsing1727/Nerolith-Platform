from fastapi import APIRouter, HTTPException
from agents.agent_runner import agent_runner
from core.region_registry import registry

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/")
def list_agents():
    return [
        {
            "region_id": r.region_id,
            "name": r.name,
            "active": agent_runner.get_agent(r.region_id).is_active()
            if agent_runner.get_agent(r.region_id) else False
        }
        for r in registry.all()
    ]


@router.get("/{region_id}")
def get_agent(region_id: str):
    agent = agent_runner.get_agent(region_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    memory = agent.memory
    return {
        "region_id": region_id,
        "active": agent.is_active(),
        "peak_risk": memory.peak_risk(),
        "flood_trend": memory.flood_trend(),
        "long_term_events": memory.long_term_events(),
        "recent_observations": [o.dict() for o in memory.recent(5)]
    }


@router.get("/{region_id}/risk")
def get_agent_risk(region_id: str):
    agent = agent_runner.get_agent(region_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    recent = agent.memory.recent(1)
    if not recent:
        return {"region_id": region_id, "risk_level": "none", "timestep": None}

    latest = recent[-1]
    return {
        "region_id": region_id,
        "risk_level": latest.risk_level,
        "timestep": latest.timestep,
        "flood_max_m": latest.flood_stats.get("max", 0),
        "flood_mean_m": latest.flood_stats.get("mean", 0),
        "anomalies": latest.anomalies
    }
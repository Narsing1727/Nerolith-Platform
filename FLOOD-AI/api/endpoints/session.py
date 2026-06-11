"""
Session endpoints.
POST /session/start  â€” start a new simulation session
POST /session/stop   â€” stop the current session
GET  /session/status â€” get current session state
"""
from fastapi import APIRouter, HTTPException
from core.session import session
from core.region_registry import registry
from agents.agent_runner import agent_runner
from agents.alert_agent import alert_agent
from agents.report_agent import report_agent
from services.snapshot_store import snapshot_store
from engine_bridge.dll_reader import dll_reader
from engine_bridge.timestep_listener import wire

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/start")
def start_session():
    if session.is_active():
        raise HTTPException(status_code=400, detail="Session already active.")

    run = session.start()
    session.set_region_count(registry.count())
    agent_runner.build_agents()
    snapshot_store.set_run(run.run_id)

    connected = dll_reader.connect()
    if connected:
        wire()
        dll_reader.start_listening()

    return {"run_id": run.run_id, "engine_connected": connected}


@router.post("/stop")
def stop_session():
    if not session.is_active():
        raise HTTPException(status_code=400, detail="No active session.")

    session.stop()
    dll_reader.stop()
    agent_runner.reset()
    alert_agent.clear()
    snapshot_store.clear()
    registry.clear()

    run = session.get_run()
    return {"run_id": run.run_id, "total_timesteps": run.total_timesteps}

@router.get("/status")
def get_status():
    run = session.get_run()
    return {
        "active": session.is_active(),
        "timestep": session.current_timestep(),
        "run_id": run.run_id if run else None,
        "region_count": registry.count(),
        "agent_count": agent_runner.agent_count(),
        "active_alerts": len(alert_agent.active_alerts())
    }
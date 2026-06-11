from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints.session import router as session_router
from api.endpoints.agents import router as agents_router
from api.endpoints.alerts import router as alerts_router
from api.endpoints.report import router as report_router
from api.endpoints.surrogate import router as surrogate_router
from api.websocket import manager
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from api.endpoints.cascade import router as cascade_router
from cascade.cascade_engine import CascadeEngine
from datetime import datetime


router = APIRouter()


class FloodSnapIn(BaseModel):
    timestep: int
    rows: int
    cols: int
    cell_size_m: float
    data: List[List[float]]
    max_depth_m: float
    flooded_cell_count: int


class TickIn(BaseModel):
    timestep: int
    elapsed_seconds: float
    rainfall_mm: float
    flood: FloodSnapIn


def create_app() -> FastAPI:
    app = FastAPI(
        title="FLOOD-AI",
        description="Intelligent agent layer for flood simulation",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.include_router(session_router)
    app.include_router(agents_router)
    app.include_router(alerts_router)
    app.include_router(report_router)
    app.include_router(surrogate_router)
    app.include_router(router)
    app.include_router(cascade_router)

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await manager.connect(ws)
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(ws)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


@router.post("/ingest/tick")
def ingest_tick(payload: TickIn):
    from engine_bridge.engine_schema import (
        FloodGridSnapshot, FlowGridSnapshot,
        RainfallGridSnapshot, EngineTickPayload
    )
    from engine_bridge.timestep_listener import _on_engine_tick
    from core.session import session
    from core.region_registry import registry
    from agents.agent_runner import agent_runner
    from services.snapshot_store import snapshot_store
    from services.alert_router import setup_default_channels
    from core.run_manager import init_run
    from services.region_clusterer import cluster_uniform_grid
    from agents.coordinator_agent import coordinator
    import numpy as np

    if not session.is_active():
        rows = payload.flood.rows
        cols = payload.flood.cols
        registry.clear()
        n_splits = 6
        regions = cluster_uniform_grid(rows, cols, n_splits, n_splits)
        for region in regions:
            registry.register(region)
        run = session.start()
        session.set_region_count(registry.count())
        snapshot_store.set_run(run.run_id)
        setup_default_channels(run.run_id)
        init_run(run.run_id, registry.count())
        agent_runner.build_agents()

    rows      = payload.flood.rows
    cols      = payload.flood.cols
    cell_size = payload.flood.cell_size_m
    zero_grid = [[0.0] * cols for _ in range(rows)]

    dem_array = np.array(payload.flood.data, dtype=np.float64)
    coordinator.set_dem(dem_array)

    tick = EngineTickPayload(
        timestep=payload.timestep,
        elapsed_seconds=payload.elapsed_seconds,
        flood=FloodGridSnapshot(
            timestep=payload.timestep,
            rows=rows, cols=cols,
            cell_size_m=cell_size,
            data=payload.flood.data,
            max_depth_m=payload.flood.max_depth_m,
            flooded_cell_count=payload.flood.flooded_cell_count
        ),
        flow=FlowGridSnapshot(
            timestep=payload.timestep,
            rows=rows, cols=cols,
            cell_size_m=cell_size,
            data=zero_grid,
            max_velocity_ms=0.0
        ),
        rainfall=RainfallGridSnapshot(
            timestep=payload.timestep,
            rows=rows, cols=cols,
            cell_size_m=cell_size,
            data=[[payload.rainfall_mm] * cols for _ in range(rows)],
            total_rainfall_mm=payload.rainfall_mm * rows * cols
        )
    )

    _on_engine_tick(tick)
    return {"status": "ok", "timestep": payload.timestep}


@router.get("/ingest/latest")
def get_latest_risks():
    from services.snapshot_store import snapshot_store
    latest = snapshot_store.latest()
    if not latest:
        return {"region_risks": {}}
    return {"region_risks": latest.get("region_risks", {})}


@router.post("/cascade/analyze")
def cascade_analyze(payload: dict):
    engine    = CascadeEngine()
    sim_state = payload.get("sim_state", {})
    region_id = payload.get("region_id", "unknown")
    timestep  = payload.get("timestep", 0)
    events    = engine.evaluate(timestep, region_id, sim_state)
    return {
        "region_id":         region_id,
        "timestep":          timestep,
        "generated_at":      datetime.utcnow().isoformat(),
        "nodes_fired":       len(events),
        "simulation_params": sim_state,
        "events":            [e.dict() for e in events]
    }
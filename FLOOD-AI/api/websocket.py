"""
WebSocket endpoint for real-time push to Qt frontend.
Streams: timestep ticks, new alerts, agent state updates.
Qt client connects once and receives a stream of JSON events.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
from agents.coordinator_agent import coordinator
from agents.alert_agent import alert_agent
from core.schemas import AlertEvent
import asyncio
import json
from loguru import logger


class ConnectionManager:
    def __init__(self):
        self._connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)
        logger.info(f"WebSocket client connected. Total: {len(self._connections)}")

    def disconnect(self, ws: WebSocket):
        self._connections.remove(ws)
        logger.info(f"WebSocket client disconnected. Total: {len(self._connections)}")

    async def broadcast(self, message: dict):
        dead = []
        for ws in self._connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)

    def connection_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


async def push_tick_update(timestep: int):
    decision = coordinator.last_decision()
    if not decision:
        return

    await manager.broadcast({
        "type": "tick",
        "timestep": timestep,
        "global_risk": decision.global_risk,
        "region_risks": decision.region_risks,
        "alerts": [a.dict() for a in decision.alerts_issued]
    })


async def push_alert(alert: AlertEvent):
    await manager.broadcast({
        "type": "alert",
        "alert": alert.dict()
    })
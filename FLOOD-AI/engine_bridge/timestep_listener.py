"""
Listens for timestep tick events from the engine.
On each tick, triggers agent observation cycle.
"""
from engine_bridge.dll_reader import dll_reader
from engine_bridge.engine_schema import EngineTickPayload
from agents.agent_runner import agent_runner
from core.session import session
from loguru import logger


def _on_engine_tick(payload: EngineTickPayload):
    if not session.is_active():
        return
    session.tick()
    try:
        decision = agent_runner.run_cycle(payload)
        logger.debug(
            f"Timestep {payload.timestep} | global_risk={decision.global_risk} | alerts={len(decision.alerts_issued)}"
        )
    except Exception as e:
        logger.error(f"Agent cycle failed at timestep {payload.timestep}: {e}")


def wire():
    dll_reader.on_tick(_on_engine_tick)
    logger.info("Timestep listener wired to engine tick events.")
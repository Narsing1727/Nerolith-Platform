"""
Routes alert events to registered output channels.
Channels: Qt frontend (via WebSocket), REST API, log file.
"""
import os
import json
from typing import Callable, List
from core.schemas import AlertEvent
from config import settings
from loguru import logger


_channels: List[Callable[[AlertEvent], None]] = []


def register(fn: Callable[[AlertEvent], None]):
    _channels.append(fn)


def route(alert: AlertEvent):
    for channel in _channels:
        try:
            channel(alert)
        except Exception as e:
            logger.error(f"Alert channel error: {e}")


def log_channel(alert: AlertEvent):
    logger.info(f"[{alert.severity.upper()}] {alert.region_id}: {alert.message}")


def file_channel(run_id: str) -> Callable[[AlertEvent], None]:
    def _write(alert: AlertEvent):
        path = os.path.join(settings.output_dir, "runs", run_id, "alerts", "alerts.jsonl")
        with open(path, "a") as f:
            f.write(json.dumps(alert.dict(), default=str) + "\n")
    return _write


def setup_default_channels(run_id: str):
    _channels.clear()
    register(log_channel)
    register(file_channel(run_id))
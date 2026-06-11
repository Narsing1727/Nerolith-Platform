"""
Reads real-time simulation output from FLOOD-ENGINE.
Connects to the engine via socket/pipe or shared memory.
Exposes: get_flood_grid(), get_flow_grid(), get_rainfall_grid()
"""
import socket
import json
import threading
from typing import Optional, Callable
from engine_bridge.engine_schema import EngineTickPayload
from config import settings
from loguru import logger


class DllReader:
    def __init__(self):
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._on_tick: Optional[Callable[[EngineTickPayload], None]] = None

    def on_tick(self, fn: Callable[[EngineTickPayload], None]):
        self._on_tick = fn

    def connect(self) -> bool:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((settings.flood_engine_host, settings.flood_engine_port))
            self._sock.settimeout(5.0)
            logger.info(f"Connected to FloodEngine at {settings.flood_engine_host}:{settings.flood_engine_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to FloodEngine: {e}")
            return False

    def start_listening(self):
        if not self._sock:
            raise RuntimeError("Not connected. Call connect() first.")
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def _listen_loop(self):
        buffer = ""
        while self._running:
            try:
                chunk = self._sock.recv(65536).decode("utf-8")
                if not chunk:
                    logger.warning("Engine connection closed.")
                    break
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self._process_message(line.strip())
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"DllReader listen error: {e}")
                break

    def _process_message(self, raw: str):
        if not raw:
            return
        try:
            data = json.loads(raw)
            payload = EngineTickPayload(**data)
            if self._on_tick:
                self._on_tick(payload)
        except Exception as e:
            logger.error(f"Failed to parse engine message: {e} | raw: {raw[:200]}")

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=3.0)


dll_reader = DllReader()
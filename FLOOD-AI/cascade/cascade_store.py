"""
cascade_store.py
In-memory event queue for cascade events.
Qt polls GET /cascade/events?since=<last_id> every 2 seconds.
Thread-safe. Events persist for duration of simulation run.
"""
from typing import List, Optional
from datetime import datetime
from threading import Lock
from cascade.cascade_schemas import CascadeEvent, NodeState, CascadeNodeType
from loguru import logger


class CascadeStore:
    def __init__(self):
        self._events: List[CascadeEvent] = []
        self._node_states: dict = {}
        self._lock = Lock()
        self._run_id: Optional[str] = None

    def set_run(self, run_id: str):
        with self._lock:
            self._run_id = run_id
            self._events.clear()
            self._node_states.clear()
            logger.info(f"CascadeStore reset for run: {run_id}")

    def push(self, event: CascadeEvent):
        """Called by CascadeEngine when a node fires."""
        with self._lock:
            self._events.append(event)
            logger.info(
                f"CascadeStore: pushed {event.node} | "
                f"severity={event.severity} | "
                f"total_events={len(self._events)}"
            )

    def update_node_state(self, node_type: CascadeNodeType, state: NodeState):
        """Called every timestep by CascadeEngine."""
        with self._lock:
            self._node_states[node_type.value] = state

    def get_events_since(self, since_event_id: Optional[str] = None) -> List[CascadeEvent]:
        """
        Returns all events after since_event_id.
        If since_event_id is None, returns all events.
        Qt sends its last received event_id each poll.
        """
        with self._lock:
            if not since_event_id:
                return list(self._events)

            # Find index of since_event_id
            idx = None
            for i, e in enumerate(self._events):
                if e.event_id == since_event_id:
                    idx = i
                    break

            if idx is None:
                # ID not found — return everything (client may have missed events)
                return list(self._events)

            return list(self._events[idx + 1:])

    def get_all_events(self) -> List[CascadeEvent]:
        with self._lock:
            return list(self._events)

    def get_node_states(self) -> dict:
        with self._lock:
            return dict(self._node_states)

    def total_events(self) -> int:
        with self._lock:
            return len(self._events)

    def last_event_at(self) -> Optional[datetime]:
        with self._lock:
            if not self._events:
                return None
            return self._events[-1].fired_at

    def cascade_active(self) -> bool:
        """True if any node has fired in this run."""
        with self._lock:
            return len(self._events) > 0

    def clear(self):
        with self._lock:
            self._events.clear()
            self._node_states.clear()


# Singleton — imported everywhere
cascade_store = CascadeStore()
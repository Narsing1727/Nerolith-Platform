"""
AlertAgent: handles real-time alert dispatch.
- Receives trigger events from CoordinatorAgent
- Routes alerts to appropriate output channels (Qt UI, log, API)
- Manages alert cooldown to avoid spam
- Severity levels: INFO, WARNING, CRITICAL, EMERGENCY
"""
from typing import List, Dict, Callable
from core.schemas import AlertEvent, AlertSeverity
from datetime import datetime, timedelta
from loguru import logger


COOLDOWN_SECONDS: Dict[AlertSeverity, int] = {
    AlertSeverity.INFO: 60,
    AlertSeverity.WARNING: 30,
    AlertSeverity.CRITICAL: 10,
    AlertSeverity.EMERGENCY: 0
}


class AlertAgent:
    def __init__(self):
        self._history: List[AlertEvent] = []
        self._last_fired: Dict[str, datetime] = {}
        self._channels: List[Callable[[AlertEvent], None]] = []

    def register_channel(self, fn: Callable[[AlertEvent], None]):
        self._channels.append(fn)

    def dispatch(self, alerts: List[AlertEvent]):
        for alert in alerts:
            if self._is_cooling_down(alert):
                continue
            self._history.append(alert)
            self._last_fired[alert.region_id] = datetime.utcnow()
            for channel in self._channels:
                try:
                    channel(alert)
                except Exception as e:
                    logger.error(f"Alert channel failed: {e}")
            logger.info(f"[ALERT][{alert.severity}] {alert.region_id}: {alert.message}")

    def _is_cooling_down(self, alert: AlertEvent) -> bool:
        last = self._last_fired.get(alert.region_id)
        if not last:
            return False
        cooldown = COOLDOWN_SECONDS.get(alert.severity, 30)
        return datetime.utcnow() - last < timedelta(seconds=cooldown)

    def active_alerts(self) -> List[AlertEvent]:
        return [a for a in self._history if not a.acknowledged]

    def history(self) -> List[AlertEvent]:
        return self._history

    def acknowledge(self, alert_id: str) -> bool:
        for alert in self._history:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def clear(self):
        self._history.clear()
        self._last_fired.clear()


alert_agent = AlertAgent()
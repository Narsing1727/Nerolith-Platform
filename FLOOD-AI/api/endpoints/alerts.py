"""
Alert endpoints.
GET  /alerts/active    â€” get all currently active alerts
GET  /alerts/history   â€” get alert history for current run
POST /alerts/ack/{id}  â€” acknowledge an alert
"""
from fastapi import APIRouter, HTTPException
from agents.alert_agent import alert_agent

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/active")
def get_active_alerts():
    return [a.dict() for a in alert_agent.active_alerts()]


@router.get("/history")
def get_alert_history():
    return [a.dict() for a in alert_agent.history()]


@router.post("/ack/{alert_id}")
def acknowledge_alert(alert_id: str):
    success = alert_agent.acknowledge(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return {"acknowledged": True, "alert_id": alert_id}
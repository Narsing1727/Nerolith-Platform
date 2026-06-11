from fastapi import APIRouter
from monitoring.metrics import get_system_metrics

router = APIRouter()


@router.get("/health")
async def health():
    metrics = await get_system_metrics()
    all_healthy = all(
        "healthy" in str(v)
        for v in metrics["services"].values()
    )
    return {
        "status": "ok" if all_healthy else "degraded",
        **metrics
    }
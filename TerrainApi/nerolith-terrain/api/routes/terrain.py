from fastapi import APIRouter, HTTPException, Depends
from api.models.request import TerrainRequest
from api.models.response import TerrainJobResponse
from api.models.enums import JobStatus
from api.middleware.auth import verify_api_key
from api.middleware.ratelimit import check_rate_limit
from workers.tasks.terrain_job import process_terrain_small
from workers.tasks.terrain_job import process_terrain_medium
from workers.tasks.terrain_job import process_terrain_large
import uuid

router = APIRouter()

FREE_TIER_MONTHLY_LIMIT = 500
SMALL_AOI_THRESHOLD = 1.0
LARGE_AOI_THRESHOLD = 10.0


def get_aoi_area(coordinates: list[float]) -> float:
    return (coordinates[2] - coordinates[0]) * (coordinates[3] - coordinates[1])


def select_queue(area: float):
    if area <= SMALL_AOI_THRESHOLD:
        return process_terrain_small, "priority_high"
    elif area <= LARGE_AOI_THRESHOLD:
        return process_terrain_medium, "priority_normal"
    else:
        return process_terrain_large, "priority_low"


@router.post(
    "/analyze",
    response_model=TerrainJobResponse,
    dependencies=[Depends(verify_api_key), Depends(check_rate_limit)]
)
async def analyze_terrain(request: TerrainRequest):
    job_id = f"trn_{uuid.uuid4().hex[:12]}"

    bbox = request.aoi.coordinates
    area = get_aoi_area(bbox) if bbox else 1.0
    task, queue = select_queue(area)

    estimated = 15 if area <= SMALL_AOI_THRESHOLD else 45 if area <= LARGE_AOI_THRESHOLD else 120

    task.apply_async(
        args=[job_id, request.model_dump()],
        queue=queue
    )

    return TerrainJobResponse(
        job_id=job_id,
        status=JobStatus.queued,
        estimated_seconds=estimated,
        poll_url=f"https://api.nerolith.in/terrain/v1/jobs/{job_id}",
        stream_url=f"https://api.nerolith.in/terrain/v1/jobs/{job_id}/stream"
    )
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from api.models.response import JobStatusResponse
from api.models.enums import JobStatus
from api.middleware.auth import verify_api_key, sanitize_job_id
import redis
import asyncio
import json
from config.settings import settings

router = APIRouter()


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    dependencies=[Depends(verify_api_key)]
)
async def get_job_status(job_id: str):
    job_id = sanitize_job_id(job_id)
    r = redis.from_url(settings.redis_url)
    data = r.hgetall(f"job:{job_id}")
    r.close()

    if not data:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job_id,
        status=data.get(b"status", b"unknown").decode(),
        stage=data.get(b"stage", b"").decode(),
        percent=int(data.get(b"percent", b"0").decode()),
    )


@router.get(
    "/jobs/{job_id}/stream",
    dependencies=[Depends(verify_api_key)]
)
async def stream_job_status(job_id: str):
    job_id = sanitize_job_id(job_id)

    async def event_generator():
        r = redis.from_url(settings.redis_url)
        last_stage = None

        while True:
            data = r.hgetall(f"job:{job_id}")

            if not data:
                yield f"data: {json.dumps({'error': 'job not found'})}\n\n"
                break

            status = data.get(b"status", b"unknown").decode()
            stage = data.get(b"stage", b"").decode()
            percent = int(data.get(b"percent", b"0").decode())

            if stage != last_stage:
                payload = json.dumps({
                    "job_id": job_id,
                    "status": status,
                    "stage": stage,
                    "percent": percent
                })
                yield f"data: {payload}\n\n"
                last_stage = stage

            if status in ("completed", "failed"):
                r.close()
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
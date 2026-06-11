from workers.celery_app import celery
from pipeline.orchestrator import run_pipeline
import redis
from config.settings import settings


def mark_failed(job_id: str, error: str):
    r = redis.from_url(settings.redis_url)
    r.hset(f"job:{job_id}", mapping={
        "status": "failed",
        "stage": "error",
        "percent": 0,
        "error": str(error)
    })
    r.expire(f"job:{job_id}", 86400)
    r.close()


@celery.task
def process_terrain_small(job_id: str, payload: dict):
    try:
        return run_pipeline(job_id, payload)
    except Exception as e:
        mark_failed(job_id, str(e))
        raise


@celery.task
def process_terrain_medium(job_id: str, payload: dict):
    try:
        return run_pipeline(job_id, payload)
    except Exception as e:
        mark_failed(job_id, str(e))
        raise


@celery.task
def process_terrain_large(job_id: str, payload: dict):
    try:
        return run_pipeline(job_id, payload)
    except Exception as e:
        mark_failed(job_id, str(e))
        raise
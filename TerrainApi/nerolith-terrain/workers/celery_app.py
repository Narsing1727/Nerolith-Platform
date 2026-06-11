from celery import Celery
from config.settings import settings

celery = Celery(
    "nerolith_terrain",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks.terrain_job", "workers.tasks.webhook"]
)

celery.conf.task_routes = {
    "workers.tasks.terrain_job.process_terrain_small":  {"queue": "priority_high"},
    "workers.tasks.terrain_job.process_terrain_medium": {"queue": "priority_normal"},
    "workers.tasks.terrain_job.process_terrain_large":  {"queue": "priority_low"},
    "workers.tasks.webhook.send_webhook":               {"queue": "callbacks"}
}

celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.conf.accept_content = ["json"]
celery.conf.timezone = "UTC"
celery.conf.broker_connection_retry_on_startup = True
celery.conf.task_acks_late = True
celery.conf.worker_prefetch_multiplier = 1
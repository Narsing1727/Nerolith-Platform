from workers.celery_app import celery

@celery.task
def send_webhook(job_id: str, webhook_url: str, payload: dict):
    pass
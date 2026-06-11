from fastapi import Request, HTTPException
import re
from config.settings import settings


async def verify_api_key(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API key")
    token = auth.split("Bearer ")[1].strip()
    if not token or token != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token


def sanitize_job_id(job_id: str) -> str:
    if not re.match(r'^trn_[a-f0-9]{12}$', job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    return job_id
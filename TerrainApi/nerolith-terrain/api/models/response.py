from pydantic import BaseModel
from typing import Optional
from api.models.enums import JobStatus


class TerrainJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    estimated_seconds: int
    poll_url: str
    stream_url: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    stage: Optional[str] = None
    percent: Optional[int] = None
    outputs: Optional[dict] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None
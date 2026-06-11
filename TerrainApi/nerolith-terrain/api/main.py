from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api.routes import terrain, jobs, health
from db.session import init_db
import os

app = FastAPI(title="Nerolith Terrain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(terrain.router, prefix="/terrain/v1")
app.include_router(jobs.router, prefix="/terrain/v1")

@app.get("/outputs/{job_id}/{filename}")
async def download_output(job_id: str, filename: str):
    file_path = f"/mnt/nerolith_outputs/{job_id}/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

@app.on_event("startup")
async def startup():
    await init_db()
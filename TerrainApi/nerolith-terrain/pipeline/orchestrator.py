import redis
from config.settings import settings
from pipeline.stages.source_select import select_best_source
from pipeline.stages.fetch import fetch_dem
from pipeline.stages.datum_norm import normalize_datum
from pipeline.stages.void_fill import fill_voids
from pipeline.stages.wang_liu import wang_liu_fill
from pipeline.stages.flow import compute_flow
from pipeline.stages.derivatives import compute_derivatives
from pipeline.stages.streams import extract_streams
from pipeline.stages.watershed import delineate_watershed
from pipeline.stages.confidence import compute_confidence
from pipeline.stages.cog_package import package_outputs
import numpy as np


def update_progress(job_id: str, stage: str, percent: int, status: str = "processing"):
    r = redis.from_url(settings.redis_url)
    r.hset(f"job:{job_id}", mapping={
        "status": status,
        "stage": stage,
        "percent": percent
    })
    r.expire(f"job:{job_id}", 86400)
    r.close()


def run_pipeline(job_id: str, payload: dict) -> dict:
    bbox = payload["aoi"]["coordinates"]

    update_progress(job_id, "source_selection", 5)
    source = select_best_source(bbox)

    update_progress(job_id, "fetching_dem", 15)
    dem = fetch_dem(source, bbox)

    update_progress(job_id, "datum_normalization", 25)
    normalized = normalize_datum(dem)

    update_progress(job_id, "void_fill", 35)
    filled = fill_voids(normalized)
    original_nodata_mask = dem.array == dem.nodata

    update_progress(job_id, "wang_liu_conditioning", 45)
    conditioned = wang_liu_fill(filled)

    update_progress(job_id, "flow_routing", 55)
    flow = compute_flow(conditioned)

    update_progress(job_id, "terrain_derivatives", 65)
    derivatives = compute_derivatives(conditioned, flow)

    update_progress(job_id, "stream_extraction", 75)
    streams = extract_streams(conditioned, flow)

    update_progress(job_id, "watershed_delineation", 85)
    watershed = delineate_watershed(flow, streams)

    update_progress(job_id, "confidence_raster", 90)
    confidence = compute_confidence(filled, source, original_nodata_mask)

    update_progress(job_id, "packaging_outputs", 95)
    outputs = package_outputs(job_id, conditioned, flow, derivatives, streams, watershed, confidence)

    update_progress(job_id, "completed", 100, status="completed")

    return {
        "output_paths": outputs.output_paths,
        "metadata": outputs.metadata
    }
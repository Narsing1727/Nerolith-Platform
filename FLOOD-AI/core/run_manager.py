"""
Manages simulation run lifecycle: start, pause, resume, stop.
Stores run artifacts (snapshots, decisions, reports) per run ID.
"""
import os
import json
from datetime import datetime, timezone
from typing import List, Optional

from config import settings
from loguru import logger


_SUBDIRS = ["snapshots", "memory", "report", "alerts", "graph", "logs"]


def init_run(run_id: str, region_count: int):
    base = _run_path(run_id)
    for sub in _SUBDIRS:
        os.makedirs(os.path.join(base, sub), exist_ok=True)

    manifest = {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ended_at": None,
        "region_count": region_count,
        "total_timesteps": 0
    }
    _write_manifest(run_id, manifest)
    logger.info(f"Run initialized: {run_id}")


def finalize_run(run_id: str, total_timesteps: int):
    manifest = read_manifest(run_id)
    if not manifest:
        return
    manifest["ended_at"] = datetime.now(timezone.utc).isoformat()
    manifest["total_timesteps"] = total_timesteps
    _write_manifest(run_id, manifest)
    logger.info(f"Run finalized: {run_id} | timesteps={total_timesteps}")


def read_manifest(run_id: str) -> Optional[dict]:
    path = os.path.join(_run_path(run_id), "manifest.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def list_runs() -> List[dict]:
    runs_dir = os.path.join(settings.output_dir, "runs")
    if not os.path.exists(runs_dir):
        return []
    results = []
    for entry in sorted(os.listdir(runs_dir), reverse=True):
        manifest = read_manifest(entry)
        if manifest:
            results.append(manifest)
    return results


def _run_path(run_id: str) -> str:
    return os.path.join(settings.output_dir, "runs", run_id)


def _write_manifest(run_id: str, manifest: dict):
    path = os.path.join(_run_path(run_id), "manifest.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)




def finalize_run_with_genome(
    run_id: str,
    total_timesteps: int,
    watershed_id: str,
    rainfall_mm: float,
    max_flood_depth: float,
    low_cells: int,
    medium_cells: int,
    high_cells: int,
):
    """
    Extended finalize — calls standard finalize then updates genome.
    Use this instead of finalize_run() when full sim data is available.
    """
    finalize_run(run_id, total_timesteps)

    from agents.genome_agent import GenomeAgent
    agent = GenomeAgent(watershed_id)
    genome = agent.ingest_run(
        run_id=run_id,
        rainfall_mm=rainfall_mm,
        max_flood_depth=max_flood_depth,
        low_cells=low_cells,
        medium_cells=medium_cells,
        high_cells=high_cells,
    )
    logger.info(
        f"Genome updated post-run | "
        f"watershed={watershed_id} | "
        f"confidence={genome.confidence_score:.2f}"
    )
    return genome
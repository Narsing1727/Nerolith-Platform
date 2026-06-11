"""
Persists and loads FloodGenome objects per watershed.
One genome file per watershed_id — accumulates across all runs.
"""
import json
import os
from dataclasses import asdict
from typing import Optional

from config import settings
from graph.genome_schema import FloodGenome, FloodEvent
from loguru import logger


def _genome_path(watershed_id: str) -> str:
    genome_dir = os.path.join(settings.data_dir, "genomes")
    os.makedirs(genome_dir, exist_ok=True)
    return os.path.join(genome_dir, f"{watershed_id}.json")


def load_genome(watershed_id: str) -> FloodGenome:
    """Load existing genome or create a fresh one."""
    path = _genome_path(watershed_id)
    if not os.path.exists(path):
        logger.info(f"Genome not found for {watershed_id}, creating new")
        return FloodGenome(watershed_id=watershed_id)

    with open(path) as f:
        raw = json.load(f)

    # Rebuild events list as FloodEvent objects
    events = [FloodEvent(**e) for e in raw.pop("events", [])]
    genome = FloodGenome(**raw)
    genome.events = events
    return genome


def save_genome(genome: FloodGenome):
    path = _genome_path(genome.watershed_id)
    with open(path, "w") as f:
        json.dump(asdict(genome), f, indent=2)
    logger.info(
        f"Genome saved: {genome.watershed_id} | "
        f"events={genome.event_count} | "
        f"confidence={genome.confidence_score:.2f}"
    )


def list_genomes() -> list[dict]:
    """Return summary of all known watershed genomes."""
    genome_dir = os.path.join(settings.data_dir, "genomes")
    if not os.path.exists(genome_dir):
        return []
    results = []
    for fname in os.listdir(genome_dir):
        if fname.endswith(".json"):
            watershed_id = fname[:-5]
            g = load_genome(watershed_id)
            results.append({
                "watershed_id": g.watershed_id,
                "event_count": g.event_count,
                "confidence_score": g.confidence_score,
                "avg_rainfall_at_flood": g.avg_rainfall_at_flood,
                "updated_at": g.updated_at
            })
    return results
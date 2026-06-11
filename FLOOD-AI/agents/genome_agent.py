"""
GenomeAgent: learns from completed simulation runs and updates
the watershed FloodGenome. Called after every run finalization.
"""
from datetime import datetime, timezone
from loguru import logger

from graph.genome_schema import FloodGenome, FloodEvent
from graph.genome_store import load_genome, save_genome


class GenomeAgent:
    """
    Reads run output and updates the watershed genome.
    Recalculates learned thresholds and confidence score.
    """

    def __init__(self, watershed_id: str):
        self.watershed_id = watershed_id

    def ingest_run(
        self,
        run_id: str,
        rainfall_mm: float,
        max_flood_depth: float,
        low_cells: int,
        medium_cells: int,
        high_cells: int,
    ):
        genome = load_genome(self.watershed_id)

        total_cells = low_cells + medium_cells + high_cells
        high_ratio = high_cells / total_cells if total_cells > 0 else 0.0

        event = FloodEvent(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            rainfall_mm=rainfall_mm,
            max_flood_depth=max_flood_depth,
            low_cells=low_cells,
            medium_cells=medium_cells,
            high_cells=high_cells,
            high_ratio=high_ratio,
        )

        genome.events.append(event)
        genome.event_count = len(genome.events)
        genome.updated_at = datetime.now(timezone.utc).isoformat()

        self._recalculate_thresholds(genome)
        save_genome(genome)

        logger.info(
            f"GenomeAgent ingested run {run_id} for "
            f"watershed {self.watershed_id} | "
            f"confidence={genome.confidence_score:.2f}"
        )
        return genome

    def apply_satellite_validation(
        self,
        run_id: str,
        divergence_pct: float,
        corrected_manning_n: Optional[float] = None,
        corrected_blend_alpha: Optional[float] = None,
    ):
        """
        Called by satellite loop after recalibration.
        Marks the event as validated and improves calibration params.
        """
        from typing import Optional  # local to avoid circular
        genome = load_genome(self.watershed_id)

        for event in genome.events:
            if event.run_id == run_id:
                event.validated = True
                event.satellite_divergence = divergence_pct
                genome.validated_event_count += 1
                break

        # Update calibration params if satellite loop corrected them
        if corrected_manning_n is not None:
            # Exponential moving average — new validated value weighted 30%
            genome.best_manning_n = (
                0.7 * genome.best_manning_n + 0.3 * corrected_manning_n
            )

        if corrected_blend_alpha is not None:
            genome.best_blend_alpha = (
                0.7 * genome.best_blend_alpha + 0.3 * corrected_blend_alpha
            )

        self._recalculate_thresholds(genome)
        save_genome(genome)

        logger.info(
            f"Genome validated for run {run_id} | "
            f"divergence={divergence_pct:.1f}% | "
            f"manning_n={genome.best_manning_n:.4f}"
        )
        return genome

    def get_recommended_params(self) -> dict:
        """
        Returns the best known simulation params for this watershed.
        Called by run_manager before starting a new simulation.
        """
        genome = load_genome(self.watershed_id)
        return {
            "manning_n": genome.best_manning_n,
            "blend_alpha": genome.best_blend_alpha,
            "expected_high_ratio": genome.typical_high_ratio,
            "flood_threshold_rainfall": genome.avg_rainfall_at_flood,
            "confidence": genome.confidence_score,
        }

    # ------------------------------------------------------------------ #
    def _recalculate_thresholds(self, genome: FloodGenome):
        events = genome.events
        if not events:
            return

        # Rolling averages across all events
        genome.avg_rainfall_at_flood = sum(
            e.rainfall_mm for e in events
        ) / len(events)

        genome.avg_response_depth = sum(
            e.max_flood_depth for e in events
        ) / len(events)

        genome.typical_high_ratio = sum(
            e.high_ratio for e in events
        ) / len(events)

        # Confidence: grows with event count, boosted by validations
        # Asymptotes toward 1.0
        base = min(genome.event_count / 20.0, 0.7)
        validation_boost = min(genome.validated_event_count / 10.0, 0.3)
        genome.confidence_score = round(base + validation_boost, 3)
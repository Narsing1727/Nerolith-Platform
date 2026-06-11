"""
Manual test for FloodGenome layer.
Run this standalone before connecting Qt.
No server, no DEM, no dependencies needed.
"""
import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime, timezone

# ─── SCHEMA ──────────────────────────────────────────────────────────────────

@dataclass
class FloodEvent:
    run_id: str
    timestamp: str
    rainfall_mm: float
    max_flood_depth: float
    low_cells: int
    medium_cells: int
    high_cells: int
    high_ratio: float
    validated: bool = False
    satellite_divergence: Optional[float] = None

@dataclass
class FloodGenome:
    watershed_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    avg_rainfall_at_flood: float = 0.0
    avg_response_depth: float = 0.0
    typical_high_ratio: float = 0.0
    best_manning_n: float = 0.035
    best_blend_alpha: float = 0.7
    event_count: int = 0
    validated_event_count: int = 0
    confidence_score: float = 0.0
    events: List[FloodEvent] = field(default_factory=list)

# ─── STORE ───────────────────────────────────────────────────────────────────

GENOME_DIR = os.path.join(os.path.expanduser("~"), "nerolith_genomes_test")
os.makedirs(GENOME_DIR, exist_ok=True)

def genome_path(watershed_id):
    return os.path.join(GENOME_DIR, f"{watershed_id}.json")

def save_genome(genome):
    with open(genome_path(genome.watershed_id), "w") as f:
        json.dump(asdict(genome), f, indent=2)

def load_genome(watershed_id):
    path = genome_path(watershed_id)
    if not os.path.exists(path):
        return FloodGenome(watershed_id=watershed_id)
    with open(path) as f:
        raw = json.load(f)
    events = [FloodEvent(**e) for e in raw.pop("events", [])]
    g = FloodGenome(**raw)
    g.events = events
    return g

# ─── AGENT LOGIC ─────────────────────────────────────────────────────────────

def recalculate(genome):
    events = genome.events
    if not events:
        return
    genome.avg_rainfall_at_flood = sum(e.rainfall_mm for e in events) / len(events)
    genome.avg_response_depth    = sum(e.max_flood_depth for e in events) / len(events)
    genome.typical_high_ratio    = sum(e.high_ratio for e in events) / len(events)
    base             = min(genome.event_count / 20.0, 0.7)
    validation_boost = min(genome.validated_event_count / 10.0, 0.3)
    genome.confidence_score = round(base + validation_boost, 3)

def ingest_run(watershed_id, run_id, rainfall_mm, max_flood_depth,
               low_cells, medium_cells, high_cells):
    genome = load_genome(watershed_id)
    total = low_cells + medium_cells + high_cells
    high_ratio = high_cells / total if total > 0 else 0.0
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
    recalculate(genome)
    save_genome(genome)
    return genome

def validate_event(watershed_id, run_id, divergence_pct,
                   corrected_manning_n=None, corrected_blend_alpha=None):
    genome = load_genome(watershed_id)
    for event in genome.events:
        if event.run_id == run_id:
            event.validated = True
            event.satellite_divergence = divergence_pct
            genome.validated_event_count += 1
            break
    if corrected_manning_n is not None:
        genome.best_manning_n = round(0.7 * genome.best_manning_n + 0.3 * corrected_manning_n, 5)
    if corrected_blend_alpha is not None:
        genome.best_blend_alpha = round(0.7 * genome.best_blend_alpha + 0.3 * corrected_blend_alpha, 4)
    recalculate(genome)
    save_genome(genome)
    return genome

def print_genome(genome):
    print(f"\n{'─'*50}")
    print(f"  WATERSHED : {genome.watershed_id}")
    print(f"  events    : {genome.event_count}  |  validated: {genome.validated_event_count}")
    print(f"  confidence: {genome.confidence_score:.3f}")
    print(f"  avg_rain  : {genome.avg_rainfall_at_flood:.1f} mm")
    print(f"  avg_depth : {genome.avg_response_depth:.4f} m")
    print(f"  high_ratio: {genome.typical_high_ratio:.3f}")
    print(f"  manning_n : {genome.best_manning_n:.5f}")
    print(f"  blend_α   : {genome.best_blend_alpha:.4f}")
    print(f"{'─'*50}")

# ─── TESTS ───────────────────────────────────────────────────────────────────

WID = "roorkee_upper_ganga"

# Clean slate — delete old test file if exists
if os.path.exists(genome_path(WID)):
    os.remove(genome_path(WID))

print("\n========== NEROLITH GENOME — MANUAL TEST ==========")

# TEST 1
print("\n[TEST 1] Fresh genome — should be empty")
g = load_genome(WID)
assert g.event_count == 0
assert g.confidence_score == 0.0
print("  PASS")

# TEST 2
print("\n[TEST 2] Ingest run_001 — light rainfall")
g = ingest_run(WID, "run_001", rainfall_mm=45.0, max_flood_depth=0.12,
               low_cells=800, medium_cells=150, high_cells=50)
assert g.event_count == 1
assert g.confidence_score > 0.0
print(f"  PASS — event_count={g.event_count}  confidence={g.confidence_score}")

# TEST 3
print("\n[TEST 3] Ingest run_002 — heavy rainfall")
g = ingest_run(WID, "run_002", rainfall_mm=180.0, max_flood_depth=1.85,
               low_cells=200, medium_cells=400, high_cells=600)
assert g.event_count == 2
assert g.avg_rainfall_at_flood == (45.0 + 180.0) / 2
print(f"  PASS — avg_rain={g.avg_rainfall_at_flood:.1f}  high_ratio={g.typical_high_ratio:.3f}")

# TEST 4
print("\n[TEST 4] Reload from disk — persistence check")
g2 = load_genome(WID)
assert g2.event_count == 2
assert len(g2.events) == 2
assert g2.events[0].run_id == "run_001"
assert g2.events[1].run_id == "run_002"
print(f"  PASS — reloaded correctly, events={g2.event_count}")

# TEST 5
print("\n[TEST 5] Satellite validates run_002 — divergence 18%")
g = validate_event(WID, "run_002", divergence_pct=18.0,
                   corrected_manning_n=0.028,
                   corrected_blend_alpha=0.65)
assert g.validated_event_count == 1
assert abs(g.best_manning_n - 0.0329) < 0.0001
print(f"  PASS — validated_count={g.validated_event_count}  manning_n={g.best_manning_n:.5f}")

# TEST 6
print("\n[TEST 6] Ingest 8 more runs — confidence grows")
for i in range(3, 11):
    ingest_run(WID, f"run_00{i}", rainfall_mm=60.0 + i*10,
               max_flood_depth=0.5 + i*0.1,
               low_cells=500, medium_cells=300, high_cells=200)
g = load_genome(WID)
assert g.event_count == 10
assert g.confidence_score >= 0.5
print(f"  PASS — event_count={g.event_count}  confidence={g.confidence_score:.3f}")

# TEST 7
print("\n[TEST 7] Recommended params for next simulation")
params = {
    "manning_n": g.best_manning_n,
    "blend_alpha": g.best_blend_alpha,
    "flood_threshold_rainfall": g.avg_rainfall_at_flood,
    "expected_high_ratio": g.typical_high_ratio,
    "confidence": g.confidence_score,
}
print(f"  {json.dumps(params, indent=4)}")
assert params["confidence"] > 0.0
print("  PASS — params ready for Qt engine")

print_genome(load_genome(WID))
print(f"\n  Genome file saved at: {genome_path(WID)}")
print("\n========== ALL TESTS PASSED ==========\n")
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import os
import time

NS_PATH = r"D:\Desktop\NeroSurrogate\NeroSurrogate"
router  = APIRouter(prefix="/surrogate", tags=["surrogate"])
_runner = None

CONFLICTS = ("config", "engine_bridge", "preprocessing", "inference",
             "model", "dataset_generator", "trainer", "export")


def _is_conflict(name: str) -> bool:
    return any(name == c or name.startswith(c + ".") for c in CONFLICTS)


class _NSContext:
    def __enter__(self):
        import sys
        if NS_PATH not in sys.path:
            sys.path.insert(0, NS_PATH)
        self._saved = {k: v for k, v in list(sys.modules.items()) if _is_conflict(k)}
        for k in self._saved:
            del sys.modules[k]
        return self

    def __exit__(self, *a):
        import sys
        for k in [m for m in sys.modules if _is_conflict(m)]:
            del sys.modules[k]
        for k, v in self._saved.items():
            sys.modules[k] = v


class SurrogateProxy:
    def __init__(self):
        with _NSContext():
            from inference.surrogate_runner import SurrogateRunner
            onnx = os.path.join(NS_PATH, "output", "models", "nerosurrogate.onnx")
            norm = os.path.join(NS_PATH, "output", "datasets", "norm_stats.json")
            if not os.path.exists(onnx):
                raise RuntimeError("ONNX model not found")
            self._runner = SurrogateRunner(onnx_path=onnx, norm_path=norm)

    def predict(self, **kw):
        return self._runner.predict(**kw)

    def predict_stats(self, *a, **kw):
        return self._runner.predict_stats(*a, **kw)


def _get_runner():
    global _runner
    if _runner is None:
        _runner = SurrogateProxy()
    return _runner


class WhatIfRequest(BaseModel):
    dem:                 List[List[float]]
    rainfall_mm_hr:      float
    duration_hr:         float = 6.0
    dTheta:              float = 0.3
    manning_n:           float = 0.035
    cell_size_m:         float = 30.0
    rainfall_multiplier: float = 1.0


class WhatIfResponse(BaseModel):
    rainfall_used:     float
    max_depth_m:       float
    mean_depth_m:      float
    flooded_fraction:  float
    high_risk_cells:   int
    medium_risk_cells: int
    risk_delta_m:      float
    inference_ms:      float


class BatchRequest(BaseModel):
    dem:               List[List[float]]
    n_scenarios:       int   = 100
    rain_min:          float = 10.0
    rain_max:          float = 150.0
    duration_hr:       float = 6.0
    dTheta:            float = 0.3
    manning_n:         float = 0.035
    cell_size_m:       float = 30.0
    physics_single_ms: float = 45000.0


class ScenarioResult(BaseModel):
    scenario_id:      int
    rainfall_mm_hr:   float
    max_depth_m:      float
    mean_depth_m:     float
    flooded_fraction: float
    high_risk_cells:  int
    medium_risk_cells: int
    risk_level:       str


class BatchResponse(BaseModel):
    n_scenarios:          int
    total_ms:             float
    avg_ms_per_scenario:  float
    physics_est_total_s:  float
    speedup_x:            float
    rain_min:             float
    rain_max:             float
    critical_threshold_mm: Optional[float]
    high_threshold_mm:     Optional[float]
    medium_threshold_mm:   Optional[float]
    max_depth_overall:     float
    scenarios:            List[ScenarioResult]


def _classify_risk(max_depth: float, high_cells: int) -> str:
    if max_depth > 1.0 or high_cells > 500:
        return "CRITICAL"
    elif max_depth > 0.5 or high_cells > 100:
        return "HIGH"
    elif max_depth > 0.1 or high_cells > 0:
        return "MEDIUM"
    return "LOW"


@router.post("/batch", response_model=BatchResponse)
def batch_scenarios(req: BatchRequest):
    runner = _get_runner()
    dem    = np.array(req.dem, dtype=np.float64)

    rainfall_values = np.linspace(req.rain_min, req.rain_max, req.n_scenarios)

    results    = []
    t0_total   = time.perf_counter()

    for i, rain in enumerate(rainfall_values):
        flood = runner.predict(
            dem         = dem,
            rainfall    = float(rain),
            duration    = req.duration_hr,
            dTheta      = req.dTheta,
            manning_n   = req.manning_n,
            cell_size_m = req.cell_size_m,
        )
        stats      = runner.predict_stats(flood)
        risk_level = _classify_risk(stats["max_depth_m"], stats["high_risk_cells"])

        results.append(ScenarioResult(
            scenario_id       = i + 1,
            rainfall_mm_hr    = round(float(rain), 2),
            max_depth_m       = round(stats["max_depth_m"], 4),
            mean_depth_m      = round(stats["mean_depth_m"], 4),
            flooded_fraction  = round(stats["flooded_fraction"], 6),
            high_risk_cells   = stats["high_risk_cells"],
            medium_risk_cells = stats["medium_risk_cells"],
            risk_level        = risk_level,
        ))

    total_ms = (time.perf_counter() - t0_total) * 1000

    critical_thresh = next(
        (r.rainfall_mm_hr for r in results if r.risk_level == "CRITICAL"), None
    )
    high_thresh = next(
        (r.rainfall_mm_hr for r in results if r.risk_level in ("HIGH", "CRITICAL")), None
    )
    medium_thresh = next(
        (r.rainfall_mm_hr for r in results if r.risk_level in ("MEDIUM", "HIGH", "CRITICAL")), None
    )

    max_depth_overall = max(r.max_depth_m for r in results)
    physics_est_s     = req.n_scenarios * (req.physics_single_ms / 1000.0)
    speedup           = (physics_est_s * 1000) / max(total_ms, 1)

    return BatchResponse(
        n_scenarios           = req.n_scenarios,
        total_ms              = round(total_ms, 1),
        avg_ms_per_scenario   = round(total_ms / req.n_scenarios, 2),
        physics_est_total_s   = round(physics_est_s, 1),
        speedup_x             = round(speedup, 1),
        rain_min              = req.rain_min,
        rain_max              = req.rain_max,
        critical_threshold_mm = critical_thresh,
        high_threshold_mm     = high_thresh,
        medium_threshold_mm   = medium_thresh,
        max_depth_overall     = round(max_depth_overall, 4),
        scenarios             = results,
    )


@router.post("/whatif", response_model=WhatIfResponse)
def whatif(req: WhatIfRequest):
    runner = _get_runner()
    dem    = np.array(req.dem, dtype=np.float64)
    rain   = req.rainfall_mm_hr * req.rainfall_multiplier

    t0    = time.perf_counter()
    flood = runner.predict(dem=dem, rainfall=rain, duration=req.duration_hr,
                           dTheta=req.dTheta, manning_n=req.manning_n,
                           cell_size_m=req.cell_size_m)
    inference_ms = (time.perf_counter() - t0) * 1000

    stats    = runner.predict_stats(flood)
    baseline = runner.predict(dem=dem, rainfall=req.rainfall_mm_hr,
                              duration=req.duration_hr, dTheta=req.dTheta,
                              manning_n=req.manning_n, cell_size_m=req.cell_size_m)
    delta = stats["max_depth_m"] - runner.predict_stats(baseline)["max_depth_m"]

    return WhatIfResponse(
        rainfall_used=rain, max_depth_m=stats["max_depth_m"],
        mean_depth_m=stats["mean_depth_m"], flooded_fraction=stats["flooded_fraction"],
        high_risk_cells=stats["high_risk_cells"], medium_risk_cells=stats["medium_risk_cells"],
        risk_delta_m=delta, inference_ms=round(inference_ms, 3),
    )


@router.get("/status")
def status():
    try:
        _get_runner()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "unavailable", "reason": str(e)}
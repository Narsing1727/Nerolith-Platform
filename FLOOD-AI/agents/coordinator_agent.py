from typing import Dict, List, Optional
import numpy as np
import os

from core.schemas import (
    RiskLevel, AlertEvent, AlertSeverity,
    CoordinatorDecision, RegionConfig
)
from core.region_registry import registry

RISK_ORDER = [RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
NS_PATH    = r"D:\Desktop\NeroSurrogate\NeroSurrogate"

CONFLICTS = ("config", "engine_bridge", "preprocessing", "inference",
             "model", "dataset_generator", "trainer", "export")


def _is_conflict(name: str) -> bool:
    return any(name == c or name.startswith(c + ".") for c in CONFLICTS)


def _risk_index(level: RiskLevel) -> int:
    return RISK_ORDER.index(level)


def _higher(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    return a if _risk_index(a) >= _risk_index(b) else b


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
            if not os.path.exists(onnx) or not os.path.exists(norm):
                raise RuntimeError("model not found")
            self._runner = SurrogateRunner(onnx_path=onnx, norm_path=norm)

    def predict(self, **kw):
        return self._runner.predict(**kw)

    def predict_stats(self, *a, **kw):
        return self._runner.predict_stats(*a, **kw)


class CoordinatorAgent:
    def __init__(self):
        self._last_decision: CoordinatorDecision = None
        self._surrogate       = None
        self._surrogate_tried = False
        self._last_dem: Optional[np.ndarray] = None

    def set_dem(self, dem: np.ndarray):
        self._last_dem = dem

    def _get_surrogate(self):
        if self._surrogate_tried:
            return self._surrogate
        self._surrogate_tried = True
        try:
            self._surrogate = SurrogateProxy()
        except Exception as e:
            print(f"[coordinator] surrogate unavailable: {e}")
        return self._surrogate

    def _surrogate_whatif(self, rainfall_mm: float, multiplier: float = 1.2) -> Optional[dict]:
        if self._last_dem is None:
            return None
        runner = self._get_surrogate()
        if runner is None:
            return None
        try:
            flood      = runner.predict(dem=self._last_dem, rainfall=rainfall_mm * multiplier,
                                        duration=6.0, dTheta=0.3, manning_n=0.035)
            stats      = runner.predict_stats(flood)
            baseline   = runner.predict(dem=self._last_dem, rainfall=rainfall_mm,
                                        duration=6.0, dTheta=0.3, manning_n=0.035)
            base_stats = runner.predict_stats(baseline)
            stats["risk_delta_m"]  = stats["max_depth_m"] - base_stats["max_depth_m"]
            stats["rainfall_used"] = rainfall_mm * multiplier
            return stats
        except Exception:
            return None

    def process(self, timestep: int, region_reports: List[dict],
                rainfall_mm: float = 0.0) -> CoordinatorDecision:
        region_risks: Dict[str, RiskLevel] = {}
        propagation_warnings: List[str]    = []
        surrogate_forecast: Optional[dict] = None

        for report in region_reports:
            region_risks[report["region_id"]] = report["risk_level"]

        self._propagate_risks(region_risks, region_reports, propagation_warnings)
        global_risk = self._compute_global_risk(region_risks)

        if global_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL) and rainfall_mm > 0:
            surrogate_forecast = self._surrogate_whatif(rainfall_mm, multiplier=1.2)

        alerts = self._generate_alerts(timestep, region_reports, region_risks, surrogate_forecast)

        decision = CoordinatorDecision(
            timestep=timestep, global_risk=global_risk,
            region_risks=region_risks, alerts_issued=alerts,
            propagation_warnings=propagation_warnings
        )
        self._last_decision = decision
        return decision

    def _propagate_risks(self, region_risks, reports, warnings):
        for r in reports:
            if r["risk_level"] in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                for ds in registry.get_downstream(r["region_id"]):
                    current = region_risks.get(ds.region_id, RiskLevel.NONE)
                    if _risk_index(current) < _risk_index(RiskLevel.MEDIUM):
                        region_risks[ds.region_id] = RiskLevel.MEDIUM
                        warnings.append(f"propagated_risk:{r['region_id']}->{ds.region_id}")

    def _compute_global_risk(self, region_risks):
        if not region_risks:
            return RiskLevel.NONE
        return max(region_risks.values(), key=lambda r: _risk_index(r))

    def _generate_alerts(self, timestep, reports, region_risks, surrogate_forecast=None):
        alerts = []
        for report in reports:
            rid  = report["region_id"]
            risk = region_risks.get(rid, RiskLevel.NONE)
            if risk == RiskLevel.CRITICAL:
                msg = f"Critical flood depth {round(report['flood_max_m'], 2)}m in {rid}. Immediate action required."
                if surrogate_forecast:
                    msg += (f" Surrogate (+20% rain): max={surrogate_forecast['max_depth_m']:.2f}m "
                            f"delta=+{surrogate_forecast['risk_delta_m']:.2f}m")
                alerts.append(AlertEvent(region_id=rid, severity=AlertSeverity.EMERGENCY,
                                         message=msg, timestep=timestep))
            elif risk == RiskLevel.HIGH:
                msg = (f"High flood risk in {rid}. Max depth {round(report['flood_max_m'], 2)}m, "
                       f"trend: {report['trend']}.")
                if surrogate_forecast:
                    msg += (f" If rainfall +20%: depth could reach {surrogate_forecast['max_depth_m']:.2f}m "
                            f"(+{surrogate_forecast['risk_delta_m']:.2f}m).")
                alerts.append(AlertEvent(region_id=rid, severity=AlertSeverity.CRITICAL,
                                         message=msg, timestep=timestep))
            elif report.get("rising_fast"):
                alerts.append(AlertEvent(region_id=rid, severity=AlertSeverity.WARNING,
                                         message=f"Rapid water rise in {rid}. Monitor closely.",
                                         timestep=timestep))
        return alerts

    def last_decision(self):
        return self._last_decision


coordinator = CoordinatorAgent()
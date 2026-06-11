import numpy as np
from dataclasses import dataclass
from inference.surrogate_runner import SurrogateRunner


@dataclass
class ScenarioResult:
    rainfall:         float
    max_depth_m:      float
    flooded_fraction: float
    high_risk_cells:  int
    risk_delta:       float


class FastQuery:
    def __init__(self, runner: SurrogateRunner):
        self.runner  = runner
        self._dem    = None
        self._base   = None
        self._params = {}

    def set_context(self, dem, rainfall, duration, dTheta, manning_n, cell_size_m=30.0):
        self._dem    = dem
        self._params = dict(rainfall=rainfall, duration=duration, dTheta=dTheta,
                            manning_n=manning_n, cell_size_m=cell_size_m)
        self._base   = self.runner.predict_stats(self.runner.predict(dem, **self._params))

    def what_if_rainfall(self, multiplier: float) -> ScenarioResult:
        if self._dem is None:
            raise RuntimeError("Call set_context() first")
        p = dict(self._params, rainfall=self._params["rainfall"] * multiplier)
        flood = self.runner.predict(self._dem, **p)
        stats = self.runner.predict_stats(flood)
        return ScenarioResult(
            rainfall         = p["rainfall"],
            max_depth_m      = stats["max_depth_m"],
            flooded_fraction = stats["flooded_fraction"],
            high_risk_cells  = stats["high_risk_cells"],
            risk_delta       = stats["max_depth_m"] - self._base["max_depth_m"],
        )

    def batch_predict(self, scenarios: list[dict]) -> list[dict]:
        results = []
        for s in scenarios:
            dem = s.get("dem", self._dem)
            p   = {k: s.get(k, self._params.get(k, v))
                   for k, v in [("rainfall", 50.0), ("duration", 6.0),
                                 ("dTheta", 0.3), ("manning_n", 0.035),
                                 ("cell_size_m", 30.0)]}
            flood = self.runner.predict(dem, **p)
            results.append({"scenario": s, **self.runner.predict_stats(flood)})
        return results

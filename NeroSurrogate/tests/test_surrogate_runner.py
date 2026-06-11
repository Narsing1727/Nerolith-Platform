import pytest
import numpy as np


def dem():
    rng = np.random.default_rng(42)
    x   = np.linspace(100, 50, 64)
    d   = np.outer(np.ones(64), x) + rng.uniform(-2, 2, (64, 64))
    return d.astype(np.float64)


def test_loads():
    try:
        from inference.surrogate_runner import SurrogateRunner
        SurrogateRunner()
    except FileNotFoundError:
        pytest.skip("ONNX model not exported yet — run: python main.py export")


def test_predict_shape():
    try:
        from inference.surrogate_runner import SurrogateRunner
        r = SurrogateRunner()
    except FileNotFoundError:
        pytest.skip("ONNX model not exported yet")
    flood = r.predict(dem(), 50.0, 6.0, 0.3, 0.035)
    assert flood.shape == (64, 64)
    assert flood.min() >= 0.0


def test_stats_keys():
    try:
        from inference.surrogate_runner import SurrogateRunner
        r = SurrogateRunner()
    except FileNotFoundError:
        pytest.skip("ONNX model not exported yet")
    flood = r.predict(dem(), 50.0, 6.0, 0.3, 0.035)
    stats = r.predict_stats(flood)
    for k in ["max_depth_m","mean_depth_m","flooded_fraction","high_risk_cells","medium_risk_cells"]:
        assert k in stats

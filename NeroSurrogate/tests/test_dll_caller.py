import pytest
import numpy as np


def make_dem(rows=32, cols=32):
    rng = np.random.default_rng(0)
    x   = np.linspace(100, 50, cols)
    dem = np.outer(np.ones(rows), x) + rng.uniform(-1, 1, (rows, cols))
    return dem


def test_dll_import():
    try:
        from engine_bridge.dll_caller import FloodEngineDLL
    except Exception as e:
        pytest.skip(f"DLL not available: {e}")


def test_run_scenario():
    try:
        from engine_bridge.dll_caller import FloodEngineDLL
    except Exception:
        pytest.skip("DLL not available")
    dem = make_dem()
    with FloodEngineDLL() as eng:
        flood = eng.run_scenario(dem, 50.0, 6.0, 0.035, 6.8, 166.8, 0.486)
    assert flood.shape == dem.shape
    assert flood.min() >= 0.0


def test_get_shape():
    try:
        from engine_bridge.dll_caller import FloodEngineDLL
    except Exception:
        pytest.skip("DLL not available")
    dem = make_dem(48, 64)
    with FloodEngineDLL() as eng:
        eng.set_dem(dem)
        assert eng.get_shape() == (48, 64)

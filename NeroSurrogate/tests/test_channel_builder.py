import numpy as np
import pytest
from preprocessing.channel_builder import build_channels, channel_info
from config import N_CHANNELS


def dem():
    rng = np.random.default_rng(1)
    x   = np.linspace(100, 50, 64)
    d   = np.outer(np.ones(64), x) + rng.uniform(-2, 2, (64, 64))
    return d


def test_shape():
    assert build_channels(dem(), 50.0, 0.3, 0.035).shape == (N_CHANNELS, 64, 64)

def test_dtype():
    assert build_channels(dem(), 50.0, 0.3, 0.035).dtype == np.float32

def test_rainfall_broadcast():
    ch = build_channels(dem(), 77.5, 0.3, 0.035)
    assert np.allclose(ch[3], 77.5)

def test_no_nan():
    ch = build_channels(dem(), 50.0, 0.3, 0.035)
    assert not np.isnan(ch).any() and not np.isinf(ch).any()

def test_channel_info():
    assert len(channel_info()) == N_CHANNELS

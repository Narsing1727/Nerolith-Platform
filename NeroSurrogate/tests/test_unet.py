import torch
from model.unet import NeroSurrogateUNet
from config import N_CHANNELS


def test_forward_shape():
    m   = NeroSurrogateUNet()
    out = m(torch.randn(2, N_CHANNELS, 64, 64))
    assert out.shape == (2, 1, 64, 64)

def test_non_negative():
    m   = NeroSurrogateUNet()
    out = m(torch.randn(1, N_CHANNELS, 64, 64))
    assert out.min().item() >= 0.0

def test_non_square():
    m   = NeroSurrogateUNet()
    out = m(torch.randn(1, N_CHANNELS, 48, 80))
    assert out.shape == (1, 1, 48, 80)

def test_param_count():
    m = NeroSurrogateUNet()
    assert 100_000 < m.count_params() < 50_000_000

def test_no_nan():
    m   = NeroSurrogateUNet()
    out = m(torch.randn(1, N_CHANNELS, 64, 64))
    assert not torch.isnan(out).any()

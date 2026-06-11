import numpy as np
import torch


def flip_h(x: torch.Tensor, y: torch.Tensor):
    return torch.flip(x, [2]), torch.flip(y, [2])


def flip_v(x: torch.Tensor, y: torch.Tensor):
    return torch.flip(x, [1]), torch.flip(y, [1])


def add_rainfall_noise(x: torch.Tensor, std: float = 0.05):
    x = x.clone()
    x[3] += torch.randn_like(x[3]) * std
    return x


def add_manning_noise(x: torch.Tensor, std: float = 0.02):
    x = x.clone()
    x[5] += torch.randn_like(x[5]) * std
    return x


def augment(x: torch.Tensor, y: torch.Tensor,
            p_flip_h: float = 0.5,
            p_flip_v: float = 0.5,
            p_noise:  float = 0.3) -> tuple[torch.Tensor, torch.Tensor]:
    if torch.rand(1).item() < p_flip_h:
        x, y = flip_h(x, y)
    if torch.rand(1).item() < p_flip_v:
        x, y = flip_v(x, y)
    if torch.rand(1).item() < p_noise:
        x = add_rainfall_noise(x)
    if torch.rand(1).item() < p_noise:
        x = add_manning_noise(x)
    return x, y

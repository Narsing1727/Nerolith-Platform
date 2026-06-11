import torch
from config import FLOOD_THRESHOLD


def rmse(pred, target):
    return torch.sqrt(torch.mean((pred - target) ** 2)).item()

def mae(pred, target):
    return torch.mean(torch.abs(pred - target)).item()

def iou_score(pred, target, threshold=FLOOD_THRESHOLD):
    p = (pred   > threshold).float()
    t = (target > threshold).float()
    inter = (p * t).sum()
    union = (p + t).clamp(0, 1).sum()
    return 1.0 if union == 0 else (inter / union).item()

def critical_success_index(pred, target, threshold=FLOOD_THRESHOLD):
    p     = (pred   > threshold).float()
    t     = (target > threshold).float()
    hits  = (p * t).sum().item()
    fa    = (p * (1 - t)).sum().item()
    miss  = ((1 - p) * t).sum().item()
    denom = hits + fa + miss
    return hits / denom if denom > 0 else 0.0

def bias(pred, target):
    return (pred.mean() - target.mean()).item()

def compute_all(pred, target, max_depth_m=10.0):
    p, t = pred * max_depth_m, target * max_depth_m
    return {
        "rmse_m": rmse(p, t),
        "mae_m":  mae(p, t),
        "iou":    iou_score(p, t),
        "csi":    critical_success_index(p, t),
        "bias_m": bias(p, t),
    }

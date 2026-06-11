import torch
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR
from config import NUM_EPOCHS, LR_MIN, WARMUP_EPOCHS


def build_scheduler(optimizer):
    warmup = LinearLR(optimizer, start_factor=0.1, end_factor=1.0, total_iters=WARMUP_EPOCHS)
    cosine = CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS - WARMUP_EPOCHS, eta_min=LR_MIN)
    return SequentialLR(optimizer, schedulers=[warmup, cosine], milestones=[WARMUP_EPOCHS])

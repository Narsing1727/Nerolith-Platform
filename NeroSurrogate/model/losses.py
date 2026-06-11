import torch
import torch.nn as nn
from config import LOSS_MSE_WEIGHT, LOSS_IOU_WEIGHT, FLOOD_THRESHOLD


class IoULoss(nn.Module):
    def __init__(self, threshold=FLOOD_THRESHOLD, smooth=1e-6):
        super().__init__()
        self.threshold = threshold
        self.smooth    = smooth

    def forward(self, pred, target):
        pred_mask    = torch.sigmoid((pred - self.threshold) * 100)
        target_mask  = (target > self.threshold).float()
        intersection = (pred_mask * target_mask).sum(dim=(2, 3))
        union        = (pred_mask + target_mask - pred_mask * target_mask).sum(dim=(2, 3))
        return (1.0 - ((intersection + self.smooth) / (union + self.smooth))).mean()


class SurrogateLoss(nn.Module):
    def __init__(self, mse_weight=LOSS_MSE_WEIGHT, iou_weight=LOSS_IOU_WEIGHT):
        super().__init__()
        self.mse_w = mse_weight
        self.iou_w = iou_weight
        self.mse   = nn.MSELoss()
        self.iou   = IoULoss()

    def forward(self, pred, target):
        mse  = self.mse(pred, target)
        iou  = self.iou(pred, target)
        total = self.mse_w * mse + self.iou_w * iou
        return total, {"loss": total.item(), "mse_loss": mse.item(), "iou_loss": iou.item()}

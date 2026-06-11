import csv
from loguru import logger as _log
from config import LOG_DIR

FIELDS = ["epoch", "train_loss", "val_loss", "rmse_m", "iou", "csi", "lr"]


class TrainingLogger:
    def __init__(self, filename="training.csv"):
        self.path = LOG_DIR / filename
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=FIELDS).writeheader()

    def log(self, epoch, train_loss, val_loss, metrics, lr):
        row = {"epoch": epoch, "train_loss": round(train_loss, 6),
               "val_loss": round(val_loss, 6), "rmse_m": round(metrics.get("rmse_m", 0), 5),
               "iou": round(metrics.get("iou", 0), 5), "csi": round(metrics.get("csi", 0), 5),
               "lr": round(lr, 8)}
        with open(self.path, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writerow(row)
        _log.info(f"Epoch {epoch:04d} | train={train_loss:.4f} val={val_loss:.4f} | "
                  f"rmse={row['rmse_m']:.4f}m iou={row['iou']:.4f} | lr={lr:.2e}")

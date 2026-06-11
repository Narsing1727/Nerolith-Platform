import torch
from pathlib import Path
from loguru import logger
from config import BEST_CKPT_PATH


def save_checkpoint(model, optimizer, epoch, val_loss, path=BEST_CKPT_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"epoch": epoch, "val_loss": val_loss,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict()}, path)
    logger.info(f"Checkpoint saved → {path} (epoch={epoch} val={val_loss:.6f})")


def load_checkpoint(model, optimizer=None, path=BEST_CKPT_PATH, device="cpu"):
    if not Path(path).exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")
    ckpt = torch.load(path, map_location=device)
    model.load_state_dict(ckpt["model"])
    if optimizer and "optimizer" in ckpt:
        optimizer.load_state_dict(ckpt["optimizer"])
    logger.info(f"Checkpoint loaded ← {path} (epoch={ckpt['epoch']})")
    return ckpt


def checkpoint_exists(path=BEST_CKPT_PATH):
    return Path(path).exists()

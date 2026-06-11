import torch
from loguru import logger
from config import DEVICE, NUM_EPOCHS, LR, WEIGHT_DECAY, BEST_CKPT_PATH, NORM_STATS_PATH, RAW_DIR, BATCH_SIZE
from model.unet     import NeroSurrogateUNet
from model.losses   import SurrogateLoss
from model.metrics  import compute_all
from trainer.checkpoint import save_checkpoint, load_checkpoint, checkpoint_exists
from trainer.scheduler  import build_scheduler
from trainer.logger     import TrainingLogger
from preprocessing.normalizer import ChannelNormalizer
from preprocessing.dataset    import make_dataloaders, split_scenarios


def train_epoch(model, loader, loss_fn, optimizer, device):
    model.train()
    total = 0.0
    for batch in loader:
        x, y = batch["input"].to(device), batch["target"].to(device)
        optimizer.zero_grad()
        loss, _ = loss_fn(model(x), y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total += loss.item()
    return total / len(loader)


@torch.no_grad()
def val_epoch(model, loader, loss_fn, device):
    model.eval()
    total, preds, tgts = 0.0, [], []
    for batch in loader:
        x, y = batch["input"].to(device), batch["target"].to(device)
        pred = model(x)
        loss, _ = loss_fn(pred, y)
        total += loss.item()
        preds.append(pred.cpu())
        tgts.append(y.cpu())
    metrics = compute_all(torch.cat(preds), torch.cat(tgts))
    return total / len(loader), metrics


def run_training(resume=False):
    norm = ChannelNormalizer()
    train_dirs, _, _ = split_scenarios(RAW_DIR)

    logger.info("Fitting normalizer...")
    from preprocessing.channel_builder import build_channels
    from engine_bridge.grid_io import load_grid
    from dataset_generator.param_sampler import load_scenario_params

    samples = []
    for d in train_dirs[:min(200, len(train_dirs))]:
        try:
            dem    = load_grid(d / "dem.bin").astype("float64")
            params = load_scenario_params(d)
            samples.append(build_channels(dem, params.rainfall_mm_hr,
                                          params.dTheta, params.manning_n,
                                          params.cell_size_m))
        except Exception:
            continue
    norm.fit(samples)
    norm.save(NORM_STATS_PATH)

    train_loader, val_loader, _ = make_dataloaders(norm, RAW_DIR, BATCH_SIZE)
    model     = NeroSurrogateUNet().to(DEVICE)
    loss_fn   = SurrogateLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = build_scheduler(optimizer)
    tlog      = TrainingLogger()
    start     = 0
    best_val  = float("inf")

    if resume and checkpoint_exists():
        ckpt  = load_checkpoint(model, optimizer, device=DEVICE)
        start = ckpt["epoch"] + 1
        best_val = ckpt["val_loss"]

    logger.info(f"Params: {model.count_params():,} | Device: {DEVICE}")

    for epoch in range(start, NUM_EPOCHS):
        train_loss        = train_epoch(model, train_loader, loss_fn, optimizer, DEVICE)
        val_loss, metrics = val_epoch(model, val_loader, loss_fn, DEVICE)
        lr                = scheduler.get_last_lr()[0]
        tlog.log(epoch, train_loss, val_loss, metrics, lr)
        scheduler.step()
        if val_loss < best_val:
            best_val = val_loss
            save_checkpoint(model, optimizer, epoch, val_loss)

    logger.info(f"Training done. Best val: {best_val:.6f}")
    return model

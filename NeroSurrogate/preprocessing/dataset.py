import numpy as np
import torch
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from config import RAW_DIR, VAL_SPLIT, TEST_SPLIT, BATCH_SIZE
from engine_bridge.grid_io import load_grid
from preprocessing.channel_builder import build_channels, channels_to_tensor, target_to_tensor
from preprocessing.normalizer import ChannelNormalizer
from dataset_generator.param_sampler import load_scenario_params
from dataset_generator.augmentor import augment


class FloodScenarioDataset(Dataset):
    def __init__(self, scenario_dirs: list[Path], normalizer: ChannelNormalizer,
                 augment_data: bool = False, max_depth_m: float = 10.0):
        self.dirs        = scenario_dirs
        self.norm        = normalizer
        self.augment     = augment_data
        self.max_depth_m = max_depth_m

    def __len__(self):
        return len(self.dirs)

    def __getitem__(self, idx):
        d      = self.dirs[idx]
        dem    = load_grid(d / "dem.bin").astype(np.float64)
        flood  = load_grid(d / "flood.bin")
        params = load_scenario_params(d)

        channels = build_channels(dem, params.rainfall_mm_hr,
                                  params.dTheta, params.manning_n,
                                  params.cell_size_m)
        x = self.norm.normalize(channels_to_tensor(channels))
        y = self.norm.normalize_target(target_to_tensor(flood), self.max_depth_m)

        if self.augment:
            x, y = augment(x, y)

        return {"input": x, "target": y, "scenario_id": d.name}


def split_scenarios(raw_dir: Path = RAW_DIR, val_split: float = VAL_SPLIT,
                    test_split: float = TEST_SPLIT, seed: int = 42):
    all_dirs = sorted([d for d in raw_dir.iterdir()
                       if d.is_dir() and (d / "flood.bin").exists()])
    if not all_dirs:
        raise RuntimeError(f"No scenarios in {raw_dir} — run generate first")

    rng     = np.random.default_rng(seed)
    idxs    = rng.permutation(len(all_dirs))
    n_test  = max(1, int(len(all_dirs) * test_split))
    n_val   = max(1, int(len(all_dirs) * val_split))

    return (
        [all_dirs[i] for i in idxs[n_test + n_val:]],
        [all_dirs[i] for i in idxs[n_test:n_test + n_val]],
        [all_dirs[i] for i in idxs[:n_test]],
    )


def make_dataloaders(normalizer: ChannelNormalizer, raw_dir: Path = RAW_DIR,
                     batch_size: int = BATCH_SIZE, num_workers: int = 2, seed: int = 42):
    train_dirs, val_dirs, test_dirs = split_scenarios(raw_dir, seed=seed)

    def loader(dirs, shuffle, aug):
        return DataLoader(FloodScenarioDataset(dirs, normalizer, aug),
                          batch_size=batch_size, shuffle=shuffle,
                          num_workers=num_workers, pin_memory=True)

    return loader(train_dirs, True, True), loader(val_dirs, False, False), loader(test_dirs, False, False)

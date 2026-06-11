import time
import numpy as np
import onnxruntime as ort
from loguru import logger
from config import ONNX_MODEL_PATH, NORM_STATS_PATH, INFERENCE_TIMEOUT_MS
from preprocessing.channel_builder import build_channels
from preprocessing.normalizer import ChannelNormalizer
import torch


def _pad_to_multiple(x: np.ndarray, multiple: int = 16) -> tuple[np.ndarray, tuple]:
    _, _, h, w = x.shape
    pad_h = (multiple - h % multiple) % multiple
    pad_w = (multiple - w % multiple) % multiple
    if pad_h == 0 and pad_w == 0:
        return x, (h, w)
    return np.pad(x, ((0,0),(0,0),(0,pad_h),(0,pad_w)), mode='edge'), (h, w)


class SurrogateRunner:
    def __init__(self, onnx_path=ONNX_MODEL_PATH, norm_path=NORM_STATS_PATH):
        self.norm         = ChannelNormalizer.from_file(norm_path)
        so                = ort.SessionOptions()
        so.intra_op_num_threads = 1
        so.inter_op_num_threads = 1
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.sess         = ort.InferenceSession(str(onnx_path),
                                                 sess_options=so,
                                                 providers=["CPUExecutionProvider"])
        self._in_name     = self.sess.get_inputs()[0].name
        self._out_name    = self.sess.get_outputs()[0].name
        logger.info(f"SurrogateRunner ready: {onnx_path}")

    def predict(self, dem, rainfall, duration, dTheta, manning_n,
                cell_size_m=30.0, max_depth_m=10.0) -> np.ndarray:
        orig_h, orig_w = dem.shape
        channels = build_channels(dem, rainfall, dTheta, manning_n, cell_size_m)
        x        = self.norm.normalize(
                       torch.from_numpy(channels.astype(np.float32)).unsqueeze(0)
                   ).numpy()
        x, (h, w) = _pad_to_multiple(x, 16)
        t0  = time.perf_counter()
        out = self.sess.run([self._out_name], {self._in_name: x})[0]
        ms  = (time.perf_counter() - t0) * 1000
        if ms > INFERENCE_TIMEOUT_MS:
            logger.warning(f"Inference {ms:.1f}ms > limit {INFERENCE_TIMEOUT_MS}ms")
        result = np.clip(out[0, 0] * max_depth_m, 0, None).astype(np.float32)
        return result[:orig_h, :orig_w]

    def predict_stats(self, flood: np.ndarray, threshold=0.01) -> dict:
        mask = flood > threshold
        return {
            "max_depth_m":       float(flood.max()),
            "mean_depth_m":      float(flood[mask].mean()) if mask.any() else 0.0,
            "flooded_fraction":  float(mask.sum()) / flood.size,
            "high_risk_cells":   int((flood > 0.5).sum()),
            "medium_risk_cells": int(((flood > 0.08) & (flood <= 0.5)).sum()),
        }
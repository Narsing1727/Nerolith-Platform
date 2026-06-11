import numpy as np
from pipeline.stages.void_fill import VoidFilledDEM
from pipeline.stages.source_select import DEMSource
from dataclasses import dataclass


SOURCE_QUALITY = {
    "cop-dem-glo-30": 0.95,
    "cop-dem-glo-90": 0.85,
    "srtmgl1": 0.80,
    "alos-dem": 0.85,
}

VOID_FILL_PENALTY = 0.6
EDGE_PENALTY = 0.85
EDGE_PIXELS = 3


@dataclass
class ConfidenceRaster:
    array: np.ndarray
    transform: object
    crs: object
    mean_confidence: float


def compute_confidence(
    filled: VoidFilledDEM,
    source: DEMSource,
    original_nodata_mask: np.ndarray
) -> ConfidenceRaster:
    base_quality = SOURCE_QUALITY.get(source.collection, 0.75)
    confidence = np.full(filled.array.shape, base_quality, dtype=np.float32)

    confidence[original_nodata_mask] *= VOID_FILL_PENALTY

    confidence[:EDGE_PIXELS, :] *= EDGE_PENALTY
    confidence[-EDGE_PIXELS:, :] *= EDGE_PENALTY
    confidence[:, :EDGE_PIXELS] *= EDGE_PENALTY
    confidence[:, -EDGE_PIXELS:] *= EDGE_PENALTY

    confidence = np.clip(confidence, 0.0, 1.0)
    mean_confidence = round(float(confidence.mean()), 4)

    return ConfidenceRaster(
        array=confidence,
        transform=filled.transform,
        crs=filled.crs,
        mean_confidence=mean_confidence
    )
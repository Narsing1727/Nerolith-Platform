import numpy as np
import rasterio
import tempfile
import os
import whitebox
from pipeline.stages.void_fill import VoidFilledDEM
from dataclasses import dataclass


@dataclass
class ConditionedDEM:
    array: np.ndarray
    transform: object
    crs: object
    nodata: float


def wang_liu_fill(filled: VoidFilledDEM) -> ConditionedDEM:
    wbt = whitebox.WhiteboxTools()
    wbt.verbose = False

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.tif")
        output_path = os.path.join(tmpdir, "output.tif")

        with rasterio.open(
            input_path, "w",
            driver="GTiff",
            height=filled.array.shape[0],
            width=filled.array.shape[1],
            count=1,
            dtype=np.float32,
            crs=filled.crs,
            transform=filled.transform,
            nodata=filled.nodata
        ) as dst:
            dst.write(filled.array, 1)

        wbt.fill_depressions_wang_and_liu(
            dem=input_path,
            output=output_path,
            fix_flats=True,
            flat_increment=0.001
        )

        with rasterio.open(output_path) as src:
            conditioned = src.read(1)

    return ConditionedDEM(
        array=conditioned,
        transform=filled.transform,
        crs=filled.crs,
        nodata=filled.nodata
    )
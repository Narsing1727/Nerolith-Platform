import numpy as np
import rasterio
import tempfile
import os
import whitebox
from pipeline.stages.wang_liu import ConditionedDEM
from dataclasses import dataclass


@dataclass
class FlowGrids:
    d8_pointer: np.ndarray
    flow_accumulation: np.ndarray
    transform: object
    crs: object
    nodata: float


def compute_flow(conditioned: ConditionedDEM) -> FlowGrids:
    wbt = whitebox.WhiteboxTools()
    wbt.verbose = False

    with tempfile.TemporaryDirectory() as tmpdir:
        dem_path = os.path.join(tmpdir, "dem.tif")
        d8_path = os.path.join(tmpdir, "d8.tif")
        accum_path = os.path.join(tmpdir, "accum.tif")

        with rasterio.open(
            dem_path, "w",
            driver="GTiff",
            height=conditioned.array.shape[0],
            width=conditioned.array.shape[1],
            count=1,
            dtype=np.float32,
            crs=conditioned.crs,
            transform=conditioned.transform,
            nodata=conditioned.nodata
        ) as dst:
            dst.write(conditioned.array, 1)

        wbt.d8_pointer(
            dem=dem_path,
            output=d8_path
        )

        wbt.d8_flow_accumulation(
            i=d8_path,
            output=accum_path,
            pntr=True
        )

        with rasterio.open(d8_path) as src:
            d8 = src.read(1)

        with rasterio.open(accum_path) as src:
            accum = src.read(1)

    return FlowGrids(
        d8_pointer=d8,
        flow_accumulation=accum,
        transform=conditioned.transform,
        crs=conditioned.crs,
        nodata=conditioned.nodata
    )
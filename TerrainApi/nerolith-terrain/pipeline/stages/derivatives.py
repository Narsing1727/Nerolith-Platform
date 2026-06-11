import numpy as np
import rasterio
import tempfile
import os
import whitebox
from pipeline.stages.wang_liu import ConditionedDEM
from pipeline.stages.flow import FlowGrids
from dataclasses import dataclass


@dataclass
class TerrainDerivatives:
    twi: np.ndarray
    slope: np.ndarray
    aspect: np.ndarray
    transform: object
    crs: object


def compute_derivatives(conditioned: ConditionedDEM, flow: FlowGrids) -> TerrainDerivatives:
    wbt = whitebox.WhiteboxTools()
    wbt.verbose = False

    with tempfile.TemporaryDirectory() as tmpdir:
        dem_path = os.path.join(tmpdir, "dem.tif")
        accum_path = os.path.join(tmpdir, "accum.tif")
        slope_path = os.path.join(tmpdir, "slope.tif")
        aspect_path = os.path.join(tmpdir, "aspect.tif")
        twi_path = os.path.join(tmpdir, "twi.tif")

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

        with rasterio.open(
            accum_path, "w",
            driver="GTiff",
            height=flow.flow_accumulation.shape[0],
            width=flow.flow_accumulation.shape[1],
            count=1,
            dtype=np.float32,
            crs=flow.crs,
            transform=flow.transform,
            nodata=flow.nodata
        ) as dst:
            dst.write(flow.flow_accumulation, 1)

        wbt.slope(
            dem=dem_path,
            output=slope_path,
            units="degrees"
        )

        wbt.aspect(
            dem=dem_path,
            output=aspect_path
        )

        wbt.wetness_index(
            sca=accum_path,
            slope=slope_path,
            output=twi_path
        )

        with rasterio.open(twi_path) as src:
            twi = src.read(1)

        with rasterio.open(slope_path) as src:
            slope = src.read(1)

        with rasterio.open(aspect_path) as src:
            aspect = src.read(1)

    return TerrainDerivatives(
        twi=twi,
        slope=slope,
        aspect=aspect,
        transform=conditioned.transform,
        crs=conditioned.crs
    )
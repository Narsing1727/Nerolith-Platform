import numpy as np
import rasterio
import tempfile
import os
import whitebox
from rasterio.transform import from_bounds
from pipeline.stages.datum_norm import NormalizedDEM
from dataclasses import dataclass


@dataclass
class VoidFilledDEM:
    array: np.ndarray
    transform: object
    crs: object
    nodata: float
    void_percent: float


def fill_voids(normalized: NormalizedDEM) -> VoidFilledDEM:
    wbt = whitebox.WhiteboxTools()
    wbt.verbose = False

    array = normalized.array.copy()
    nodata = normalized.nodata

    void_mask = (array == nodata) | np.isnan(array)
    void_percent = round(float(void_mask.sum() / array.size * 100), 4)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.tif")
        output_path = os.path.join(tmpdir, "output.tif")

        with rasterio.open(
            input_path, "w",
            driver="GTiff",
            height=array.shape[0],
            width=array.shape[1],
            count=1,
            dtype=np.float32,
            crs=normalized.crs,
            transform=normalized.transform,
            nodata=nodata
        ) as dst:
            dst.write(array, 1)

        wbt.fill_missing_data(
            i=input_path,
            output=output_path,
            filter=11,
            weight=2.0,
            no_edges=True
        )

        with rasterio.open(output_path) as src:
            filled_array = src.read(1)

    return VoidFilledDEM(
        array=filled_array,
        transform=normalized.transform,
        crs=normalized.crs,
        nodata=nodata,
        void_percent=void_percent
    )
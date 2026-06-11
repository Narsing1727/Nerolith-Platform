import numpy as np
import rasterio
import tempfile
import os
import whitebox
from rasterio.features import shapes
from pipeline.stages.flow import FlowGrids
from pipeline.stages.streams import StreamNetwork
from dataclasses import dataclass


@dataclass
class Watershed:
    geojson: dict
    raster: np.ndarray
    transform: object
    crs: object


def delineate_watershed(flow: FlowGrids, streams: StreamNetwork) -> Watershed:
    wbt = whitebox.WhiteboxTools()
    wbt.verbose = False

    with tempfile.TemporaryDirectory() as tmpdir:
        d8_path = os.path.join(tmpdir, "d8.tif")
        accum_path = os.path.join(tmpdir, "accum.tif")
        pour_path = os.path.join(tmpdir, "pour.tif")
        watershed_path = os.path.join(tmpdir, "watershed.tif")

        with rasterio.open(
            d8_path, "w",
            driver="GTiff",
            height=flow.d8_pointer.shape[0],
            width=flow.d8_pointer.shape[1],
            count=1,
            dtype=np.float32,
            crs=flow.crs,
            transform=flow.transform,
            nodata=flow.nodata
        ) as dst:
            dst.write(flow.d8_pointer, 1)

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

        max_accum_idx = np.unravel_index(
            flow.flow_accumulation.argmax(),
            flow.flow_accumulation.shape
        )

        pour_array = np.zeros_like(flow.flow_accumulation)
        pour_array[max_accum_idx] = 1.0

        with rasterio.open(
            pour_path, "w",
            driver="GTiff",
            height=pour_array.shape[0],
            width=pour_array.shape[1],
            count=1,
            dtype=np.float32,
            crs=flow.crs,
            transform=flow.transform,
            nodata=0.0
        ) as dst:
            dst.write(pour_array, 1)

        wbt.watershed(
            d8_pntr=d8_path,
            pour_pts=pour_path,
            output=watershed_path
        )

        with rasterio.open(watershed_path) as src:
            watershed_raster = src.read(1)
            crs = src.crs
            transform = src.transform

        features = []
        mask = watershed_raster > 0
        for geom, val in shapes(
            watershed_raster.astype(np.float32),
            mask=mask,
            transform=transform
        ):
            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {"basin_id": int(val)}
            })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return Watershed(
        geojson=geojson,
        raster=watershed_raster,
        transform=transform,
        crs=crs
    )
import numpy as np
import rasterio
import tempfile
import os
import json
import whitebox
from rasterio.features import shapes
from shapely.geometry import shape, mapping
from pipeline.stages.flow import FlowGrids
from pipeline.stages.wang_liu import ConditionedDEM
from dataclasses import dataclass


@dataclass
class StreamNetwork:
    geojson: dict
    stream_raster: np.ndarray
    transform: object
    crs: object


def extract_streams(conditioned: ConditionedDEM, flow: FlowGrids, threshold: int = 1000) -> StreamNetwork:
    wbt = whitebox.WhiteboxTools()
    wbt.verbose = False

    with tempfile.TemporaryDirectory() as tmpdir:
        d8_path = os.path.join(tmpdir, "d8.tif")
        accum_path = os.path.join(tmpdir, "accum.tif")
        streams_path = os.path.join(tmpdir, "streams.tif")
        strahler_path = os.path.join(tmpdir, "strahler.tif")
        vector_path = os.path.join(tmpdir, "streams.shp")

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

        wbt.extract_streams(
            flow_accum=accum_path,
            output=streams_path,
            threshold=threshold
        )

        wbt.strahler_stream_order(
            d8_pntr=d8_path,
            streams=streams_path,
            output=strahler_path
        )

        wbt.raster_streams_to_vector(
            streams=strahler_path,
            d8_pntr=d8_path,
            output=vector_path
        )

        with rasterio.open(streams_path) as src:
            stream_raster = src.read(1)
            crs = src.crs
            transform = src.transform

        features = []
        with rasterio.open(strahler_path) as src:
            image = src.read(1)
            mask = image > 0
            for geom, val in shapes(image, mask=mask, transform=src.transform):
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {"strahler_order": int(val)}
                })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return StreamNetwork(
        geojson=geojson,
        stream_raster=stream_raster,
        transform=transform,
        crs=crs
    )
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
from pipeline.stages.source_select import DEMSource
from dataclasses import dataclass
import planetary_computer
import pystac_client


@dataclass
class FetchedDEM:
    array: np.ndarray
    transform: object
    crs: CRS
    nodata: float
    source: DEMSource


def fetch_dem(source: DEMSource, bbox: list[float]) -> FetchedDEM:
    client = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace
    )

    results = client.search(
        bbox=bbox,
        collections=[source.collection],
        max_items=1
    ).item_collection()

    item = results[0]
    signed_item = planetary_computer.sign(item)
    asset = signed_item.assets.get("data") or signed_item.assets.get("elevation")
    url = asset.href

    with rasterio.open(url) as src:
        src_crs = src.crs

        bbox_transformed = transform_bounds(
            CRS.from_epsg(4326),
            src_crs,
            bbox[0], bbox[1], bbox[2], bbox[3]
        )

        window = from_bounds(
            bbox_transformed[0],
            bbox_transformed[1],
            bbox_transformed[2],
            bbox_transformed[3],
            src.transform
        )

        array = src.read(1, window=window)
        transform = src.window_transform(window)
        nodata = src.nodata if src.nodata is not None else -9999.0

    return FetchedDEM(
        array=array,
        transform=transform,
        crs=src_crs,
        nodata=nodata,
        source=source
    )
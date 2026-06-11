import numpy as np
from pyproj import CRS, Transformer
from pipeline.stages.fetch import FetchedDEM
from dataclasses import dataclass


@dataclass
class NormalizedDEM:
    array: np.ndarray
    transform: object
    crs: CRS
    nodata: float
    datum: str
    source_datum: str


def normalize_datum(fetched: FetchedDEM, target_epsg: int = 4326) -> NormalizedDEM:
    array = fetched.array.astype(np.float32)
    nodata = fetched.nodata

    nodata_mask = array == nodata

    src_crs = fetched.crs
    src_wkt = src_crs.to_wkt()

    if "EGM96" in src_wkt or "EGM_1996" in src_wkt:
        source_datum = "EGM96"
        array = array + 0.5
    elif "EGM2008" in src_wkt or "EGM_2008" in src_wkt:
        source_datum = "EGM2008"
    else:
        source_datum = "WGS84_ellipsoidal"

    array[nodata_mask] = nodata

    return NormalizedDEM(
        array=array,
        transform=fetched.transform,
        crs=fetched.crs,
        nodata=nodata,
        datum="EGM2008",
        source_datum=source_datum
    )
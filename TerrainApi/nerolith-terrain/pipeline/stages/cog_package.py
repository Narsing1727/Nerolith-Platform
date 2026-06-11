import numpy as np
import rasterio
import os
import json
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from dataclasses import dataclass


OUTPUT_BASE = "/mnt/nerolith_outputs"


@dataclass
class PackagedOutputs:
    output_paths: dict
    metadata: dict


def write_tif(array: np.ndarray, path: str, crs, transform, nodata: float = -9999.0):
    with rasterio.open(
        path, "w",
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype=np.float32,
        crs=crs,
        transform=transform,
        nodata=nodata
    ) as dst:
        dst.write(array.astype(np.float32), 1)


def to_cog(input_path: str, output_path: str):
    cog_translate(
        source=input_path,
        dst_path=output_path,
        dst_kwargs=cog_profiles.get("deflate"),
        quiet=True
    )


def package_outputs(
    job_id: str,
    conditioned,
    flow,
    derivatives,
    streams,
    watershed,
    confidence
) -> PackagedOutputs:
    job_dir = os.path.join(OUTPUT_BASE, job_id)
    os.makedirs(job_dir, exist_ok=True)

    output_paths = {}

    layers = {
        "filled_dem": (conditioned.array, conditioned.transform, conditioned.crs),
        "flow_direction": (flow.d8_pointer, flow.transform, flow.crs),
        "flow_accumulation": (flow.flow_accumulation, flow.transform, flow.crs),
        "twi": (derivatives.twi, derivatives.transform, derivatives.crs),
        "slope": (derivatives.slope, derivatives.transform, derivatives.crs),
        "aspect": (derivatives.aspect, derivatives.transform, derivatives.crs),
        "confidence": (confidence.array, confidence.transform, confidence.crs),
    }

    for name, (array, transform, crs) in layers.items():
        raw_path = os.path.join(job_dir, f"{name}_raw.tif")
        cog_path = os.path.join(job_dir, f"{name}.tif")
        write_tif(array, raw_path, crs, transform)
        to_cog(raw_path, cog_path)
        os.remove(raw_path)
        output_paths[name] = cog_path

    watershed_path = os.path.join(job_dir, "watershed.geojson")
    with open(watershed_path, "w") as f:
        json.dump(watershed.geojson, f)
    output_paths["watershed"] = watershed_path

    streams_path = os.path.join(job_dir, "stream_network.geojson")
    with open(streams_path, "w") as f:
        json.dump(streams.geojson, f)
    output_paths["stream_network"] = streams_path

    metadata = {
        "source": "cop-dem-glo-30",
        "confidence_mean": confidence.mean_confidence,
        "resolution_m": 30,
        "job_id": job_id
    }

    return PackagedOutputs(
        output_paths=output_paths,
        metadata=metadata
    )
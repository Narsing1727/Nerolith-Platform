# divergence_engine.py
# Layer 06 — Real-Time Satellite Change Detection Loop
# Nerolith · Flood Intelligence Platform

import numpy as np
import json
import sys
import os
from osgeo import gdal
import warnings




warnings.filterwarnings("ignore")
# ─── CONFIG ───────────────────────────────────────────────
DIVERGENCE_THRESHOLD = 0.15   # 15% — recalibration trigger
MANNING_STEP         = 0.005  # how much to adjust Manning n per iteration
KS_STEP              = 0.1    # how much to adjust Ks (mm/hr) per iteration
# ──────────────────────────────────────────────────────────


def load_geotiff(path: str) -> tuple[np.ndarray, dict]:
    """
    Load a GeoTIFF and return (array, geo_meta).
    Works for both flood sim output and Sentinel-1 SAR extent.
    """
    ds = gdal.Open(path)
    if ds is None:
        raise FileNotFoundError(f"Cannot open: {path}")

    band  = ds.GetRasterBand(1)
    arr   = band.ReadAsArray().astype(np.float32)
    nodata = band.GetNoDataValue()
    if nodata is not None:
        arr[arr == nodata] = np.nan

    meta = {
        "geotransform" : ds.GetGeoTransform(),
        "projection"   : ds.GetProjection(),
        "rows"         : ds.RasterYSize,
        "cols"         : ds.RasterXSize,
    }
    ds = None
    return arr, meta


def sim_to_binary(f_sim: np.ndarray, threshold: float = 0.05) -> np.ndarray:
    """
    Convert continuous depth grid (metres) → binary flood extent.
    Cells with depth > threshold = 1 (flooded), else 0.
    """
    binary = np.where(f_sim > threshold, 1.0, 0.0)
    binary[np.isnan(f_sim)] = np.nan
    return binary


def sar_to_binary(f_obs: np.ndarray) -> np.ndarray:
    """
    Sentinel-1 SAR flood extent is already binary (0/1).
    Just clean nodata.
    """
    out = f_obs.copy()
    out[np.isnan(f_obs)] = np.nan
    return out


def align_grids(f_sim: np.ndarray, f_obs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    If grids have different shapes, resample f_obs to match f_sim.
    Simple nearest-neighbour via numpy (no extra deps).
    Production mein GDAL Warp use karna.
    """
    if f_sim.shape == f_obs.shape:
        return f_sim, f_obs

    from PIL import Image
    obs_img    = Image.fromarray(f_obs)
    obs_resamp = obs_img.resize(
        (f_sim.shape[1], f_sim.shape[0]),
        Image.NEAREST
    )
    return f_sim, np.array(obs_resamp, dtype=np.float32)


def compute_divergence(f_sim_bin: np.ndarray, f_obs_bin: np.ndarray) -> np.ndarray:
    """
    D(x,y) = F_obs(x,y) - F_sim(x,y)

     1  → sim missed it   (under-predict) → RED in 3D view
    -1  → sim over-called (over-predict)  → BLUE in 3D view
     0  → correct
    """
    D = f_obs_bin - f_sim_bin
    # mask where either grid has nodata
    mask = np.isnan(f_sim_bin) | np.isnan(f_obs_bin)
    D[mask] = np.nan
    return D


def divergence_stats(D: np.ndarray) -> dict:
    """
    Scalar metrics from divergence grid.
    """
    valid      = D[~np.isnan(D)]
    total      = len(valid)
    if total == 0:
        return {"max_divergence": 0.0, "under_predict_pct": 0.0,
                "over_predict_pct": 0.0, "correct_pct": 0.0}

    under      = np.sum(valid ==  1.0)   # sim missed
    over       = np.sum(valid == -1.0)   # sim over-called
    correct    = np.sum(valid ==  0.0)

    under_pct  = float(under)   / total
    over_pct   = float(over)    / total
    correct_pct= float(correct) / total
    max_div    = max(under_pct, over_pct)

    return {
        "max_divergence"    : round(max_div,    4),
        "under_predict_pct" : round(under_pct,  4),
        "over_predict_pct"  : round(over_pct,   4),
        "correct_pct"       : round(correct_pct,4),
        "total_cells"       : int(total),
    }


def identify_cause(stats: dict) -> str:
    """
    Heuristic — production mein ML-based hoga.
    Abhi simple rules:
      - Under-predict zyada → Manning n too high (flow too slow)
      - Over-predict zyada  → Manning n too low / rainfall over-estimated
    """
    if stats["under_predict_pct"] > stats["over_predict_pct"]:
        return "manning_n_high"   # flow resistance over-estimated
    else:
        return "manning_n_low"    # flow too fast / rainfall over


def suggest_recalibration(
    cause        : str,
    current_n    : float = 0.035,
    current_Ks   : float = 10.0,
) -> dict:
    """
    Return suggested new parameter values.
    Qt side pe in values ko directly DLL mein pass karega.
    """
    new_n  = current_n
    new_Ks = current_Ks

    if cause == "manning_n_high":
        # flow too slow → reduce resistance → water spreads more
        new_n = round(current_n - MANNING_STEP, 4)

    elif cause == "manning_n_low":
        # flow too fast → increase resistance
        new_n = round(current_n + MANNING_STEP, 4)

    # clamp to physically valid range
    new_n  = max(0.010, min(new_n,  0.150))
    new_Ks = max(0.1,   min(new_Ks, 100.0))

    return {
        "manning_n" : new_n,
        "soil_Ks"   : new_Ks,
    }


def save_divergence_geotiff(D: np.ndarray, meta: dict, out_path: str):
    """
    Divergence grid GeoTIFF save karo — Qt/OpenGL isko texture ke
    roop mein load karega 3D overlay ke liye.
    """
    driver = gdal.GetDriverByName("GTiff")
    rows, cols = D.shape
    ds_out = driver.Create(out_path, cols, rows, 1, gdal.GDT_Float32)
    ds_out.SetGeoTransform(meta["geotransform"])
    ds_out.SetProjection(meta["projection"])
    band = ds_out.GetRasterBand(1)
    band.WriteArray(D)
    band.SetNoDataValue(np.nan)
    ds_out.FlushCache()
    ds_out = None


def run(
    sim_path     : str,
    obs_path     : str,
    out_div_path : str,
    current_n    : float = 0.035,
    current_Ks   : float = 10.0,
) -> dict:
    """
    Main entry — Qt QProcess se yahi call hoga.

    Args:
        sim_path     : FloodSim output GeoTIFF path
        obs_path     : Sentinel-1 SAR flood extent GeoTIFF path
        out_div_path : where to write divergence GeoTIFF
        current_n    : current Manning n in simulation
        current_Ks   : current soil Ks in simulation

    Returns:
        JSON dict — Qt side pe parse hoga
    """

    # 1. Load
    f_sim_raw, meta = load_geotiff(sim_path)
    f_obs_raw, _    = load_geotiff(obs_path)

    # 2. Binary extent
    f_sim_bin = sim_to_binary(f_sim_raw, threshold=0.05)
    f_obs_bin = sar_to_binary(f_obs_raw)

    # 3. Align grids
    f_sim_bin, f_obs_bin = align_grids(f_sim_bin, f_obs_bin)

    # 4. Divergence
    D     = compute_divergence(f_sim_bin, f_obs_bin)
    stats = divergence_stats(D)

    # 5. Save divergence GeoTIFF for Qt 3D overlay
    save_divergence_geotiff(D, meta, out_div_path)

    # 6. Recalibration decision
    needs_recalibration = stats["max_divergence"] > DIVERGENCE_THRESHOLD
    recalib_params      = {}
    cause               = ""

    if needs_recalibration:
        cause          = identify_cause(stats)
        recalib_params = suggest_recalibration(cause, current_n, current_Ks)

    # 7. Final output — Qt JSON parse karega
    result = {
        "status"              : "ok",
        "stats"               : stats,
        "needs_recalibration" : needs_recalibration,
        "cause"               : cause,
        "recalib_params"      : recalib_params,
        "divergence_tiff"     : out_div_path,
    }

    return result


# ─── CLI entry (QProcess se aise call hoga) ───────────────
# python divergence_engine.py <sim.tif> <obs.tif> <div_out.tif> <manning_n> <Ks>
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({"status": "error", "msg": "insufficient args"}))
        sys.exit(1)

    sim_path     = sys.argv[1]
    obs_path     = sys.argv[2]
    out_div_path = sys.argv[3]
    current_n    = float(sys.argv[4]) if len(sys.argv) > 4 else 0.035
    current_Ks   = float(sys.argv[5]) if len(sys.argv) > 5 else 10.0

    try:
        result = run(sim_path, obs_path, out_div_path, current_n, current_Ks)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "msg": str(e)}))
        sys.exit(1)
"""
satellite_loader.py
-------------------
Pulls NDVI (Normalized Difference Vegetation Index) statistics per region
from Google Earth Engine (MODIS MOD13A3 product).

Requires:
    - Authenticated GEE account: `earthengine authenticate`
    - earthengine-api, geopandas, rasterio installed

Falls back to a synthetic NDVI generator when GEE is unavailable
(useful for offline development / CI).
"""

import os
import numpy as np
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)

GEE_AVAILABLE = False
try:
    import ee
    ee.Initialize()
    GEE_AVAILABLE = True
    logger.info("Google Earth Engine initialized successfully")
except Exception as e:
    logger.warning(f"GEE not available ({e}). Using synthetic NDVI fallback.")


# ──────────────────────────────────────────────────
# GEE-based NDVI extraction
# ──────────────────────────────────────────────────

def fetch_ndvi_gee(
    region_bounds: dict,          # {"xmin": float, "ymin": float, "xmax": float, "ymax": float}
    region_id: str,
    start_date: str = "2023-01-01",
    end_date: str   = "2023-12-31",
) -> pd.DataFrame:
    """
    Fetch monthly NDVI statistics for a bounding box from GEE.

    Parameters
    ----------
    region_bounds : dict  — lat/lon bounding box of the region
    region_id     : str   — identifier to attach to rows
    start_date    : str   — ISO date string
    end_date      : str   — ISO date string

    Returns
    -------
    pd.DataFrame with columns: region_id, month, ndvi_mean, ndvi_std, ndvi_trend
    """
    if not GEE_AVAILABLE:
        logger.warning("GEE unavailable — returning synthetic NDVI data")
        return _synthetic_ndvi(region_id)

    aoi = ee.Geometry.Rectangle([
        region_bounds["xmin"], region_bounds["ymin"],
        region_bounds["xmax"], region_bounds["ymax"],
    ])

    collection = (
        ee.ImageCollection("MODIS/006/MOD13A3")
        .filterDate(start_date, end_date)
        .filterBounds(aoi)
        .select("NDVI")
    )

    records = []
    for month in range(1, 13):
        monthly = collection.filter(
            ee.Filter.calendarRange(month, month, "month")
        )
        if monthly.size().getInfo() == 0:
            continue

        stats = monthly.mean().reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), "", True),
            geometry=aoi,
            scale=1000,
            maxPixels=1e8,
        ).getInfo()

        ndvi_raw_mean = stats.get("NDVI_mean", 0) or 0
        ndvi_raw_std  = stats.get("NDVI_stdDev", 0) or 0
        records.append({
            "region_id": region_id,
            "month":     month,
            "ndvi_mean": round(ndvi_raw_mean * 0.0001, 4),   # scale factor
            "ndvi_std":  round(ndvi_raw_std  * 0.0001, 4),
        })

    df = pd.DataFrame(records)
    df = _add_ndvi_trend(df)
    return df


def fetch_ndvi_batch(regions: list[dict]) -> pd.DataFrame:
    """
    Fetch NDVI for a list of regions.
    Each dict must have: region_id, xmin, ymin, xmax, ymax.
    """
    frames = []
    for r in regions:
        bounds = {k: r[k] for k in ["xmin", "ymin", "xmax", "ymax"]}
        df = fetch_ndvi_gee(bounds, r["region_id"])
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


# ──────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────

def _add_ndvi_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute NDVI trend as the slope of a simple linear regression
    over months — positive = vegetation improving, negative = degrading.
    """
    if len(df) < 2:
        df["ndvi_trend"] = 0.0
        return df

    x = df["month"].values
    y = df["ndvi_mean"].values
    slope = np.polyfit(x, y, 1)[0]
    df["ndvi_trend"] = round(slope, 6)
    return df


def _synthetic_ndvi(region_id: str) -> pd.DataFrame:
    """Deterministic synthetic NDVI for offline development."""
    np.random.seed(abs(hash(region_id)) % (2**31))
    base = np.random.uniform(0.3, 0.7)
    monthly_values = base + 0.1 * np.sin(np.linspace(0, 2 * np.pi, 12))
    records = [
        {
            "region_id": region_id,
            "month": m + 1,
            "ndvi_mean": round(float(monthly_values[m]), 4),
            "ndvi_std":  round(float(np.random.uniform(0.01, 0.05)), 4),
        }
        for m in range(12)
    ]
    df = pd.DataFrame(records)
    return _add_ndvi_trend(df)


def aggregate_annual_ndvi(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse monthly NDVI to a single row per region for model input."""
    return (
        df.groupby("region_id")
          .agg(
              ndvi_mean=("ndvi_mean", "mean"),
              ndvi_std=("ndvi_std", "mean"),
              ndvi_trend=("ndvi_trend", "first"),
              ndvi_max=("ndvi_mean", "max"),
              ndvi_min=("ndvi_mean", "min"),
          )
          .reset_index()
    )


if __name__ == "__main__":
    region = {
        "region_id": "Tamil_Nadu_Coimbatore",
        "xmin": 76.5, "ymin": 10.5,
        "xmax": 77.5, "ymax": 11.5,
    }
    df = fetch_ndvi_gee(
        {k: region[k] for k in ["xmin", "ymin", "xmax", "ymax"]},
        region["region_id"],
    )
    print(df)
    print("\nAnnual aggregation:")
    print(aggregate_annual_ndvi(df))

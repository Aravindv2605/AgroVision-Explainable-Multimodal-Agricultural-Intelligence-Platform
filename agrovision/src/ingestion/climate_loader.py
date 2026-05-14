"""
climate_loader.py
-----------------
Loads monthly rainfall, temperature, humidity, and solar radiation data.
Compatible with IMD open data CSVs or ERA5 reanalysis exports.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import load_config

logger = get_logger(__name__)

REQUIRED_COLS = ["region_id", "year", "month",
                 "rainfall_mm", "temp_max", "temp_min", "humidity"]

VALID_RANGES = {
    "rainfall_mm":      (0, 1200),
    "temp_max":         (10, 50),
    "temp_min":         (-5, 45),
    "humidity":         (0, 100),
    "solar_radiation":  (0, 30),   # MJ/m²/day
}


def load_climate_data(filepath: str = None) -> pd.DataFrame:
    """
    Load and clean climate CSV.
    Adds derived features: temp_range, is_monsoon, season.

    Returns
    -------
    pd.DataFrame — monthly climate records per region
    """
    cfg = load_config()
    if filepath is None:
        filepath = Path(cfg["paths"]["raw_data"]) / cfg["data"]["climate_file"]

    logger.info(f"Loading climate data from {filepath}")
    df = pd.read_csv(filepath)

    _check_required_cols(df)
    df = _validate_ranges(df)
    df = _add_derived_features(df)
    df = df.fillna(df.select_dtypes(include=[np.number]).median())

    logger.info(f"Climate data loaded: {df.shape[0]} records")
    return df


def _check_required_cols(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Climate data missing required columns: {missing}")


def _validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
    for col, (lo, hi) in VALID_RANGES.items():
        if col not in df.columns:
            continue
        out_of_range = ((df[col] < lo) | (df[col] > hi)).sum()
        if out_of_range:
            logger.warning(f"{out_of_range} out-of-range values in '{col}' — clamping")
            df[col] = df[col].clip(lo, hi)
    return df


def _add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add agronomically meaningful derived columns."""
    df["temp_range"] = df["temp_max"] - df["temp_min"]
    df["temp_mean"]  = (df["temp_max"] + df["temp_min"]) / 2

    # Indian monsoon months: June–September
    df["is_monsoon"] = df["month"].isin([6, 7, 8, 9]).astype(int)

    # Four agricultural seasons
    season_map = {
        12: "rabi", 1: "rabi", 2: "rabi",
        3: "zaid", 4: "zaid", 5: "zaid",
        6: "kharif", 7: "kharif", 8: "kharif", 9: "kharif",
        10: "post_kharif", 11: "post_kharif",
    }
    df["season"] = df["month"].map(season_map)

    # Cumulative annual rainfall per region-year
    df["annual_rainfall_mm"] = df.groupby(["region_id", "year"])["rainfall_mm"].transform("sum")

    return df


def aggregate_annual(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate monthly records to a single annual row per region.
    Useful for joining with soil data (which is not time-indexed).
    """
    agg_dict = {
        "rainfall_mm":       "sum",
        "temp_max":          "mean",
        "temp_min":          "mean",
        "temp_mean":         "mean",
        "humidity":          "mean",
        "solar_radiation":   "mean",
        "is_monsoon":        "sum",   # months of monsoon received
    }
    # Only aggregate columns that exist
    agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}

    annual = (
        df.groupby(["region_id", "year"])
          .agg(agg_dict)
          .reset_index()
          .rename(columns={"rainfall_mm": "annual_rainfall_mm"})
    )
    return annual


if __name__ == "__main__":
    import os, tempfile
    months = list(range(1, 13))
    synthetic = pd.DataFrame({
        "region_id":   ["R001"] * 12,
        "year":        [2023] * 12,
        "month":       months,
        "rainfall_mm": [10, 8, 15, 30, 60, 200, 250, 230, 180, 50, 20, 12],
        "temp_max":    [28, 30, 34, 37, 40, 38, 36, 35, 34, 32, 29, 27],
        "temp_min":    [18, 19, 22, 26, 30, 28, 27, 27, 26, 24, 20, 18],
        "humidity":    [60, 55, 50, 45, 55, 80, 90, 88, 82, 70, 60, 58],
    })
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        synthetic.to_csv(f, index=False)
        tmp = f.name

    df = load_climate_data(tmp)
    print(df[["region_id", "month", "season", "is_monsoon", "temp_range"]].head())
    print("\nAnnual aggregation:")
    print(aggregate_annual(df))
    os.unlink(tmp)

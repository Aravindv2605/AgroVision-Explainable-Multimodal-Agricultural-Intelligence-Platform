"""
soil_loader.py
--------------
Loads and validates soil data (NPK, pH, moisture, organic matter).
Source: CSV upload from field sensors, ISRIC API, or manual entry.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import load_config

logger = get_logger(__name__)

REQUIRED_COLS = ["region_id", "latitude", "longitude", "N", "P", "K",
                 "pH", "moisture", "organic_matter"]

VALID_RANGES = {
    "N":             (0, 150),    # kg/ha
    "P":             (0, 100),
    "K":             (0, 300),
    "pH":            (3.5, 9.5),
    "moisture":      (0, 100),    # %
    "organic_matter": (0, 10),    # %
}


def load_soil_data(filepath: str = None) -> pd.DataFrame:
    """
    Load soil CSV, validate ranges, impute minor missing values.

    Returns
    -------
    pd.DataFrame  — cleaned soil dataframe
    """
    cfg = load_config()
    if filepath is None:
        filepath = Path(cfg["paths"]["raw_data"]) / cfg["data"]["soil_file"]

    logger.info(f"Loading soil data from {filepath}")
    df = pd.read_csv(filepath)

    _check_required_cols(df)
    df = _validate_ranges(df)
    df = _impute_missing(df)

    logger.info(f"Soil data loaded: {df.shape[0]} records, {df.shape[1]} columns")
    return df


def _check_required_cols(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Soil data missing required columns: {missing}")


def _validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
    for col, (lo, hi) in VALID_RANGES.items():
        if col not in df.columns:
            continue
        out_of_range = ((df[col] < lo) | (df[col] > hi)).sum()
        if out_of_range > 0:
            logger.warning(f"{out_of_range} out-of-range values in '{col}' — clamping to [{lo}, {hi}]")
            df[col] = df[col].clip(lo, hi)
    return df


def _impute_missing(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    missing_counts = df[numeric_cols].isnull().sum()
    if missing_counts.any():
        logger.info("Imputing missing numeric values with column median")
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    return df


if __name__ == "__main__":
    # Quick smoke test with synthetic data
    import os, tempfile
    synthetic = pd.DataFrame({
        "region_id": ["R001", "R002"],
        "latitude":  [11.1, 12.5],
        "longitude": [77.5, 78.2],
        "N": [80, 55], "P": [40, 30], "K": [120, 90],
        "pH": [6.5, 7.1], "moisture": [45, 60], "organic_matter": [2.1, 1.8],
    })
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        synthetic.to_csv(f, index=False)
        tmp = f.name

    df = load_soil_data(tmp)
    print(df)
    os.unlink(tmp)

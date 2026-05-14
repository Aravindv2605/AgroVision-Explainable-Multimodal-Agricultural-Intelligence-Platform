"""
feature_engineer.py
--------------------
Merges soil, climate, NDVI, and market data into a single feature matrix
ready for model training or inference.

Pipeline:
  1. Load all data sources
  2. Aggregate to region-level (annual)
  3. Merge on region_id
  4. Compute interaction & lag features
  5. Return feature DataFrame + label column
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import load_config, save_json, ensure_dir
from src.ingestion.soil_loader import load_soil_data
from src.ingestion.climate_loader import load_climate_data, aggregate_annual
from src.ingestion.satellite_loader import fetch_ndvi_gee, aggregate_annual_ndvi
from src.ingestion.market_loader import load_market_data, compute_profit_index

logger = get_logger(__name__)


def build_feature_matrix(
    soil_file: str = None,
    climate_file: str = None,
    market_file: str = None,
    regions: list[dict] = None,
    label_file: str = None,
    save_path: str = None,
) -> pd.DataFrame:
    """
    Orchestrate all loaders and return merged feature matrix.

    Parameters
    ----------
    soil_file    : path to soil CSV
    climate_file : path to climate CSV
    market_file  : path to market prices CSV
    regions      : list of dicts with region GEE bounding boxes
    label_file   : path to CSV with region_id → crop_label ground truth
    save_path    : if provided, saves merged CSV here

    Returns
    -------
    pd.DataFrame — feature matrix (one row per region), includes 'crop_label'
    """
    cfg = load_config()

    # ── Load & aggregate each source ──────────────────────────────────────
    logger.info("Loading soil data …")
    soil_df = load_soil_data(soil_file)

    logger.info("Loading climate data …")
    climate_raw = load_climate_data(climate_file)
    climate_df  = aggregate_annual(climate_raw)

    logger.info("Loading NDVI data …")
    if regions:
        ndvi_raw = pd.concat(
            [fetch_ndvi_gee({k: r[k] for k in ["xmin","ymin","xmax","ymax"]}, r["region_id"])
             for r in regions],
            ignore_index=True,
        )
    else:
        # Use synthetic NDVI for each region found in soil data
        from src.ingestion.satellite_loader import _synthetic_ndvi
        ndvi_raw = pd.concat(
            [_synthetic_ndvi(rid) for rid in soil_df["region_id"].unique()],
            ignore_index=True,
        )
    ndvi_df = aggregate_annual_ndvi(ndvi_raw)

    logger.info("Loading market / profitability data …")
    mkt_df = compute_profit_index(load_market_data(market_file))
    # Keep only the national-level profit index (used as a feature weight)
    mkt_pivot = (
        mkt_df.groupby("crop")["profit_index"]
              .mean()
              .reset_index()
              .rename(columns={"profit_index": "market_profit_index"})
    )

    # ── Merge sources on region_id ─────────────────────────────────────────
    merged = soil_df.merge(climate_df, on="region_id", how="left")
    merged = merged.merge(ndvi_df,    on="region_id", how="left")

    # ── Interaction features ───────────────────────────────────────────────
    merged = _add_interaction_features(merged)

    # ── Load labels (ground truth crop for each region) ───────────────────
    if label_file and Path(label_file).exists():
        labels = pd.read_csv(label_file)[["region_id", "crop_label"]]
        merged = merged.merge(labels, on="region_id", how="left")
    else:
        logger.warning("No label file provided. 'crop_label' column will be absent.")

    # ── Save ───────────────────────────────────────────────────────────────
    if save_path:
        ensure_dir(str(Path(save_path).parent))
        merged.to_csv(save_path, index=False)
        logger.info(f"Feature matrix saved to {save_path}")

    logger.info(f"Feature matrix built: {merged.shape[0]} rows × {merged.shape[1]} cols")
    return merged


def _add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute agronomically meaningful interaction features."""

    # Water Stress Index: high temperature + low rainfall → stress
    if "annual_rainfall_mm" in df.columns and "temp_mean" in df.columns:
        df["water_stress_index"] = (
            df["temp_mean"] / (df["annual_rainfall_mm"].replace(0, np.nan) + 1)
        ).round(4)

    # Soil fertility composite
    if all(c in df.columns for c in ["N", "P", "K"]):
        df["fertility_score"] = (
            0.4 * _normalize(df["N"]) +
            0.3 * _normalize(df["P"]) +
            0.3 * _normalize(df["K"])
        ).round(4)

    # pH suitability (most crops prefer 5.5–7.5)
    if "pH" in df.columns:
        df["pH_suitability"] = (
            1 - (df["pH"] - 6.5).abs() / 3.0
        ).clip(0, 1).round(4)

    # Crop-water requirement proxy
    if "annual_rainfall_mm" in df.columns and "humidity" in df.columns:
        df["moisture_availability"] = (
            (df["annual_rainfall_mm"] / 1200) * 0.6 +
            (df["humidity"] / 100) * 0.4
        ).clip(0, 1).round(4)

    # NDVI × fertility interaction
    if "ndvi_mean" in df.columns and "fertility_score" in df.columns:
        df["agri_potential"] = (
            df["ndvi_mean"] * df["fertility_score"]
        ).round(4)

    return df


def _normalize(series: pd.Series) -> pd.Series:
    rng = series.max() - series.min()
    if rng == 0:
        return pd.Series(0.5, index=series.index)
    return (series - series.min()) / rng


def get_feature_columns(cfg: dict = None) -> list[str]:
    """Return the ordered list of feature columns used for model input."""
    if cfg is None:
        cfg = load_config()
    base = (
        cfg["features"]["soil_cols"] +
        cfg["features"]["climate_cols"] +
        cfg["features"]["ndvi_cols"]
    )
    derived = [
        "water_stress_index", "fertility_score",
        "pH_suitability", "moisture_availability", "agri_potential",
    ]
    return [c for c in base + derived]


if __name__ == "__main__":
    df = build_feature_matrix()
    print(df.head())
    print("\nFeature columns:", get_feature_columns())

"""
market_loader.py
----------------
Loads commodity market prices (MSP / spot prices) per crop and region.
Source: Agmarknet open data, government MSP notifications, or CSV export.

Provides:
    - load_market_data()     — load raw prices CSV
    - compute_profit_index() — merge with yield estimates for profitability score
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import load_config

logger = get_logger(__name__)

# Minimum Support Prices 2023-24 (INR per quintal) — fallback if CSV missing
DEFAULT_MSP = {
    "rice":       2183,
    "wheat":      2275,
    "maize":      2090,
    "sugarcane":  315,
    "cotton":     6620,
    "soybean":    4600,
    "groundnut":  6377,
    "black_gram": 6950,
    "turmeric":   7000,
    "onion":      800,
    "potato":     650,
    "tomato":     600,
    "banana":     1200,
    "mango":      2500,
    "coconut":    3200,
}

# Average yield (quintals/hectare) — fallback constants
AVERAGE_YIELD_QHA = {
    "rice": 26, "wheat": 35, "maize": 32, "sugarcane": 700,
    "cotton": 5, "soybean": 10, "groundnut": 12, "black_gram": 8,
    "turmeric": 45, "onion": 130, "potato": 200, "tomato": 250,
    "banana": 300, "mango": 80, "coconut": 65,
}


def load_market_data(filepath: str = None) -> pd.DataFrame:
    """
    Load market price CSV or return default MSP table if file not found.

    Expected CSV columns: crop, region_id, price_per_quintal, date
    """
    cfg = load_config()
    if filepath is None:
        filepath = Path(cfg["paths"]["raw_data"]) / cfg["data"]["market_file"]

    if not Path(filepath).exists():
        logger.warning(f"Market file not found at {filepath}. Using default MSP values.")
        return _build_default_market_df()

    logger.info(f"Loading market data from {filepath}")
    df = pd.read_csv(filepath, parse_dates=["date"])
    df = df.dropna(subset=["crop", "price_per_quintal"])

    # Use latest available price per crop
    df = (
        df.sort_values("date")
          .groupby(["crop", "region_id"])
          .last()
          .reset_index()
    )
    logger.info(f"Market data loaded: {df.shape[0]} records")
    return df


def _build_default_market_df() -> pd.DataFrame:
    """Build a simple crop → price dataframe from hardcoded MSP constants."""
    rows = [
        {"crop": crop, "region_id": "national", "price_per_quintal": price}
        for crop, price in DEFAULT_MSP.items()
    ]
    return pd.DataFrame(rows)


def compute_profit_index(
    market_df: pd.DataFrame,
    input_cost_per_ha: dict = None,
) -> pd.DataFrame:
    """
    Compute a profitability score per crop:
        profit_inr_per_ha = (price_per_quintal × yield_q_per_ha) - input_cost

    Parameters
    ----------
    market_df         : output of load_market_data()
    input_cost_per_ha : optional dict of {crop: INR/ha input cost}

    Returns
    -------
    pd.DataFrame with profit_inr_per_ha, profit_index (0–1 scaled)
    """
    default_costs = {c: 25000 for c in DEFAULT_MSP}  # ~INR 25k/ha default
    costs = {**default_costs, **(input_cost_per_ha or {})}

    market_df = market_df.copy()
    market_df["yield_q_per_ha"] = market_df["crop"].map(AVERAGE_YIELD_QHA).fillna(20)
    market_df["input_cost_inr"] = market_df["crop"].map(costs).fillna(25000)
    market_df["profit_inr_per_ha"] = (
        market_df["price_per_quintal"] * market_df["yield_q_per_ha"]
        - market_df["input_cost_inr"]
    )

    # Normalize to 0–1 for use as a model feature
    min_p = market_df["profit_inr_per_ha"].min()
    max_p = market_df["profit_inr_per_ha"].max()
    market_df["profit_index"] = (
        (market_df["profit_inr_per_ha"] - min_p) / (max_p - min_p + 1e-9)
    ).round(4)

    return market_df.sort_values("profit_inr_per_ha", ascending=False)


if __name__ == "__main__":
    mkt = load_market_data()
    result = compute_profit_index(mkt)
    print(result[["crop", "price_per_quintal", "yield_q_per_ha",
                  "profit_inr_per_ha", "profit_index"]].to_string(index=False))

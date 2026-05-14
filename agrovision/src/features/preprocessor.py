"""
preprocessor.py
---------------
Handles:
    - Feature selection from merged matrix
    - Label encoding of crop names
    - Standard scaling of numeric features
    - Train / validation / test split
    - Saving & loading fitted transformers (for inference)
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder

from src.utils.logger import get_logger
from src.utils.helpers import load_config, ensure_dir, save_json

logger = get_logger(__name__)


class AgroPreprocessor:
    """Stateful preprocessor: fit on training data, transform inference data."""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.cfg = load_config(config_path)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_cols: list[str] = []
        self._fitted = False

    # ── Public API ─────────────────────────────────────────────────────────

    def fit_transform(self, df: pd.DataFrame):
        """
        Fit on full dataframe and return train/val/test splits as numpy arrays.

        Returns
        -------
        X_train, X_val, X_test, y_train, y_val, y_test
        """
        target = self.cfg["data"]["target_column"]
        if target not in df.columns:
            raise ValueError(f"Target column '{target}' not found in dataframe")

        self.feature_cols = self._resolve_feature_cols(df)
        logger.info(f"Using {len(self.feature_cols)} feature columns")

        X = df[self.feature_cols].values
        y_raw = df[target].values

        # Fit encoders
        X_scaled = self.scaler.fit_transform(X)
        y_encoded = self.label_encoder.fit_transform(y_raw)
        # Remap to continuous 0..N-1 to avoid XGBoost gaps
        from sklearn.preprocessing import LabelEncoder as LE
        self._remap = LE()
        y_encoded = self._remap.fit_transform(y_encoded)
        self._fitted = True

        logger.info(f"Classes: {list(self.label_encoder.classes_)}")
        save_json(
            {"classes": list(self.label_encoder.classes_),
             "n_features": len(self.feature_cols),
             "feature_cols": self.feature_cols},
            self.cfg["paths"]["model_artifacts"] + "metadata.json",
        )

        # Split: 70% train, 15% val, 15% test
        seed = self.cfg["data"]["random_seed"]

        # Disable stratify if any class has fewer than 2 samples
        from collections import Counter
        min_count = min(Counter(y_encoded).values())
        use_stratify = min_count >= 2
        if not use_stratify:
            logger.warning("Some classes have only 1 sample - disabling stratify.")

        X_tr, X_tmp, y_tr, y_tmp = train_test_split(
            X_scaled, y_encoded, test_size=0.30, random_state=seed,
            stratify=y_encoded if use_stratify else None
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_tmp, y_tmp, test_size=0.50, random_state=seed,
            stratify=y_tmp if use_stratify else None
        )

        logger.info(
            f"Split → train: {len(X_tr)}, val: {len(X_val)}, test: {len(X_test)}"
        )
        return X_tr, X_val, X_test, y_tr, y_val, y_test

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform new inference data using fitted scaler."""
        if not self._fitted:
            raise RuntimeError("Preprocessor must be fitted before calling transform()")
        X = df[self.feature_cols].values
        return self.scaler.transform(X)

    def decode_labels(self, y_encoded: np.ndarray) -> list[str]:
        """Convert integer predictions back to crop names."""
        if hasattr(self, '_remap'):
            y_encoded = self._remap.inverse_transform(y_encoded)
        return list(self.label_encoder.inverse_transform(y_encoded))

    def save(self, dir_path: str = None):
        """Persist fitted scaler and label encoder to disk."""
        dir_path = dir_path or self.cfg["paths"]["model_artifacts"]
        ensure_dir(dir_path)
        joblib.dump(self.scaler,        Path(dir_path) / "scaler.joblib")
        joblib.dump(self.label_encoder, Path(dir_path) / "label_encoder.joblib")
        logger.info(f"Preprocessor artifacts saved to {dir_path}")

    @classmethod
    def load(cls, dir_path: str, config_path: str = "config/config.yaml"):
        """Load a previously fitted preprocessor from disk."""
        obj = cls(config_path)
        obj.scaler        = joblib.load(Path(dir_path) / "scaler.joblib")
        obj.label_encoder = joblib.load(Path(dir_path) / "label_encoder.joblib")

        from src.utils.helpers import load_json
        meta = load_json(str(Path(dir_path) / "metadata.json"))
        obj.feature_cols  = meta["feature_cols"]
        obj._fitted = True
        logger.info(f"Preprocessor loaded from {dir_path}")
        return obj

    # ── Private ────────────────────────────────────────────────────────────

    def _resolve_feature_cols(self, df: pd.DataFrame) -> list[str]:
        """
        Build the final feature column list from config + derived columns,
        keeping only those present in the actual dataframe.
        """
        from src.features.feature_engineer import get_feature_columns
        candidates = get_feature_columns(self.cfg)
        available = [c for c in candidates if c in df.columns]
        dropped = set(candidates) - set(available)
        if dropped:
            logger.warning(f"Dropping missing feature columns: {dropped}")
        return available

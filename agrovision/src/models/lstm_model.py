"""
lstm_model.py
-------------
LSTM-based model for seasonal crop suitability prediction.
Takes a sequence of monthly climate + NDVI readings and predicts crop probabilities.

Input shape : (n_samples, sequence_length=12, n_features)
Output shape: (n_samples, n_classes)
"""

import numpy as np
import joblib
from pathlib import Path

from src.utils.logger import get_logger
from src.utils.helpers import load_config, ensure_dir

logger = get_logger(__name__)

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not installed. LSTMCropModel will be unavailable.")


def build_sequences(
    df,
    region_col: str,
    time_col: str,
    feature_cols: list[str],
    label_col: str,
    seq_len: int = 12,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert a monthly time-series dataframe to overlapping sequences.

    Returns
    -------
    X : (n_samples, seq_len, n_features)
    y : (n_samples,) — integer labels
    """
    import pandas as pd
    from sklearn.preprocessing import LabelEncoder

    le = LabelEncoder()
    df = df.sort_values([region_col, time_col])
    X_list, y_list = [], []

    for region, grp in df.groupby(region_col):
        feat = grp[feature_cols].values
        labs = grp[label_col].values
        for i in range(len(feat) - seq_len):
            X_list.append(feat[i : i + seq_len])
            y_list.append(labs[i + seq_len])

    X = np.array(X_list, dtype=np.float32)
    y = le.fit_transform(y_list)
    return X, y


class LSTMCropModel:

    def __init__(self, n_features: int, n_classes: int,
                 config_path: str = "config/config.yaml"):
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTMCropModel")

        self.cfg = load_config(config_path)
        lp = self.cfg["lstm"]
        self.seq_len   = lp["sequence_length"]
        self.n_features = n_features
        self.n_classes  = n_classes
        self.model = self._build(lp)
        self._trained = False

    def _build(self, lp: dict) -> "Sequential":
        model = Sequential([
            LSTM(lp["hidden_units"], return_sequences=True,
                 input_shape=(self.seq_len, self.n_features)),
            BatchNormalization(),
            Dropout(lp["dropout_rate"]),

            LSTM(lp["hidden_units"] // 2, return_sequences=False),
            BatchNormalization(),
            Dropout(lp["dropout_rate"]),

            Dense(64, activation="relu"),
            Dense(self.n_classes, activation="softmax"),
        ])
        model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        model.summary(print_fn=logger.info)
        return model

    def train(self, X_train, y_train, X_val, y_val) -> dict:
        lp = self.cfg["lstm"]
        model_dir = self.cfg["paths"]["model_artifacts"]
        ensure_dir(model_dir)

        callbacks = [
            EarlyStopping(patience=8, restore_best_weights=True, verbose=1),
            ModelCheckpoint(Path(model_dir) / "lstm_best.keras",
                            save_best_only=True, verbose=0),
            ReduceLROnPlateau(factor=0.5, patience=4, verbose=1),
        ]

        logger.info("Training LSTM model …")
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=lp["epochs"],
            batch_size=lp["batch_size"],
            callbacks=callbacks,
            verbose=1,
        )
        self._trained = True

        best_val_acc = max(history.history["val_accuracy"])
        logger.info(f"LSTM best val accuracy: {best_val_acc:.4f}")
        return {"best_val_accuracy": best_val_acc}

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return softmax probabilities (n_samples × n_classes)."""
        self._require_trained()
        return self.model.predict(X, verbose=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

    def save(self, dir_path: str = None):
        dir_path = dir_path or self.cfg["paths"]["model_artifacts"]
        ensure_dir(dir_path)
        self.model.save(Path(dir_path) / "lstm_model.keras")
        logger.info(f"LSTM model saved to {dir_path}/lstm_model.keras")

    @classmethod
    def load(cls, dir_path: str, n_features: int, n_classes: int,
             config_path: str = "config/config.yaml"):
        obj = cls.__new__(cls)
        obj.cfg = load_config(config_path)
        obj.seq_len    = obj.cfg["lstm"]["sequence_length"]
        obj.n_features = n_features
        obj.n_classes  = n_classes
        obj.model = load_model(Path(dir_path) / "lstm_model.keras")
        obj._trained = True
        logger.info("LSTM model loaded")
        return obj

    def _require_trained(self):
        if not self._trained:
            raise RuntimeError("LSTM model must be trained or loaded before inference.")

"""
trainer.py
----------
Unified training script. Run this to:
    1. Build the feature matrix from raw data
    2. Preprocess & split
    3. Train XGBoost
    4. Train LSTM (optional)
    5. Save all artifacts
    6. Print evaluation summary

Usage:
    python src/models/trainer.py
"""

import json
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import load_config, save_json, ensure_dir
from src.features.feature_engineer import build_feature_matrix
from src.features.preprocessor import AgroPreprocessor
from src.models.xgb_model import XGBCropModel
from src.ingestion.market_loader import load_market_data, compute_profit_index

logger = get_logger(__name__, log_file="outputs/training.log")


def train_pipeline(config_path: str = "config/config.yaml"):
    cfg = load_config(config_path)
    model_dir = cfg["paths"]["model_artifacts"]
    ensure_dir(model_dir)

    # ── 1. Feature matrix ──────────────────────────────────────────────────
    logger.info("=" * 50)
    logger.info("STEP 1 - Building feature matrix")
    feature_df = build_feature_matrix(
        save_path=cfg["paths"]["processed_data"] + "features.csv",
        label_file=cfg["paths"]["raw_data"] + "labels.csv",
    )

    if cfg["data"]["target_column"] not in feature_df.columns:
        logger.error("No target labels found. Cannot train. "
                     "Provide a label_file with region_id -> crop_label mapping.")
        return

    # ── 2. Preprocess ──────────────────────────────────────────────────────
    logger.info("=" * 50)
    logger.info("STEP 2 - Preprocessing & splitting")
    preprocessor = AgroPreprocessor(config_path)
    X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.fit_transform(feature_df)
    preprocessor.save(model_dir)
    class_names = list(preprocessor.label_encoder.classes_)

    # ── 3. XGBoost ─────────────────────────────────────────────────────────
    logger.info("=" * 50)
    logger.info("STEP 3 - Training XGBoost")
    xgb = XGBCropModel(config_path)
    xgb_metrics = xgb.train(X_train, y_train, X_val, y_val)
    xgb_eval    = xgb.evaluate(X_test, y_test, class_names)
    xgb.save(model_dir)

    fi = xgb.feature_importance(preprocessor.feature_cols)
    logger.info("Top 5 features: " + str(list(fi.items())[:5]))

    # ── 4. LSTM (optional) ─────────────────────────────────────────────────
    lstm_eval = {}
    try:
        from src.models.lstm_model import LSTMCropModel
        logger.info("=" * 50)
        logger.info("STEP 4 - Training LSTM")
        n_features = X_train.shape[1]
        n_classes  = len(class_names)
        lstm = LSTMCropModel(n_features, n_classes, config_path)
        # Reshape for LSTM: add a fake time dimension (seq_len=1 for tabular)
        import numpy as np
        X_tr_seq  = X_train[:, np.newaxis, :]
        X_val_seq = X_val[:, np.newaxis, :]
        lstm_metrics = lstm.train(X_tr_seq, y_train, X_val_seq, y_val)
        lstm.save(model_dir)
        lstm_eval = lstm_metrics
    except Exception as e:
        logger.warning(f"LSTM training skipped: {e}")

    # ── 5. Save summary ────────────────────────────────────────────────────
    summary = {
        "xgb": {**xgb_metrics, "test_accuracy": xgb_eval["test_accuracy"]},
        "lstm": lstm_eval,
        "classes": class_names,
        "n_features": len(preprocessor.feature_cols),
        "feature_importance_top10": dict(list(fi.items())[:10]),
    }
    save_json(summary, Path(model_dir) / "training_summary.json")
    logger.info("=" * 50)
    logger.info("Training complete.")
    logger.info(f"XGBoost test accuracy : {xgb_eval['test_accuracy']:.4f}")
    logger.info(f"Artifacts saved to    : {model_dir}")
    return summary


if __name__ == "__main__":
    train_pipeline()

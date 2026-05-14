"""
xgb_model.py
-------------
XGBoost multi-class classifier for crop suitability.
Predicts probability of each crop class given soil + climate + NDVI features.
"""

import numpy as np
import joblib
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report

from src.utils.logger import get_logger
from src.utils.helpers import load_config, ensure_dir

logger = get_logger(__name__)


class XGBCropModel:

    def __init__(self, config_path: str = "config/config.yaml"):
        self.cfg = load_config(config_path)
        xgb_params = self.cfg["xgboost"]
        self.model = XGBClassifier(
            n_estimators=xgb_params["n_estimators"],
            max_depth=xgb_params["max_depth"],
            learning_rate=xgb_params["learning_rate"],
            subsample=xgb_params["subsample"],
            colsample_bytree=xgb_params["colsample_bytree"],
            eval_metric=xgb_params["eval_metric"],
            use_label_encoder=False,
            random_state=self.cfg["data"]["random_seed"],
            n_jobs=-1,
        )
        self._trained = False

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ) -> dict:
        """
        Train with early stopping on validation set.

        Returns
        -------
        dict — training metrics
        """
        logger.info("Training XGBoost model …")
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=50,
        )
        self._trained = True

        train_acc = accuracy_score(y_train, self.model.predict(X_train))
        val_acc   = accuracy_score(y_val,   self.model.predict(X_val))
        logger.info(f"XGB train accuracy: {train_acc:.4f} | val accuracy: {val_acc:.4f}")
        return {"train_accuracy": train_acc, "val_accuracy": val_acc}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return predicted class indices."""
        self._require_trained()
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return probability matrix (n_samples × n_classes)."""
        self._require_trained()
        return self.model.predict_proba(X)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray, class_names: list) -> dict:
        """Full evaluation on held-out test set."""
        self._require_trained()
        preds = self.predict(X_test)
        report = classification_report(y_test, preds,
                                       target_names=class_names, output_dict=True)
        acc = accuracy_score(y_test, preds)
        logger.info(f"XGB test accuracy: {acc:.4f}")
        return {"test_accuracy": acc, "classification_report": report}

    def feature_importance(self, feature_names: list[str]) -> dict:
        """Return feature importances as a sorted dict."""
        self._require_trained()
        importances = self.model.feature_importances_
        return dict(
            sorted(
                zip(feature_names, importances.tolist()),
                key=lambda x: x[1],
                reverse=True,
            )
        )

    def save(self, dir_path: str = None):
        dir_path = dir_path or self.cfg["paths"]["model_artifacts"]
        ensure_dir(dir_path)
        joblib.dump(self.model, Path(dir_path) / "xgb_model.joblib")
        logger.info(f"XGBoost model saved to {dir_path}/xgb_model.joblib")

    @classmethod
    def load(cls, dir_path: str, config_path: str = "config/config.yaml"):
        obj = cls(config_path)
        obj.model = joblib.load(Path(dir_path) / "xgb_model.joblib")
        obj._trained = True
        logger.info("XGBoost model loaded")
        return obj

    def _require_trained(self):
        if not self._trained:
            raise RuntimeError("Model must be trained or loaded before inference.")

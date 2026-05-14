"""
shap_explainer.py
-----------------
Generates SHAP (SHapley Additive exPlanations) values for crop recommendations.

Provides:
    - per-sample force plots (why was THIS crop recommended?)
    - global summary plots (which features matter most overall?)
    - natural-language explanation strings for the API response
"""

import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import ensure_dir

logger = get_logger(__name__)

# Human-readable descriptions for each feature
FEATURE_DESCRIPTIONS = {
    "N":                    "Nitrogen content",
    "P":                    "Phosphorus content",
    "K":                    "Potassium content",
    "pH":                   "Soil pH level",
    "moisture":             "Soil moisture",
    "organic_matter":       "Organic matter content",
    "annual_rainfall_mm":   "Annual rainfall",
    "temp_max":             "Maximum temperature",
    "temp_min":             "Minimum temperature",
    "temp_mean":            "Average temperature",
    "humidity":             "Relative humidity",
    "solar_radiation":      "Solar radiation",
    "ndvi_mean":            "Vegetation index (NDVI)",
    "ndvi_std":             "NDVI variability",
    "ndvi_trend":           "Vegetation trend",
    "water_stress_index":   "Water stress index",
    "fertility_score":      "Soil fertility score",
    "pH_suitability":       "pH suitability score",
    "moisture_availability":"Moisture availability",
    "agri_potential":       "Agricultural potential",
}


class SHAPExplainer:

    def __init__(self, xgb_model, feature_names: list[str],
                 class_names: list[str], background_data: np.ndarray = None):
        """
        Parameters
        ----------
        xgb_model       : trained XGBCropModel instance
        feature_names   : list of feature column names
        class_names     : list of crop class names
        background_data : subset of X_train for TreeExplainer background
        """
        self.feature_names = feature_names
        self.class_names   = class_names
        logger.info("Initializing SHAP TreeExplainer …")
        self.explainer = shap.TreeExplainer(
            xgb_model.model,
            data=background_data,
            feature_names=feature_names,
        )
        self._shap_values_cache = {}

    def explain_sample(self, X: np.ndarray, class_idx: int = None) -> dict:
        """
        Compute SHAP values for a single sample.

        Parameters
        ----------
        X         : (1, n_features) scaled input array
        class_idx : which class to explain (default: argmax / top prediction)

        Returns
        -------
        dict with top positive/negative drivers and natural-language explanation
        """
        shap_vals = self.explainer.shap_values(X)   # list of arrays [n_classes]

        if class_idx is None:
            class_idx = int(np.argmax([sv[0].sum() for sv in shap_vals]))

        vals = shap_vals[class_idx][0]               # (n_features,)
        crop_name = self.class_names[class_idx]

        # Build feature → SHAP contribution mapping
        contributions = {f: round(float(v), 5)
                         for f, v in zip(self.feature_names, vals)}
        sorted_contrib = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)

        top_positive = [(f, v) for f, v in sorted_contrib if v > 0][:3]
        top_negative = [(f, v) for f, v in sorted_contrib if v < 0][:2]

        explanation_text = self._build_explanation(
            crop_name, top_positive, top_negative, X[0]
        )

        return {
            "crop":            crop_name,
            "class_idx":       class_idx,
            "shap_values":     contributions,
            "top_drivers":     [{"feature": f, "impact": v,
                                  "description": FEATURE_DESCRIPTIONS.get(f, f)}
                                 for f, v in top_positive],
            "top_suppressors": [{"feature": f, "impact": v,
                                  "description": FEATURE_DESCRIPTIONS.get(f, f)}
                                 for f, v in top_negative],
            "explanation":     explanation_text,
        }

    def _build_explanation(
        self,
        crop: str,
        positives: list,
        negatives: list,
        x_raw: np.ndarray,
    ) -> str:
        """Generate a farmer-friendly explanation string."""
        lines = [f"✅ {crop.replace('_', ' ').title()} is recommended because:"]
        for feat, val in positives:
            desc = FEATURE_DESCRIPTIONS.get(feat, feat)
            lines.append(f"  • Your {desc} strongly supports this crop (+{val:.3f})")

        if negatives:
            lines.append(f"\n⚠️  Minor limiting factors:")
            for feat, val in negatives:
                desc = FEATURE_DESCRIPTIONS.get(feat, feat)
                lines.append(f"  • {desc} slightly reduces suitability ({val:.3f})")

        return "\n".join(lines)

    def global_summary_plot(
        self,
        X: np.ndarray,
        class_idx: int = 0,
        save_path: str = "outputs/reports/shap_summary.png",
    ):
        """Generate and save a global SHAP summary plot."""
        ensure_dir(str(Path(save_path).parent))
        shap_vals = self.explainer.shap_values(X)
        plt.figure(figsize=(10, 6))
        shap.summary_plot(
            shap_vals[class_idx],
            X,
            feature_names=self.feature_names,
            show=False,
            plot_type="bar",
        )
        plt.title(f"Feature Importance — {self.class_names[class_idx]}")
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
        logger.info(f"SHAP summary plot saved to {save_path}")

    def force_plot_html(
        self,
        X: np.ndarray,
        class_idx: int,
        save_path: str = "outputs/reports/shap_force.html",
    ) -> str:
        """Generate an interactive SHAP force plot as HTML."""
        ensure_dir(str(Path(save_path).parent))
        shap_vals = self.explainer.shap_values(X)
        expected  = self.explainer.expected_value[class_idx]

        shap.initjs()
        plot = shap.force_plot(
            expected,
            shap_vals[class_idx][0],
            X[0],
            feature_names=self.feature_names,
            matplotlib=False,
        )
        shap.save_html(save_path, plot)
        logger.info(f"Force plot saved to {save_path}")
        return save_path

"""
ensemble.py
-----------
Fuses XGBoost and LSTM predictions into a final ranked crop recommendation.

Strategy:
    final_score[crop] = α × xgb_prob[crop]
                      + β × lstm_prob[crop]
                      + γ × market_profit_index[crop]

α, β, γ are configurable weights (default: 0.45, 0.35, 0.20).
The output is a ranked list of (crop, confidence_score, profit_estimate).
"""

import numpy as np
import pandas as pd
from src.utils.logger import get_logger
from src.utils.helpers import load_config

logger = get_logger(__name__)

# Default ensemble weights
ALPHA = 0.55   # XGBoost weight (Suitability)
BETA  = 0.35   # LSTM weight (Sequential/Climate trends)
GAMMA = 0.10   # Market profit weight (Economic impact)


class CropEnsemble:

    def __init__(
        self,
        xgb_model,
        lstm_model,
        class_names: list[str],
        market_profit_index: dict[str, float],
        alpha: float = ALPHA,
        beta: float  = BETA,
        gamma: float = GAMMA,
    ):
        """
        Parameters
        ----------
        xgb_model           : trained XGBCropModel instance
        lstm_model          : trained LSTMCropModel instance (or None)
        class_names         : list of crop names ordered by class index
        market_profit_index : dict {crop_name: 0–1 profit score}
        alpha, beta, gamma  : blending weights (must sum to ≈1)
        """
        self.xgb   = xgb_model
        self.lstm  = lstm_model
        self.names = class_names
        self.mpi   = market_profit_index
        self.alpha = alpha
        self.beta  = beta if lstm_model is not None else 0.0
        self.gamma = gamma
        self._renormalize_weights()

    def _renormalize_weights(self):
        total = self.alpha + self.beta + self.gamma
        self.alpha /= total
        self.beta  /= total
        self.gamma /= total

    def predict_top_k(
        self,
        X_tabular: np.ndarray,
        X_sequence: np.ndarray = None,
        k: int = 5,
    ) -> list[dict]:
        """
        Return the top-k crops ranked by ensemble score.

        Parameters
        ----------
        X_tabular  : (1, n_features) scaled feature vector for XGB
        X_sequence : (1, seq_len, n_seq_features) for LSTM — optional
        k          : number of top crops to return

        Returns
        -------
        list of dicts: [
            {"rank": 1, "crop": "rice", "score": 0.82,
             "profit_index": 0.74, "drivers": {...}},
            ...
        ]
        """
        # XGB probabilities
        xgb_proba = self.xgb.predict_proba(X_tabular)[0]          # (n_classes,)

        # LSTM probabilities (if available)
        if self.lstm is not None and X_sequence is not None:
            lstm_proba = self.lstm.predict_proba(X_sequence)[0]
        else:
            lstm_proba = np.zeros(len(self.names))

        # Market profit index vector (aligned to class_names order)
        mpi_vec = np.array([self.mpi.get(c, 0.5) for c in self.names])

        # Weighted ensemble
        ensemble_score = (
            self.alpha * xgb_proba +
            self.beta  * lstm_proba +
            self.gamma * mpi_vec
        )

        # Rank
        top_indices = np.argsort(ensemble_score)[::-1][:k]
        results = []
        for rank, idx in enumerate(top_indices, start=1):
            results.append({
                "rank":         rank,
                "crop":         self.names[idx],
                "score":        round(float(ensemble_score[idx]), 4),
                "xgb_prob":     round(float(xgb_proba[idx]), 4),
                "lstm_prob":    round(float(lstm_proba[idx]), 4),
                "profit_index": round(float(mpi_vec[idx]), 4),
            })

        logger.info(f"Top recommendation: {results[0]['crop']} (score={results[0]['score']})")
        return results

    def to_dataframe(self, predictions: list[dict]) -> pd.DataFrame:
        return pd.DataFrame(predictions)

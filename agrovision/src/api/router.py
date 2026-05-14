"""
router.py
---------
FastAPI route handlers for:
    POST /predict   — return top-K crop recommendations
    POST /explain   — return SHAP explanation for a prediction
    GET  /health    — liveness / readiness check
"""

import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from src.api.schemas import (
    PredictRequest, PredictResponse, CropRecommendation,
    ExplainResponse, DriverDetail, HealthResponse,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _build_feature_vector(req: PredictRequest, preprocessor) -> np.ndarray:
    """Assemble a raw feature dict from the request and run the preprocessor."""
    import pandas as pd

    raw = {
        "N":              req.soil.N,
        "P":              req.soil.P,
        "K":              req.soil.K,
        "pH":             req.soil.pH,
        "moisture":       req.soil.moisture,
        "organic_matter": req.soil.organic_matter,
        "annual_rainfall_mm": req.climate.annual_rainfall_mm,
        "temp_max":       req.climate.temp_max,
        "temp_min":       req.climate.temp_min,
        "humidity":       req.climate.humidity,
        "solar_radiation":req.climate.solar_radiation if req.climate.solar_radiation is not None else 15.0,
        "ndvi_mean":      req.ndvi_mean if req.ndvi_mean is not None else 0.45,
        "ndvi_std":       0.05,
        "ndvi_trend":     0.0,
    }

    # Derived features (mirror feature_engineer.py logic)
    raw["temp_mean"]            = (raw["temp_max"] + raw["temp_min"]) / 2
    raw["temp_range"]           = raw["temp_max"] - raw["temp_min"]
    raw["water_stress_index"]   = raw["temp_mean"] / (raw["annual_rainfall_mm"] + 1)
    raw["fertility_score"]      = round(
        0.4 * min(raw["N"] / 150, 1) +
        0.3 * min(raw["P"] / 100, 1) +
        0.3 * min(raw["K"] / 300, 1), 4
    )
    raw["pH_suitability"]       = round(max(0, 1 - abs(raw["pH"] - 6.5) / 3.0), 4)
    raw["moisture_availability"]= round(
        min(raw["annual_rainfall_mm"] / 1200, 1) * 0.6 +
        (raw["humidity"] / 100) * 0.4, 4
    )
    raw["agri_potential"]       = round(raw["ndvi_mean"] * raw["fertility_score"], 4)

    df = pd.DataFrame([raw])
    return preprocessor.transform(df)


# ── Dependency: load app state from FastAPI app ────────────────────────────

def get_app_state(request):
    return request.app.state


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    return HealthResponse(
        status="ok",
        models_loaded=True,
        version="1.0.0",
    )


@router.post("/predict", response_model=PredictResponse, tags=["Inference"])
async def predict(req: PredictRequest, request=None):
    """
    Given soil, climate and location data, return ranked crop recommendations.
    """
    try:
        from src.api.main import app
        state = app.state
        X = _build_feature_vector(req, state.preprocessor)
        top_k = state.ensemble.predict_top_k(X, k=req.top_k)

        recs = [
            CropRecommendation(
                rank=r["rank"],
                crop=r["crop"],
                score=r["score"],
                profit_index=r["profit_index"],
                xgb_prob=r["xgb_prob"],
            )
            for r in top_k
        ]
        return PredictResponse(region_id=req.region_id, recommendations=recs)

    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain", response_model=ExplainResponse, tags=["Explainability"])
async def explain(req: PredictRequest):
    """
    Return a SHAP-based explanation for why the top crop was recommended.
    """
    try:
        from src.api.main import app
        state = app.state
        X = _build_feature_vector(req, state.preprocessor)
        top_crop = state.ensemble.predict_top_k(X, k=1)[0]
        class_idx = state.preprocessor.label_encoder.transform([top_crop["crop"]])[0]

        explanation = state.explainer.explain_sample(X, class_idx=int(class_idx))

        return ExplainResponse(
            region_id=req.region_id,
            crop=top_crop["crop"],
            explanation=explanation["explanation"],
            top_drivers=[DriverDetail(**d) for d in explanation["top_drivers"]],
            top_suppressors=[DriverDetail(**d) for d in explanation["top_suppressors"]],
        )
    except Exception as e:
        logger.error(f"Explain error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

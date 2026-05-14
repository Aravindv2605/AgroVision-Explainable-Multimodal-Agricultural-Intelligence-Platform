"""
main.py
-------
FastAPI application entry point.
Loads all model artifacts on startup via lifespan context manager.

Run:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from src.utils.logger import get_logger
from src.utils.helpers import load_config, load_json
from src.api.router import router
from src.api.assistant_router import assistant_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models once at startup, release on shutdown."""
    logger.info("AgroVision API starting …")
    cfg = load_config()
    model_dir = cfg["paths"]["model_artifacts"]

    # ── Load preprocessor ──────────────────────────────────────────────────
    from src.features.preprocessor import AgroPreprocessor
    app.state.preprocessor = AgroPreprocessor.load(model_dir)
    class_names = list(app.state.preprocessor.label_encoder.classes_)

    # ── Load XGBoost ───────────────────────────────────────────────────────
    from src.models.xgb_model import XGBCropModel
    app.state.xgb = XGBCropModel.load(model_dir)

    # ── Load LSTM (optional) ───────────────────────────────────────────────
    try:
        from src.models.lstm_model import LSTMCropModel
        meta = load_json(str(Path(model_dir) / "metadata.json"))
        app.state.lstm = LSTMCropModel.load(
            model_dir,
            n_features=meta["n_features"],
            n_classes=len(class_names),
        )
    except Exception as e:
        logger.warning(f"LSTM not loaded: {e}. Running XGB-only ensemble.")
        app.state.lstm = None

    # ── Market profit index ────────────────────────────────────────────────
    from src.ingestion.market_loader import load_market_data, compute_profit_index
    mkt = compute_profit_index(load_market_data())
    mpi = dict(zip(mkt["crop"], mkt["profit_index"]))

    # ── Ensemble ───────────────────────────────────────────────────────────
    from src.models.ensemble import CropEnsemble
    app.state.ensemble = CropEnsemble(
        xgb_model=app.state.xgb,
        lstm_model=app.state.lstm,
        class_names=class_names,
        market_profit_index=mpi,
    )

    # ── SHAP explainer ─────────────────────────────────────────────────────
    from src.explainability.shap_explainer import SHAPExplainer
    feature_cols = app.state.preprocessor.feature_cols
    app.state.explainer = SHAPExplainer(
        xgb_model=app.state.xgb,
        feature_names=feature_cols,
        class_names=class_names,
    )

    logger.info(f"All models loaded. Classes: {class_names}")
    yield

    logger.info("AgroVision API shutting down.")


# ── App factory ────────────────────────────────────────────────────────────

app = FastAPI(
    title="AgroVision API",
    description=(
        "AI-powered smart crop recommendation engine. "
        "Combines soil, climate, satellite and market data with "
        "XGBoost + LSTM ensemble and SHAP explainability."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(assistant_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    cfg = load_config()
    uvicorn.run(
        "src.api.main:app",
        host=cfg["api"]["host"],
        port=cfg["api"]["port"],
        reload=True,
    )

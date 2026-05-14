# AgroVision — Smart Crop Intelligence Platform

An AI-powered system that fuses soil, climate, satellite, and market data to recommend
the most profitable and sustainable crops for any region — with full explainability via SHAP.

## Project Structure

```
agrovision/
├── config/
│   ├── config.yaml              # Global settings (paths, model params, API keys)
│   └── logging.yaml             # Logging configuration
├── data/
│   ├── raw/                     # Raw CSVs from APIs / sensors
│   ├── processed/               # Cleaned, merged, feature-engineered data
│   └── satellite/               # GeoTIFF NDVI raster files
├── src/
│   ├── ingestion/
│   │   ├── soil_loader.py       # Load & validate soil NPK/pH data
│   │   ├── climate_loader.py    # IMD / ERA5 rainfall & temperature ingestion
│   │   ├── satellite_loader.py  # Google Earth Engine NDVI puller
│   │   └── market_loader.py     # Agmarknet / commodity price scraper
│   ├── features/
│   │   ├── feature_engineer.py  # Merge all sources, create lag/season features
│   │   └── preprocessor.py      # Scaling, encoding, train/val split
│   ├── models/
│   │   ├── xgb_model.py         # XGBoost crop suitability classifier
│   │   ├── lstm_model.py        # LSTM for seasonal time-series forecasting
│   │   ├── ensemble.py          # Fuse XGB + LSTM → profitability score
│   │   └── trainer.py           # Unified training orchestrator
│   ├── explainability/
│   │   └── shap_explainer.py    # SHAP values, force plots, summary plots
│   ├── api/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── schemas.py           # Pydantic request/response models
│   │   └── router.py            # /predict, /explain, /health endpoints
│   └── utils/
│       ├── logger.py            # Centralized logger setup
│       └── helpers.py           # Shared utility functions
├── notebooks/
│   ├── 01_eda.ipynb             # Exploratory data analysis
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_evaluation.ipynb
├── tests/
│   ├── test_ingestion.py
│   ├── test_features.py
│   └── test_api.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Quickstart

```bash
pip install -r requirements.txt
python src/ingestion/soil_loader.py       # Pull raw data
python src/features/feature_engineer.py  # Build features
python src/models/trainer.py             # Train models
uvicorn src.api.main:app --reload        # Start API
```

## API Endpoints

| Method | Endpoint     | Description                        |
|--------|--------------|------------------------------------|
| POST   | /predict     | Get top crop recommendations       |
| POST   | /explain     | SHAP explanation for a prediction  |
| GET    | /health      | Service health check               |

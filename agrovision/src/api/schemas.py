"""
schemas.py
----------
Pydantic v2 request / response models for the AgroVision API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ── Request models ─────────────────────────────────────────────────────────

class SoilInput(BaseModel):
    N:              float = Field(..., ge=0,   le=150,  description="Nitrogen (kg/ha)")
    P:              float = Field(..., ge=0,   le=100,  description="Phosphorus (kg/ha)")
    K:              float = Field(..., ge=0,   le=300,  description="Potassium (kg/ha)")
    pH:             float = Field(..., ge=3.5, le=9.5,  description="Soil pH")
    moisture:       float = Field(..., ge=0,   le=100,  description="Soil moisture (%)")
    organic_matter: float = Field(..., ge=0,   le=10,   description="Organic matter (%)")


class ClimateInput(BaseModel):
    annual_rainfall_mm: float = Field(..., ge=0,  le=5000, description="Annual rainfall (mm)")
    temp_max:           float = Field(..., ge=10, le=50,   description="Max temp (°C)")
    temp_min:           float = Field(..., ge=-5, le=45,   description="Min temp (°C)")
    humidity:           float = Field(..., ge=0,  le=100,  description="Relative humidity (%)")
    solar_radiation:    Optional[float] = Field(None, ge=0, le=30,
                            description="Solar radiation (MJ/m²/day)")


class PredictRequest(BaseModel):
    region_id: str             = Field(..., description="Unique region identifier")
    latitude:  float           = Field(..., ge=-90,  le=90)
    longitude: float           = Field(..., ge=-180, le=180)
    soil:      SoilInput
    climate:   ClimateInput
    ndvi_mean: Optional[float] = Field(None, ge=-1, le=1,
                                       description="Mean NDVI (auto-fetched if omitted)")
    top_k:     int             = Field(5, ge=1, le=15,
                                       description="Number of crop recommendations to return")


# ── Response models ────────────────────────────────────────────────────────

class CropRecommendation(BaseModel):
    rank:         int
    crop:         str
    score:        float   = Field(..., description="Ensemble confidence score (0–1)")
    profit_index: float   = Field(..., description="Market profitability index (0–1)")
    xgb_prob:     float   = Field(..., description="XGBoost probability component")

class PredictResponse(BaseModel):
    region_id:       str
    recommendations: list[CropRecommendation]
    model_version:   str = "1.0.0"


class DriverDetail(BaseModel):
    feature:     str
    impact:      float
    description: str

class ExplainResponse(BaseModel):
    region_id:     str
    crop:          str
    explanation:   str
    top_drivers:   list[DriverDetail]
    top_suppressors: list[DriverDetail]


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    version: str

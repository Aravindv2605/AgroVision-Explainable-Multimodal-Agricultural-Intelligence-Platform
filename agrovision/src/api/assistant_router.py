"""
assistant_router.py
-------------------
FastAPI router for the AgroVision Assistant endpoints.
Mounted at: /api/v1/assistant/

Endpoints:
  POST /assistant/chat         — text + optional image chat
  POST /assistant/disease      — plant disease from image upload
  GET  /assistant/weather      — weather + farming alerts
  POST /assistant/tts          — text → MP3 audio bytes
  POST /assistant/crop-advice  — deep crop advice from prediction
"""

import base64
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from src.utils.logger import get_logger

logger = get_logger(__name__)
assistant_router = APIRouter(prefix="/assistant", tags=["Assistant"])


# ── Request / Response schemas ────────────────────────────────────────────

class ChatRequest(BaseModel):
    text: str
    crop_context: Optional[str] = ""
    image_b64: Optional[str] = None   # base64-encoded image (optional)


class ChatResponse(BaseModel):
    response: str
    mode: str
    success: bool


class CropAdviceRequest(BaseModel):
    crop: str
    score: float = 0.0
    soil: Optional[dict] = None
    climate: Optional[dict] = None
    use_gemini: bool = False


class WeatherResponse(BaseModel):
    success: bool
    location: str
    current: dict
    alerts: list
    farming_advice: str
    mode: str


# ── Endpoints ─────────────────────────────────────────────────────────────

@assistant_router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Conversational endpoint.
    Accepts text query + optional base64 image + crop context.
    Returns markdown-formatted AI response.
    """
    try:
        from src.assistant.agro_brain import chat as brain_chat

        image_bytes = None
        if req.image_b64:
            image_bytes = base64.b64decode(req.image_b64)

        result = brain_chat(
            text=req.text,
            image_bytes=image_bytes,
            crop_context=req.crop_context or "",
        )
        return ChatResponse(**result)
    except Exception as exc:
        logger.error(f"Chat error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@assistant_router.post("/disease")
async def disease_detect(file: UploadFile = File(...)):
    """
    Plant disease detection from uploaded image.
    Accepts multipart image upload.
    Returns structured markdown disease analysis.
    """
    try:
        from src.assistant.disease_detector import analyze_image

        image_bytes = await file.read()
        result = analyze_image(image_bytes)
        return result
    except Exception as exc:
        logger.error(f"Disease detection error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@assistant_router.get("/weather", response_model=WeatherResponse)
async def weather(lat: float = 20.0, lon: float = 78.0, city: str = ""):
    """
    Fetch current weather + generate farming alerts.
    Uses OpenWeatherMap if OPENWEATHER_API_KEY set, else demo data.
    """
    try:
        from src.assistant.weather_intel import get_weather
        result = get_weather(lat=lat, lon=lon, city=city)
        return WeatherResponse(
            success=result["success"],
            location=result["location"],
            current=result["current"],
            alerts=result["alerts"],
            farming_advice=result["farming_advice"],
            mode=result["mode"],
        )
    except Exception as exc:
        logger.error(f"Weather error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@assistant_router.post("/tts")
async def tts(text: str = Form(...), language: str = Form("English")):
    """
    Convert text to MP3 audio using gTTS.
    Returns audio/mpeg bytes.
    """
    try:
        from src.assistant.voice_handler import text_to_speech
        audio_bytes = text_to_speech(text, language)
        if not audio_bytes:
            raise HTTPException(status_code=503, detail="TTS unavailable — install gTTS")
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"TTS error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@assistant_router.post("/crop-advice")
async def crop_advice(req: CropAdviceRequest):
    """
    Generate a full advisory card for the predicted crop.
    Integrates with the existing prediction engine output.
    """
    try:
        if req.use_gemini:
            from src.assistant.crop_advisor import get_gemini_enhanced_advice
            md = get_gemini_enhanced_advice(
                crop=req.crop,
                soil=req.soil or {},
                climate=req.climate or {},
            )
        else:
            from src.assistant.crop_advisor import get_crop_advice_card
            advice = get_crop_advice_card(
                crop=req.crop,
                score=req.score,
                soil=req.soil,
                climate=req.climate,
            )
            md = advice["summary_md"]

        return {"success": True, "advice_md": md, "crop": req.crop}
    except Exception as exc:
        logger.error(f"Crop advice error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

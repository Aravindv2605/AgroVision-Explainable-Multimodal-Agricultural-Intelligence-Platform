"""
weather_intel.py
----------------
Weather intelligence module for AgroVision Assistant.

Priority:
  1. OpenWeatherMap API  (if OPENWEATHER_API_KEY is set)
  2. Static demo data (offline mode)

Provides: current weather, 5-day forecast, farming alerts.
"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

OWM_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OWM_BASE = "https://api.openweathermap.org/data/2.5"


# ── Farming alert thresholds ─────────────────────────────────────────────
def _generate_farming_alerts(temp: float, humidity: float, rain_mm: float, wind_kph: float) -> list[str]:
    alerts = []
    if temp > 40:
        alerts.append("🔴 **Heat Alert:** Temperature > 40°C — Mulch fields, increase irrigation frequency")
    elif temp < 10:
        alerts.append("🔵 **Cold Alert:** Temperature < 10°C — Protect cold-sensitive seedlings with covers")
    if humidity > 80:
        alerts.append("⚠️ **Disease Risk:** Humidity > 80% — Apply preventive fungicide; avoid overhead irrigation")
    if rain_mm > 50:
        alerts.append("🌧️ **Heavy Rain Alert:** Postpone spraying; ensure field drainage; watch for waterlogging")
    elif rain_mm == 0 and humidity < 40:
        alerts.append("☀️ **Dry Conditions:** Low rainfall + humidity — Irrigate crops, apply mulch")
    if wind_kph > 30:
        alerts.append("💨 **High Wind Alert:** Avoid pesticide spraying today — risk of drift")
    if not alerts:
        alerts.append("✅ **Good Farming Conditions:** Weather is suitable for most field operations today")
    return alerts


def _farming_advice_from_weather(temp: float, humidity: float, rain_mm: float) -> str:
    advice = []
    if 20 <= temp <= 32 and rain_mm < 10 and humidity < 80:
        advice.append("✅ Excellent conditions for pesticide/fertilizer application")
    if rain_mm > 20:
        advice.append("💧 Rainfall detected — skip irrigation today, check drainage")
    if humidity > 75:
        advice.append("🦠 High humidity — monitor crops for fungal diseases")
    if temp > 35:
        advice.append("🌡️ Heat stress risk — irrigate in early morning or evening")
    if 15 <= temp <= 25:
        advice.append("🌾 Ideal temperature range — good for vegetative growth")
    return "\n".join(advice) if advice else "🌤️ Moderate conditions — routine field monitoring recommended"


# ── Live weather fetch ────────────────────────────────────────────────────
def get_weather(lat: float, lon: float, city: str = "") -> dict:
    """
    Fetch current weather and generate farming advice.

    Returns dict: { success, current, forecast_days, alerts, farming_advice, mode }
    """
    if OWM_KEY:
        return _fetch_live_weather(lat, lon, city)
    else:
        return _demo_weather(lat, lon)


def _fetch_live_weather(lat: float, lon: float, city: str) -> dict:
    try:
        # Current weather
        if city:
            url = f"{OWM_BASE}/weather?q={city}&appid={OWM_KEY}&units=metric"
        else:
            url = f"{OWM_BASE}/weather?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric"

        r = requests.get(url, timeout=8)
        r.raise_for_status()
        d = r.json()

        temp = d["main"]["temp"]
        humidity = d["main"]["humidity"]
        rain_mm = d.get("rain", {}).get("1h", 0)
        wind_kph = d["wind"]["speed"] * 3.6
        description = d["weather"][0]["description"].title()
        location_name = d.get("name", f"{lat:.2f}°N, {lon:.2f}°E")

        # 5-day forecast
        if city:
            fc_url = f"{OWM_BASE}/forecast?q={city}&appid={OWM_KEY}&units=metric&cnt=5"
        else:
            fc_url = f"{OWM_BASE}/forecast?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric&cnt=5"

        fc_r = requests.get(fc_url, timeout=8)
        forecast_days = []
        if fc_r.ok:
            for item in fc_r.json().get("list", [])[:5]:
                forecast_days.append({
                    "datetime": item["dt_txt"],
                    "temp": item["main"]["temp"],
                    "humidity": item["main"]["humidity"],
                    "rain_mm": item.get("rain", {}).get("3h", 0),
                    "description": item["weather"][0]["description"].title(),
                })

        alerts = _generate_farming_alerts(temp, humidity, rain_mm, wind_kph)
        advice = _farming_advice_from_weather(temp, humidity, rain_mm)

        return {
            "success": True,
            "location": location_name,
            "current": {
                "temp_c": round(temp, 1),
                "humidity_pct": humidity,
                "rain_mm": rain_mm,
                "wind_kph": round(wind_kph, 1),
                "description": description,
            },
            "forecast_days": forecast_days,
            "alerts": alerts,
            "farming_advice": advice,
            "mode": "live",
        }
    except Exception as exc:
        return _demo_weather(lat, lon, error=str(exc))


def _demo_weather(lat: float, lon: float, error: str = "") -> dict:
    """Return demo/static weather data when API key not configured."""
    temp, humidity, rain_mm, wind_kph = 28.5, 65.0, 2.0, 12.0
    alerts = _generate_farming_alerts(temp, humidity, rain_mm, wind_kph)
    advice = _farming_advice_from_weather(temp, humidity, rain_mm)
    note = f"\n\n*⚠️ Error: {error}*" if error else "\n\n*💡 Add `OPENWEATHER_API_KEY` to `.env` for live weather data.*"
    return {
        "success": True,
        "location": f"Demo Location ({lat:.2f}°N, {lon:.2f}°E)",
        "current": {
            "temp_c": temp,
            "humidity_pct": humidity,
            "rain_mm": rain_mm,
            "wind_kph": wind_kph,
            "description": "Partly Cloudy (Demo)",
        },
        "forecast_days": [],
        "alerts": alerts,
        "farming_advice": advice + note,
        "mode": "demo",
    }

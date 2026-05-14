"""
crop_advisor.py
---------------
Generates detailed, contextual crop advice by integrating
the existing ensemble prediction output with the AgroBrain LLM.

When the crop prediction module recommends e.g. "Rice", this module
produces a full advisory card covering soil, water, diseases,
fertilizers, yield, weather suitability, and farming tips.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Embedded crop knowledge ────────────────────────────────────────────────
_CROP_DB: dict[str, dict] = {
    "rice": {
        "why_suitable": "Rice thrives in warm, humid climates with high water availability. It excels in clay-loam soils with excellent water retention and is the backbone of Indian food security.",
        "soil": "Clay or clay-loam | pH 5.5–7.0 | High water retention | Tolerates slight acidity",
        "water": "High — 900–1200 mm seasonal | Keep 2–5 cm standing water during vegetative phase | Drain 10 days before harvest",
        "diseases": "Rice Blast, Bacterial Leaf Blight (BLB), Sheath Blight, Brown Plant Hopper, Stem Borer, False Smut",
        "fertilizers": "N: 100–120 kg/ha (3 splits) | P: 50 kg/ha (basal) | K: 50 kg/ha | Zinc: 25 kg/ha if deficient",
        "yield": "National avg: 2.5 t/ha | With good management: 5–7 t/ha | SRI method: up to 8–10 t/ha",
        "weather": "Temp: 20–35°C | Humid climate | Annual rainfall > 1000 mm or assured irrigation",
        "tips": ["Use certified seed of local recommended variety", "Transplant at 20–25 days seedling age (single seedling in SRI)", "Drain field 10 days before harvest for uniform ripening", "Apply Zinc sulfate 25 kg/ha if yellowing between leaf veins observed"],
    },
    "wheat": {
        "why_suitable": "Wheat is ideal for rabi season with cool growing temperatures. It produces high yields in well-drained loamy soils with moderate irrigation.",
        "soil": "Well-drained loamy to clay-loam | pH 6.0–7.5 | Avoid waterlogging",
        "water": "Medium — 450–650 mm | 4–6 critical irrigations | Most critical: CRI at 20–25 DAS",
        "diseases": "Yellow Rust, Brown Rust, Loose Smut, Powdery Mildew, Karnal Bunt, Alternaria Blight",
        "fertilizers": "N: 120–150 kg/ha (3 splits) | P: 60 kg/ha (basal) | K: 40 kg/ha | S: 20–30 kg/ha",
        "yield": "National avg: 3.2 t/ha | Achievable: 5–7 t/ha | Irrigated HD varieties: up to 7 t/ha",
        "weather": "Sowing: 10–15°C | Growing: 15–25°C | Cool + dry at maturity | Frost risk at heading",
        "tips": ["Sow at right time: mid-November for most N-Indian regions", "Seed treatment with Carboxin+Thiram @ 3g/kg seed", "First irrigation at 20–25 DAS (CRI stage) is most critical", "Harvest when grain moisture < 14% for safe storage"],
    },
    "maize": {
        "why_suitable": "Maize is a versatile C4 crop with high yield potential. Performs well in well-drained loamy soils with adequate nutrition and irrigation.",
        "soil": "Well-drained sandy loam to loamy | pH 6.0–7.5 | Cannot tolerate waterlogging",
        "water": "Medium — 500–800 mm | Critical: knee-high, tasseling, silking, grain filling",
        "diseases": "Downy Mildew, Turcicum Leaf Blight, Post Borer, Fall Armyworm, Northern Corn Leaf Blight",
        "fertilizers": "N: 150–180 kg/ha (3 splits) | P: 75 kg/ha (basal) | K: 60 kg/ha | Zinc: 25 kg/ha",
        "yield": "National avg: 2.8 t/ha | Hybrid varieties: 6–10 t/ha",
        "weather": "Temp: 18–32°C | Moderate humidity | Well-distributed rainfall",
        "tips": ["Use hybrid seeds for 2–3x yield advantage over open-pollinated varieties", "Maintain plant population: 65,000–75,000 plants/ha", "Apply earthing up at 30 DAS to prevent lodging", "Intercrop with soybean for additional income and nitrogen fixation"],
    },
    "tomato": {
        "why_suitable": "Tomato is a high-value vegetable with year-round demand. Suitable for both open field and protected cultivation with high returns.",
        "soil": "Well-drained sandy loam to loam | pH 6.0–7.0 | Rich in organic matter",
        "water": "Medium — 400–600 mm | Drip irrigation preferred | Avoid wetting foliage",
        "diseases": "Early Blight, Late Blight, Fusarium Wilt, Leaf Curl Virus, Fruit Borer, Bacterial Wilt",
        "fertilizers": "N: 120 kg/ha | P: 60 kg/ha | K: 60 kg/ha | Ca + B for fruit quality",
        "yield": "Open field: 12–25 t/ha | Protected cultivation: 50–100 t/ha",
        "weather": "Day: 21–27°C | Night: 10–20°C | Avoid > 35°C at flowering",
        "tips": ["Train with single or double stake system", "Remove suckers below first flower cluster for better yield", "Mulching reduces soil-borne diseases by 40–60%", "Harvest at breaker stage for distant markets"],
    },
    "cotton": {
        "why_suitable": "Cotton thrives in black (Vertisol) soils with good water-holding capacity. High commercial value fiber crop for dry regions.",
        "soil": "Black (Vertisol) or deep loamy soil | pH 7.0–8.0 | Good water retention",
        "water": "Low-Medium — 500–700 mm | Drip preferred | Critical: boll formation stage",
        "diseases": "Bacterial Blight, Alternaria Leaf Spot, Grey Mildew, Pink Bollworm, American Bollworm",
        "fertilizers": "N: 120 kg/ha | P: 60 kg/ha | K: 60 kg/ha | Foliar boron at flowering",
        "yield": "National avg: 450 kg lint/ha | Bt cotton: 550–650 kg lint/ha",
        "weather": "Temp: 21–30°C | Requires 180–200 frost-free days | Dry weather at maturity",
        "tips": ["Use Bt cotton hybrids for bollworm resistance", "Maintain optimum plant population: 8,000–10,000 plants/ha", "Monitor for Pink Bollworm: install pheromone traps @ 5/ha", "Avoid excessive nitrogen — causes vegetative growth at expense of bolls"],
    },
    "sugarcane": {
        "why_suitable": "Sugarcane is suited to tropical humid conditions with high solar radiation. Requires heavy irrigation but delivers very high biomass.",
        "soil": "Well-drained loamy to clay-loam | pH 6.5–7.5 | Deep fertile soil",
        "water": "High — 1500–2500 mm | Flood or drip (drip saves 30–40% water) | Critical: grand growth phase",
        "diseases": "Red Rot, Smut, Grassy Shoot Disease, Scale Insect, Top Borer, Early Shoot Borer",
        "fertilizers": "N: 250–300 kg/ha | P: 60–80 kg/ha | K: 120–150 kg/ha | Press mud: 10 t/ha",
        "yield": "National avg: 65 t/ha | Achievable: 80–120 t/ha | Ratoon: 60–80 t/ha",
        "weather": "Temp: 21–38°C | Long growing season (12–18 months) | High humidity in early growth",
        "tips": ["Use disease-free setts for planting", "Adopt Trench method of planting for better lodging resistance", "Ratoon crop can give 70–80% of main crop yield at lower cost", "Apply trash mulching to conserve moisture and suppress weeds"],
    },
    "groundnut": {
        "why_suitable": "Groundnut is a drought-tolerant legume suitable for sandy soils. Fixes atmospheric nitrogen and improves soil fertility.",
        "soil": "Well-drained sandy loam to sandy | pH 6.0–7.0 | Loose friable structure",
        "water": "Low — 400–600 mm | Critical: pegging + pod filling | Drip irrigation ideal",
        "diseases": "Tikka Leaf Spot, Rust, Stem Rot, Collar Rot, Bud Necrosis Virus",
        "fertilizers": "N: 20–25 kg/ha | P: 60 kg/ha | K: 40 kg/ha | Gypsum: 400–500 kg/ha at pegging",
        "yield": "National avg: 1.4 t pods/ha | Improved varieties: 2.5–3.5 t/ha",
        "weather": "Temp: 25–30°C | Semi-arid conditions | 500–700 mm rainfall",
        "tips": ["Inoculate seeds with Rhizobium to enhance nitrogen fixation", "Apply gypsum at pegging stage for proper pod development", "Harvest at right maturity (dark veins inside shell)", "Dry pods to < 10% moisture for safe storage"],
    },
    "soybean": {
        "why_suitable": "Soybean is a high-protein legume crop that fixes nitrogen and improves soil health. Popular in central India during kharif season.",
        "soil": "Well-drained loamy to clay-loam | pH 6.0–7.0 | Avoid waterlogging",
        "water": "Medium — 450–700 mm | Critical: flowering, pod filling",
        "diseases": "Yellow Mosaic Virus, Bacterial Pustule, Rust, Stem Fly, Spodoptera",
        "fertilizers": "N: 20–30 kg/ha (starter) | P: 60–80 kg/ha | K: 40 kg/ha | Rhizobium + PSB inoculation",
        "yield": "National avg: 1.2 t/ha | Improved varieties: 2.0–2.8 t/ha",
        "weather": "Temp: 25–30°C | Kharif season | Well-distributed rainfall",
        "tips": ["Seed treatment with Rhizobium + Thiram is essential", "Intercrop with maize (4:2 row ratio) for risk diversification", "Weed control in first 30 DAS is critical", "Yellow Mosaic Virus — use resistant varieties; control whitefly vector"],
    },
    "onion": {
        "why_suitable": "Onion is a high-value rabi vegetable with consistent market demand. Suitable for well-drained soils in moderate climates.",
        "soil": "Sandy loam to loam | pH 6.0–7.0 | Good drainage essential",
        "water": "Medium — 350–550 mm | Critical: bulb initiation stage | Stop irrigation 10 days before harvest",
        "diseases": "Purple Blotch, Stemphylium Blight, Botrytis Leaf Blight, Thrips, Onion Fly",
        "fertilizers": "N: 100 kg/ha | P: 60 kg/ha | K: 80 kg/ha | S: 30 kg/ha",
        "yield": "National avg: 16 t/ha | Good management: 25–35 t/ha",
        "weather": "Temp: 13–24°C growing | 35–45°C maturation | Low humidity at bulbing",
        "tips": ["Use certified disease-free transplants", "Maintain plant population: 75,000–1,00,000 plants/ha", "Cure bulbs for 10–14 days before storage", "Control thrips early — they spread Iris Yellow Spot Virus"],
    },
    "potato": {
        "why_suitable": "Potato is a cool-season crop with high caloric yield and market value. Performs well in well-drained fertile loamy soils.",
        "soil": "Sandy loam to loam | pH 5.5–6.5 | Well-drained | Loose fertile",
        "water": "Medium — 400–600 mm | Critical: tuber initiation, tuber filling | Avoid waterlogging",
        "diseases": "Late Blight, Early Blight, Bacterial Wilt, Common Scab, Aphids, Potato Tuber Moth",
        "fertilizers": "N: 180–200 kg/ha | P: 100 kg/ha | K: 150 kg/ha | Ca + Mg for quality",
        "yield": "National avg: 23 t/ha | Improved: 35–40 t/ha",
        "weather": "Temp: 15–25°C growing | Cool nights preferred | Avoid frost",
        "tips": ["Use certified seed tubers — disease-free is non-negotiable", "Earthing up at 30 DAS to protect tubers from sunlight (greening)", "Late Blight monitoring critical during cool-wet weather — spray Metalaxyl", "Store at 2–4°C in dark to prevent sprouting and greening"],
    },
}

_DEFAULT_ADVICE = {
    "why_suitable": "This crop has been recommended based on your soil NPK values, pH, moisture, climate data, and local market profitability index.",
    "soil": "Ensure balanced NPK — conduct soil test for precise recommendations",
    "water": "Monitor crop water stress at critical growth stages",
    "diseases": "Regular field scouting; early detection and IPM-based control",
    "fertilizers": "Soil-test-based NPK application; supplement with organic manures",
    "yield": "Follow recommended package of practices for your region",
    "weather": "Check local forecast; adjust irrigation and spray schedules accordingly",
    "tips": ["Use certified quality seeds", "Practice crop rotation", "Maintain field sanitation", "Regular crop monitoring"],
}


def get_crop_advice_card(crop: str, score: float = 0.0, soil: dict = None, climate: dict = None) -> dict:
    """
    Generate a comprehensive crop advisory card.

    Parameters
    ----------
    crop    : predicted crop name (lowercase, e.g. 'rice')
    score   : ensemble prediction confidence score
    soil    : dict with soil parameters (optional, for context)
    climate : dict with climate parameters (optional, for context)

    Returns
    -------
    dict with all advisory fields + a formatted markdown summary
    """
    data = _CROP_DB.get(crop.lower(), _DEFAULT_ADVICE)
    crop_display = crop.replace("_", " ").title()

    # Build explanation sentence
    reasons = []
    if soil:
        ph = soil.get("pH", 0)
        moisture = soil.get("moisture", 0)
        if 5.5 <= ph <= 7.5:
            reasons.append(f"soil pH ({ph}) is within optimal range")
        if moisture > 40:
            reasons.append(f"soil moisture ({moisture}%) supports this crop")
    if climate:
        temp_max = climate.get("temp_max", 0)
        rainfall = climate.get("annual_rainfall_mm", 0)
        if temp_max:
            reasons.append(f"temperature ({temp_max}°C max) is suitable")
        if rainfall:
            reasons.append(f"annual rainfall ({rainfall} mm) matches requirements")

    if reasons:
        explanation = f"**{crop_display}** is recommended because your {', '.join(reasons)}."
    else:
        explanation = f"**{crop_display}** is recommended based on your soil and climate profile with {score:.1%} confidence."

    # Format tips as bullet list
    tips = data.get("tips", _DEFAULT_ADVICE["tips"])
    tips_md = "\n".join(f"- {t}" for t in tips)

    summary_md = f"""## 🌾 {crop_display} — Complete Farming Guide

### 🤖 Why {crop_display}?
{explanation}

> {data.get('why_suitable', _DEFAULT_ADVICE['why_suitable'])}

---

### 🌍 Soil Requirements
{data.get('soil', _DEFAULT_ADVICE['soil'])}

### 💧 Water Requirements
{data.get('water', _DEFAULT_ADVICE['water'])}

### 🌦️ Suitable Weather
{data.get('weather', _DEFAULT_ADVICE['weather'])}

### 🌱 Fertilizer Recommendations
{data.get('fertilizers', _DEFAULT_ADVICE['fertilizers'])}

### 🦠 Common Diseases & Pests
{data.get('diseases', _DEFAULT_ADVICE['diseases'])}

### 📈 Expected Yield
{data.get('yield', _DEFAULT_ADVICE['yield'])}

### 💡 Key Farming Tips
{tips_md}
"""

    return {
        "crop": crop_display,
        "confidence": f"{score:.1%}",
        "explanation": explanation,
        "why_suitable": data.get("why_suitable"),
        "soil": data.get("soil"),
        "water": data.get("water"),
        "weather": data.get("weather"),
        "fertilizers": data.get("fertilizers"),
        "diseases": data.get("diseases"),
        "yield": data.get("yield"),
        "tips": tips,
        "summary_md": summary_md,
    }


def get_gemini_enhanced_advice(crop: str, soil: dict, climate: dict) -> str:
    """
    Use Gemini to generate a richer, personalized advice if API key is available.
    Falls back to local advice card.
    """
    from src.assistant.agro_brain import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        return get_crop_advice_card(crop, soil=soil, climate=climate)["summary_md"]

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""You are AgroVision, an expert agricultural AI.
The crop prediction model has recommended **{crop}** for this farmer.

Soil data: {soil}
Climate data: {climate}

Provide a detailed, farmer-friendly guide covering:
1. Why {crop} is suitable for these conditions (explain using the actual soil/climate numbers)
2. Exact soil preparation steps
3. Fertilizer schedule with timing
4. Irrigation schedule with critical stages
5. Top 3 disease risks and prevention
6. Expected yield and income estimate
7. 5 key tips to maximize yield

Format with markdown headers, bullet points, and tables. Be specific and actionable."""

        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return get_crop_advice_card(crop, soil=soil, climate=climate)["summary_md"]

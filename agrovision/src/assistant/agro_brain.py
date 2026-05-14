"""
agro_brain.py
-------------
Core conversational AI engine for AgroVision Assistant.

Priority:
  1. Google Gemini API  (if GEMINI_API_KEY is set)
  2. Built-in offline agricultural knowledge base

The engine accepts plain text or text + image (bytes),
and always returns a markdown-formatted string response.
"""

import os
import base64
from io import BytesIO
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Agricultural system prompt ─────────────────────────────────────────────
_SYSTEM_PROMPT = """You are AgroVision Assistant, an expert AI agricultural advisor for Indian farmers.

You have deep knowledge of:
- Crops: rice, wheat, maize, sugarcane, cotton, soybean, groundnut, tomato, onion, potato,
  turmeric, banana, mango, coconut, black gram
- Soil science: NPK management, pH, organic matter, soil health
- Plant diseases: identification, symptoms, causes, prevention, organic & chemical treatment
- Pest management: identification, IPM, organic and chemical control
- Fertilizer: organic and synthetic, timing, dosage, soil-test-based recommendations
- Irrigation: flood, drip, sprinkler, critical stages
- Weather-based farming decisions
- Organic and sustainable farming
- Crop yield improvement techniques
- Indian farming seasons: Kharif, Rabi, Zaid

Always respond in clear, farmer-friendly language using markdown formatting.
Provide actionable, practical advice. Use bullet points and tables where helpful.
When mentioning chemical inputs, always include safety notes.
"""

# ── Offline knowledge base ─────────────────────────────────────────────────
_KB = {
    "fertilizer": """**🌱 Fertilizer Recommendations**

**Soil-Test-Based Approach (Always preferred):**
- Contact your nearest Krishi Vigyan Kendra (KVK) for free/subsidized soil testing.

**General NPK Guidelines:**
| Crop | N (kg/ha) | P (kg/ha) | K (kg/ha) |
|---|---|---|---|
| Rice | 100–120 | 50 | 50 |
| Wheat | 120–150 | 60 | 40 |
| Maize | 150–180 | 75 | 60 |
| Tomato | 120 | 60 | 60 |
| Cotton | 120 | 60 | 60 |

**Organic Fertilizers:**
- FYM / Compost: 10–15 t/ha (improves long-term soil health)
- Vermicompost: 3–5 t/ha
- Neem cake: 200–250 kg/ha (fertilizer + pest repellent)
- Biofertilizers (Rhizobium, PSB, KSB): for legumes especially

**Key Rule:** Apply N in splits (basal + top-dressing) to reduce losses.""",

    "disease": """**🦠 Plant Disease Management**

**Common Disease Symptoms:**
| Symptom | Likely Cause |
|---|---|
| Yellow leaves | N deficiency / Mosaic virus / Iron chlorosis |
| Brown/black spots | Fungal blight / Bacterial leaf spot |
| White powder on leaves | Powdery mildew (fungal) |
| Wilting | Fusarium wilt / Root rot / Water stress |
| Holes in leaves | Insect feeding (caterpillar / beetles) |
| Leaf curling | Aphids / Leaf curl virus / Water stress |

**Integrated Disease Management (IDM):**
1. Use certified disease-resistant seeds
2. Crop rotation (breaks disease cycle)
3. Field sanitation (remove crop debris)
4. Apply Trichoderma viride 2.5 kg/ha (biocontrol)
5. Neem oil 5% spray (broad-spectrum organic)
6. Chemical fungicides only as last resort

📸 **Upload a photo** for specific AI-based disease diagnosis!""",

    "irrigation": """**💧 Irrigation Guide**

**Critical Irrigation Stages:**
| Crop | Most Critical Stage |
|---|---|
| Rice | Transplanting, Tillering, Panicle Initiation |
| Wheat | CRI (20–25 DAS), Tillering, Flowering, Grain Fill |
| Maize | Knee-high, Tasseling, Silking |
| Tomato | Transplanting, Flowering, Fruit Development |

**Modern Methods (Water Saving):**
- Drip Irrigation: 40–60% water saving — best for vegetables, fruits
- Sprinkler: 20–30% saving — best for wheat, groundnut
- AWD (Alternate Wetting & Drying): 15–30% saving for paddy

**Signs of Water Stress:** Leaf rolling, wilting in early morning, bluish-green color
**Signs of Overwatering:** Yellow lower leaves, root rot, stunted growth

**Practical Test:** Push finger 5 cm into soil — if dry, irrigate immediately.""",

    "pest": """**🐛 Pest Management (IPM)**

**Common Pests & Controls:**

**Aphids** (suck sap, spread viruses)
- Organic: Neem oil 5%, yellow sticky traps
- Chemical: Dimethoate 30% EC @ 1 ml/L

**Stem Borer** (dead hearts / white ears)
- Organic: Trichogramma egg parasitoid @ 1.5 lakh cards/ha
- Chemical: Chlorpyrifos 20% EC @ 2.5 ml/L

**Whitefly** (yellowing, honeydew, virus vector)
- Organic: Yellow sticky traps, Verticillium lecanii
- Chemical: Imidacloprid 17.8% SL @ 0.5 ml/L

**Fall Armyworm** (maize leaves with frass)
- Organic: Bt (Bacillus thuringiensis) @ 1 kg/ha
- Chemical: Spinetoram 11.7% SC @ 0.5 ml/L

**IPM Principles:** Monitor weekly → Reach ETL → Select right pesticide → Rotate chemicals""",

    "soil": """**🌍 Soil Health Guide**

**Ideal Soil Parameters:**
| Parameter | Optimal Range |
|---|---|
| pH | 6.0 – 7.0 |
| Nitrogen | > 280 kg/ha |
| Phosphorus | > 15 kg/ha |
| Potassium | > 120 kg/ha |
| Organic Matter | > 2.5% |
| Moisture | 40–80% |

**Soil pH Correction:**
- Too acidic (< 6.0): Apply agricultural lime 2–4 t/ha
- Too alkaline (> 7.5): Apply gypsum 2.5 t/ha or elemental sulfur

**Improving Soil Health:**
1. Add FYM/compost every season
2. Practice green manuring (Dhaincha/Sunhemp)
3. Reduce tillage to protect soil structure
4. Grow cover crops in off-season
5. Balanced NPK — avoid single-nutrient excess""",

    "weather": """**🌦️ Weather-Based Farming Advice**

**Temperature Guidelines:**
- < 10°C: Cold stress risk — protect cold-sensitive crops
- 20–35°C: Ideal for most kharif crops
- > 40°C: Heat stress — mulch + increase irrigation
- > 35°C at flowering: Reduces grain/fruit set significantly

**Rainfall Management:**
- < 500 mm season: Grow drought-tolerant crops (millets, groundnut)
- 600–1200 mm: Rice, maize, cotton
- > 1500 mm: Waterlogged — paddy ideal, drainage critical for others

**Humidity Alerts:**
- > 80% RH: High fungal disease risk — preventive fungicide spray
- < 30% RH: Increase irrigation, use mulching

**Before Spraying:** Check 48-hour forecast; avoid spraying before rain or in strong wind""",

    "organic": """**🌿 Organic Farming Guide**

**Key Organic Inputs:**
| Input | Rate | Benefit |
|---|---|---|
| Vermicompost | 3–5 t/ha | Soil structure + nutrition |
| FYM | 10–15 t/ha | Broad-spectrum nutrition |
| Neem cake | 200–250 kg/ha | Fertilizer + pest repellent |
| Trichoderma viride | 2.5 kg/ha | Biocontrol fungicide |
| Panchagavya | 3% spray | Plant immunity booster |
| Jeevamrutha | 200 L/ha | Soil microbial activator |

**Homemade Inputs:**
- Jeevamrutha: 200L water + 10kg cow dung + 10L cow urine + 2kg jaggery + 2kg pulse flour
- Panchagavya: Cow dung + cow urine + milk + curd + ghee (fermented 30 days)

**Benefits of Organic Farming:**
- 20–30% premium price in organic markets
- Improved soil health long-term
- Reduced input cost after 3 seasons
- Eligible for NPOP certification""",

    "yield": """**📈 Crop Yield Enhancement**

**Top Strategies:**
1. **Seed Quality** — Certified HYV/hybrid seeds (germination > 85%)
2. **Optimum Plant Density** — Follow spacing recommendations
3. **Balanced Nutrition** — Soil-test-based NPK + micronutrients
4. **Timely Pest/Disease Control** — Early action saves 20–40% yield loss
5. **Efficient Irrigation** — Deficit at critical stages = 30–50% yield loss

**Advanced Techniques:**
- System of Rice Intensification (SRI): 20–50% paddy yield boost
- Precision farming with soil sensors
- Drone-based crop monitoring and spraying
- Protected cultivation for vegetables (50–100 t/ha tomato vs 15–20 open field)

**Realistic Targets:**
| Crop | India Avg | Achievable |
|---|---|---|
| Rice | 2.5 t/ha | 5–7 t/ha |
| Wheat | 3.2 t/ha | 5–7 t/ha |
| Maize | 2.8 t/ha | 6–10 t/ha |
| Tomato | 15 t/ha | 25–50 t/ha |""",
}

# ── Keyword → topic routing ───────────────────────────────────────────────
_ROUTES = {
    "fertilizer": ["fertilizer", "npk", "nitrogen", "phosphorus", "potassium", "manure", "compost", "dap", "urea", "nutrition"],
    "disease": ["disease", "blight", "spot", "rust", "mildew", "rot", "wilt", "infection", "fungal", "virus", "lesion", "yellowing", "brown leaf"],
    "irrigation": ["irrigation", "water", "drip", "sprinkler", "flood", "moisture", "irrigate", "watering"],
    "pest": ["pest", "insect", "bug", "aphid", "borer", "caterpillar", "whitefly", "thrips", "mite", "grasshopper", "locust"],
    "soil": ["soil", "ph", "sandy", "loam", "clay", "organic matter", "soil test", "fertility", "acidic", "alkaline"],
    "weather": ["weather", "rain", "temperature", "humidity", "forecast", "climate", "rainfall", "heat", "cold", "frost"],
    "organic": ["organic", "natural", "bio", "vermicompost", "neem", "jeevamrutha", "panchagavya"],
    "yield": ["yield", "production", "increase", "improve", "harvest", "output", "productivity"],
}


def _route_query(query: str) -> Optional[str]:
    q = query.lower()
    for topic, keywords in _ROUTES.items():
        if any(k in q for k in keywords):
            return topic
    return None


def get_offline_response(query: str, crop_context: str = "") -> str:
    """Return knowledge-base response matched to query keywords."""
    topic = _route_query(query)
    if topic and topic in _KB:
        response = _KB[topic]
        if crop_context:
            response = f"*Crop context: **{crop_context}***\n\n" + response
        return response

    # Fallback: general help menu
    return (
        "**🌾 AgroVision Assistant — I'm here to help!**\n\n"
        "Ask me about:\n"
        "- 🌱 Fertilizers & Nutrients\n"
        "- 🦠 Plant Diseases & Treatment\n"
        "- 💧 Irrigation & Water Management\n"
        "- 🐛 Pest Control (IPM)\n"
        "- 🌍 Soil Health & Analysis\n"
        "- 🌦️ Weather-Based Farming\n"
        "- 🌿 Organic Farming\n"
        "- 📈 Yield Improvement\n\n"
        "📸 **Upload a plant photo** for disease detection!\n"
        "🎤 **Use voice input** to speak your question!\n\n"
        + (f"*Current crop context: **{crop_context}***" if crop_context else "")
    )


# ── Gemini integration ────────────────────────────────────────────────────
def _gemini_chat(text: str, image_bytes: Optional[bytes], crop_context: str) -> str:
    """Send query to Gemini 1.5 Flash. Returns markdown response string."""
    import google.generativeai as genai
    from PIL import Image

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=_SYSTEM_PROMPT,
    )

    parts = []
    if crop_context:
        parts.append(f"[Context: The AgroVision crop prediction model recommends: {crop_context}]\n\n")
    parts.append(text)

    if image_bytes:
        img = Image.open(BytesIO(image_bytes))
        parts.append(img)

    response = model.generate_content(parts)
    return response.text


# ── Public API ─────────────────────────────────────────────────────────────
def chat(
    text: str,
    image_bytes: Optional[bytes] = None,
    crop_context: str = "",
) -> dict:
    """
    Main entry point for the conversational engine.

    Parameters
    ----------
    text         : user's text query
    image_bytes  : raw bytes of an uploaded image (optional)
    crop_context : top predicted crop from the existing prediction module

    Returns
    -------
    dict with keys: response (str), mode (str), success (bool)
    """
    if GEMINI_API_KEY:
        try:
            answer = _gemini_chat(text, image_bytes, crop_context)
            return {"response": answer, "mode": "gemini", "success": True}
        except Exception as exc:
            # Graceful degradation
            fallback = get_offline_response(text, crop_context)
            return {
                "response": fallback + f"\n\n*⚠️ Gemini unavailable: {exc}*",
                "mode": "offline",
                "success": True,
            }
    else:
        answer = get_offline_response(text, crop_context)
        note = "\n\n---\n*💡 Add `GEMINI_API_KEY` to `.env` for full AI-powered responses.*"
        return {"response": answer + note, "mode": "offline", "success": True}

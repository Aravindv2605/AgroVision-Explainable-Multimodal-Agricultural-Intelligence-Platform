"""
disease_detector.py
-------------------
Plant disease detection from crop images.

Priority:
  1. Google Gemini Vision  (if GEMINI_API_KEY set)
  2. Offline symptom knowledge base

Returns a structured dict with: disease name, symptoms,
causes, prevention, organic & chemical treatment, urgency.
"""

import os
from io import BytesIO
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

_VISION_PROMPT = """
You are an expert plant pathologist and agricultural AI assistant.
Analyze the provided plant image carefully.

Respond ONLY in this structured markdown format:

**🔍 Disease / Issue Detected:** [name or "Healthy Plant"]
**📊 Confidence Level:** [High / Medium / Low]
**🌿 Crop Identified:** [crop name if identifiable]

**🔬 Symptoms Observed:**
- [symptom 1]
- [symptom 2]

**⚗️ Probable Cause:** [Fungal / Bacterial / Viral / Pest / Nutrient Deficiency / Unknown]

**🌿 Organic Treatment:**
- [remedy 1]
- [remedy 2]

**💊 Chemical Treatment:**
- [chemical + dosage]
- [safety note]

**🛡️ Prevention Tips:**
- [tip 1]
- [tip 2]
- [tip 3]

**⚡ Urgency:** [Immediate Action / Monitor Closely / Low Priority]

If the image is NOT a plant, say: "No plant detected in the image. Please upload a clear photo of a crop leaf or plant."
"""

_OFFLINE_RESPONSE = """**🔍 Plant Disease Analysis — Offline Mode**

*📸 Image received. For AI-powered analysis, add your `GEMINI_API_KEY` to the `.env` file.*

**Visual Symptom Checker:**
| What You See | Likely Issue | Action |
|---|---|---|
| 🟡 Yellow leaves | N deficiency / Mosaic virus | Soil test + Urea spray |
| 🟤 Brown/black spots | Fungal blight / Bacterial spot | Neem oil / Copper fungicide |
| ⬜ White powder | Powdery mildew | Wettable sulfur / Carbendazim |
| 🥀 Wilting | Fusarium wilt / Root rot / Drought | Check roots + irrigation |
| 🕳️ Holes in leaves | Caterpillar / Beetle feeding | Bt spray / Chlorpyrifos |
| 🌀 Leaf curling | Aphids / Leaf curl virus | Neem oil / Imidacloprid |
| 🔴 Reddish discolor | P deficiency / Anthracnose | DAP application |
| ⬛ Black lesions | Anthracnose / Black rot | Mancozeb 75% WP spray |

**General First-Aid Protocol:**
1. **Isolate** affected plants immediately
2. **Remove** severely infected leaves/branches
3. **Spray Neem Oil 5%** as broad-spectrum organic control
4. **Apply Trichoderma viride** 2.5 kg/ha for biocontrol
5. **Improve drainage** to reduce root diseases
6. **Consult your KVK** (Krishi Vigyan Kendra) for lab-based diagnosis

**Fungicide Quick Guide:**
| Type | Product | Dosage |
|---|---|---|
| Broad fungal | Mancozeb 75% WP | 2.5 g/L water |
| Systemic | Carbendazim 50% WP | 1 g/L water |
| Preventive | Copper Oxychloride | 3 g/L water |
| Organic | Trichoderma viride | 2.5 kg/ha soil |
"""


def analyze_image(image_bytes: bytes) -> dict:
    """
    Analyze a plant image for disease/pest/nutrient issues.

    Parameters
    ----------
    image_bytes : raw bytes of the uploaded image

    Returns
    -------
    dict: { success, analysis (markdown str), mode, confidence }
    """
    if not image_bytes:
        return {"success": False, "analysis": "No image provided.", "mode": "error"}

    if GEMINI_API_KEY:
        return _analyze_with_gemini(image_bytes)
    else:
        return {
            "success": True,
            "analysis": _OFFLINE_RESPONSE,
            "mode": "offline",
            "confidence": "N/A",
        }


def _analyze_with_gemini(image_bytes: bytes) -> dict:
    try:
        import google.generativeai as genai
        from PIL import Image

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        image = Image.open(BytesIO(image_bytes))
        response = model.generate_content([_VISION_PROMPT, image])

        return {
            "success": True,
            "analysis": response.text,
            "mode": "gemini_vision",
            "confidence": "AI-Powered",
        }
    except Exception as exc:
        return {
            "success": True,
            "analysis": _OFFLINE_RESPONSE + f"\n\n*⚠️ Gemini Vision error: {exc}*",
            "mode": "offline_fallback",
            "confidence": "N/A",
        }

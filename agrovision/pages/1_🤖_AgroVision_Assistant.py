"""
pages/1_🤖_AgroVision_Assistant.py
------------------------------------
AgroVision Assistant — Multimodal AI Farming Companion

Streamlit multipage app page. Run via:  streamlit run dashboard.py

Features:
  • Text / Image / Voice chat with AgroBrain (Gemini or offline)
  • Plant disease detection from uploaded photo
  • Live weather + farming alerts panel
  • Full crop advisory card (integrates with crop prediction)
  • TTS voice response playback
"""

import io
import base64
import requests
import streamlit as st

API_URL = "http://localhost:8000/api/v1"

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroVision Assistant",
    page_icon="🤖",
    layout="wide",
)

from styles import inject_custom_css
inject_custom_css()



# ── Helpers ────────────────────────────────────────────────────────────────
def api_chat(text: str, image_bytes: bytes = None, crop_context: str = "") -> dict:
    payload = {"text": text, "crop_context": crop_context}
    if image_bytes:
        payload["image_b64"] = base64.b64encode(image_bytes).decode()
    try:
        r = requests.post(f"{API_URL}/assistant/chat", json=payload, timeout=30)
        return r.json() if r.ok else {"response": f"API Error: {r.status_code}", "mode": "error", "success": False}
    except Exception as e:
        return {"response": f"Cannot reach API: {e}", "mode": "error", "success": False}


def api_disease(image_bytes: bytes) -> dict:
    try:
        r = requests.post(
            f"{API_URL}/assistant/disease",
            files={"file": ("image.jpg", image_bytes, "image/jpeg")},
            timeout=30,
        )
        return r.json() if r.ok else {"analysis": f"API Error: {r.status_code}", "success": False}
    except Exception as e:
        return {"analysis": f"Cannot reach API: {e}", "success": False}


def api_weather(lat: float, lon: float) -> dict:
    try:
        r = requests.get(f"{API_URL}/assistant/weather", params={"lat": lat, "lon": lon}, timeout=10)
        return r.json() if r.ok else {}
    except Exception:
        return {}


def api_tts(text: str, lang: str = "English") -> bytes:
    try:
        r = requests.post(
            f"{API_URL}/assistant/tts",
            data={"text": text[:600], "language": lang},
            timeout=20,
        )
        return r.content if r.ok and r.headers.get("content-type", "").startswith("audio") else b""
    except Exception:
        return b""


def api_crop_advice(crop: str, score: float, soil: dict, climate: dict) -> dict:
    try:
        payload = {"crop": crop, "score": score, "soil": soil, "climate": climate, "use_gemini": False}
        r = requests.post(f"{API_URL}/assistant/crop-advice", json=payload, timeout=20)
        return r.json() if r.ok else {}
    except Exception:
        return {}


def render_chat_messages():
    """Render all chat messages from session state."""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f'''
                <div class="msg-container">
                    <div class="msg-user-box">
                        <div class="msg-content">🧑‍🌾 {msg["content"]}</div>
                    </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'''
                <div class="msg-container">
                    <div class="msg-ai-box">
                        <div class="msg-content">🤖 {msg["content"]}</div>
                    </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )


# ── Session state init ─────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Vanakkam! I'm AgroVision Assistant** — your AI farming companion.\n\n"
                "I can help you with:\n"
                "🌱 Crop guidance • 🦠 Disease detection • 💧 Irrigation advice\n"
                "🌦️ Weather alerts • 🐛 Pest control • 🌍 Soil health\n\n"
                "📸 Upload a plant photo or 🎤 use your microphone to get started!"
            ),
        }
    ]
if "crop_context" not in st.session_state:
    st.session_state.crop_context = ""
if "tts_lang" not in st.session_state:
    st.session_state.tts_lang = "English"
if "last_weather" not in st.session_state:
    st.session_state.last_weather = None


# ── Header (Hero Section) ──────────────────────────────────────────────────
st.markdown('''
<div class="hero-container">
    <div class="hero-content">
        <h1 class="hero-title">🤖 AgroVision Assistant</h1>
        <p class="hero-subtitle">AI-Powered Multimodal Agricultural Companion — Text • Voice • Image</p>
    </div>
</div>
''', unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Assistant Settings")

    st.markdown("### 🛰️ Crop Context")
    crop_ctx = st.text_input(
        "Predicted crop (from predictor)",
        value=st.session_state.crop_context,
        placeholder="e.g. Rice, Wheat...",
        help="If you ran the crop predictor, enter the top result here for context-aware advice",
    )
    st.session_state.crop_context = crop_ctx
    if crop_ctx:
        st.success(f"✅ Context: **{crop_ctx}**")

    st.divider()

    st.markdown("### 🔊 Voice Settings")
    st.session_state.tts_lang = st.selectbox("TTS Language", ["English", "Tamil"], index=0)
    tts_enabled = st.checkbox("🔊 Auto-play voice response", value=True)

    st.divider()

    # ── Live Weather Panel ─────────────────────────────────────────────────
    st.markdown("### 🌦️ Weather Intelligence")
    lat = st.number_input("Latitude", value=11.1, format="%.4f")
    lon = st.number_input("Longitude", value=77.5, format="%.4f")

    if st.button("🌤️ Fetch Weather", use_container_width=True):
        with st.spinner("Fetching weather…"):
            st.session_state.last_weather = api_weather(lat, lon)

    weather = st.session_state.last_weather
    if weather:
        cur = weather.get("current", {})
        desc = cur.get('description','').lower()
        w_emoji = "☀️"
        if "rain" in desc or "shower" in desc:
            w_emoji = "🌧️"
        elif "cloud" in desc or "overcast" in desc:
            w_emoji = "☁️"
        elif "mist" in desc or "fog" in desc:
            w_emoji = "🌫️"
        elif "snow" in desc or "sleet" in desc:
            w_emoji = "❄️"
        
        st.markdown(f"""
<div class="weather-card-premium">
  <div class="weather-header">
    <b style="font-size: 1.1rem; color: white;">📍 {weather.get('location','—')}</b>
    <span style="font-size: 1.3rem;">{w_emoji}</span>
  </div>
  <div style="font-size: 0.95rem; margin-bottom: 8px;">
    🌡️ <b>Temp:</b> {cur.get('temp_c','—')}°C <br>
    💧 <b>Humidity:</b> {cur.get('humidity_pct','—')}% <br>
    🌬️ <b>Wind:</b> {cur.get('wind_kph','—')} km/h <br>
    🌧️ <b>Rain:</b> {cur.get('rain_mm',0)} mm
  </div>
  <div style="background: rgba(255,255,255,0.04); padding: 6px 10px; border-radius: 6px; font-size: 0.85rem; border-left: 3px solid #4CAF50;">
    <i>{cur.get('description','')}</i>
  </div>
</div>
""", unsafe_allow_html=True)
        for alert in weather.get("alerts", []):
            st.markdown(f"""
<div class="alert-card-premium">
  <b style="color: #FFA000; font-size: 0.9rem;">⚠️ Alert: {alert}</b>
</div>
""", unsafe_allow_html=True)
        with st.expander("🌾 Farming Advice"):
            st.markdown(weather.get("farming_advice", ""))

    st.divider()
    st.markdown("### ℹ️ About")
    st.markdown("""
**AgroVision Assistant v1.0**
- 🤖 Powered by Google Gemini
- 🌾 15 crop knowledge base
- 🦠 Plant disease detection
- 🌦️ Real-time weather intel
- 🔊 English + Tamil TTS

*Add API keys to `.env` for full AI features*
""")


# ── Main tabs ──────────────────────────────────────────────────────────────
tab_chat, tab_disease, tab_advisor, tab_voice = st.tabs([
    "💬 AI Chat",
    "🦠 Disease Detector",
    "🌾 Crop Advisor",
    "🎤 Voice Assistant",
])


# ══════════════════════════════════════════════════════════════════
# TAB 1 — AI CHAT
# ══════════════════════════════════════════════════════════════════
with tab_chat:
    st.markdown("### 💬 Chat with AgroVision Assistant")

    # Quick actions row
    st.markdown("**⚡ Quick Questions:**")
    q_cols = st.columns(4)
    quick_questions = [
        "Which fertilizer is best for rice?",
        "Why are my leaves turning yellow?",
        "How to increase crop yield?",
        "How to improve soil fertility?",
    ]
    quick_trigger = None
    for i, (col, q) in enumerate(zip(q_cols, quick_questions)):
        if col.button(q[:28] + "…", key=f"quick_{i}", use_container_width=True):
            quick_trigger = q

    st.divider()

    # Chat history display
    chat_container = st.container(height=380)
    with chat_container:
        render_chat_messages()

    # Image attachment
    with st.expander("📎 Attach an Image (optional)"):
        chat_img = st.file_uploader(
            "Upload a plant photo to ask about it",
            type=["jpg", "jpeg", "png", "webp"],
            key="chat_image_upload",
        )
        if chat_img:
            st.image(chat_img, caption="Attached image", width=200)

    # Text input + send
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_send = st.columns([5, 1])
        with col_input:
            user_text = st.text_input(
                "Ask anything about farming…",
                placeholder="e.g. How often should I irrigate wheat?",
                label_visibility="collapsed",
            )
        with col_send:
            send_btn = st.form_submit_button("Send 🚀", use_container_width=True)

    # Handle quick-action or form submit
    final_query = quick_trigger or (user_text if send_btn and user_text.strip() else None)

    if final_query:
        # Add user message
        img_bytes = chat_img.read() if chat_img else None
        display_text = final_query
        if img_bytes:
            display_text += " 📸 [image attached]"

        st.session_state.messages.append({"role": "user", "content": display_text})

        with st.spinner("🤖 AgroVision is thinking…"):
            result = api_chat(final_query, img_bytes, st.session_state.crop_context)
            response_text = result.get("response", "Sorry, I could not process that.")
            mode = result.get("mode", "unknown")

        st.session_state.messages.append({"role": "assistant", "content": response_text})

        # TTS
        if tts_enabled:
            with st.spinner("🔊 Generating voice response…"):
                audio = api_tts(response_text, st.session_state.tts_lang)
            if audio:
                st.audio(audio, format="audio/mp3")

        st.markdown(f'<span class="mode-badge">Mode: {mode}</span>', unsafe_allow_html=True)
        st.rerun()

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = [st.session_state.messages[0]]  # keep greeting
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# TAB 2 — DISEASE DETECTOR
# ══════════════════════════════════════════════════════════════════
with tab_disease:
    st.markdown("### 🦠 Plant Disease Detection")
    st.info("📸 Upload a clear photo of your affected crop leaf or plant part for AI-powered diagnosis.")

    col_upload, col_result = st.columns([1, 1])

    with col_upload:
        disease_img = st.file_uploader(
            "Upload crop image",
            type=["jpg", "jpeg", "png", "webp"],
            key="disease_upload",
        )
        if disease_img:
            st.image(disease_img, caption="Uploaded Plant Image", use_column_width=True)
            analyze_btn = st.button("🔬 Analyze Disease", type="primary", use_container_width=True)

            if analyze_btn:
                with st.spinner("🧬 Analyzing plant image…"):
                    result = api_disease(disease_img.read())

                with col_result:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown("#### 🔍 Analysis Result")
                    if result.get("mode"):
                        st.markdown(f'<span class="mode-badge">Mode: {result["mode"]}</span>', unsafe_allow_html=True)
                    st.markdown(result.get("analysis", "No result returned."))
                    st.markdown('</div>', unsafe_allow_html=True)

                    # TTS for disease result
                    if tts_enabled:
                        audio = api_tts(result.get("analysis", ""), st.session_state.tts_lang)
                        if audio:
                            st.audio(audio, format="audio/mp3")
        else:
            with col_result:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("""
#### 🔬 How it works

1. **Upload** a clear photo of the affected plant
2. Click **Analyze Disease**
3. Get instant AI diagnosis including:
   - Disease/pest name
   - Symptoms observed
   - Probable cause
   - Organic & chemical treatment
   - Prevention tips
   - Urgency level

**Best practices for accurate results:**
- Take photo in natural light
- Focus on the affected leaf/stem
- Include both healthy and diseased parts
- Avoid blurry or dark images
""")
                st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 3 — CROP ADVISOR
# ══════════════════════════════════════════════════════════════════
with tab_advisor:
    st.markdown("### 🌾 Intelligent Crop Advisory")
    st.markdown("Get complete farming guidance for any crop — enhanced with the AgroVision prediction results.")

    col_form, col_advice = st.columns([1, 1.3])

    with col_form:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### Enter Crop Details")

        CROPS = [
            "rice", "wheat", "maize", "sugarcane", "cotton",
            "soybean", "groundnut", "tomato", "onion", "potato",
            "turmeric", "banana", "mango", "coconut", "black_gram",
        ]
        selected_crop = st.selectbox(
            "Select Crop",
            [c.replace("_", " ").title() for c in CROPS],
            index=0,
        )
        crop_key = selected_crop.lower().replace(" ", "_")
        confidence = st.slider("Prediction Confidence (%)", 0, 100, 75)

        st.markdown("**Optional: Soil Parameters**")
        soil_n = st.number_input("Nitrogen (kg/ha)", 0, 150, 90)
        soil_p = st.number_input("Phosphorus (kg/ha)", 0, 100, 42)
        soil_k = st.number_input("Potassium (kg/ha)", 0, 300, 43)
        soil_ph = st.number_input("Soil pH", 3.5, 9.5, 6.5)

        st.markdown("**Optional: Climate Parameters**")
        rainfall = st.number_input("Annual Rainfall (mm)", 0, 5000, 800)
        temp_max = st.number_input("Max Temperature (°C)", 10, 50, 32)

        get_advice_btn = st.button("🌱 Get Full Advisory", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_advice:
        if get_advice_btn:
            soil = {"N": soil_n, "P": soil_p, "K": soil_k, "pH": soil_ph}
            climate = {"annual_rainfall_mm": rainfall, "temp_max": temp_max}

            with st.spinner(f"📋 Generating advisory for {selected_crop}…"):
                result = api_crop_advice(
                    crop=crop_key,
                    score=confidence / 100,
                    soil=soil,
                    climate=climate,
                )

            if result.get("advice_md"):
                st.markdown(result["advice_md"])

                if tts_enabled:
                    audio = api_tts(result["advice_md"][:600], st.session_state.tts_lang)
                    if audio:
                        st.audio(audio, format="audio/mp3")
            else:
                st.warning("Could not generate advisory. Is the API running?")
        else:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("""
#### 📚 What you'll get

Complete farming guide covering:
- ✅ Why this crop suits your conditions
- 🌍 Soil preparation steps
- 💧 Irrigation schedule
- 🌱 Fertilizer calendar with dosage
- 🦠 Disease & pest risk profile
- 📈 Expected yield and income estimate
- 💡 5 expert farming tips

*Select a crop and click **Get Full Advisory** to start!*
""")
            st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 4 — VOICE ASSISTANT
# ══════════════════════════════════════════════════════════════════
with tab_voice:
    st.markdown("### 🎤 Voice Assistant")

    col_v1, col_v2 = st.columns([1, 1])

    with col_v1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 🎙️ Voice Input")
        st.info(
            "Click the microphone below to record your farming question. "
            "Your spoken words will be processed as a text query."
        )

        # Streamlit's native audio input (v1.37+)
        try:
            audio_input = st.audio_input("🎙️ Speak your farming question")
            if audio_input:
                st.success("✅ Voice recorded!")
                st.audio(audio_input)

                # Transcribe using SpeechRecognition
                with st.spinner("🧠 Transcribing voice…"):
                    try:
                        import speech_recognition as sr
                        recognizer = sr.Recognizer()
                        audio_bytes_io = io.BytesIO(audio_input.getvalue())
                        with sr.AudioFile(audio_bytes_io) as source:
                            audio_data = recognizer.record(source)
                        transcribed = recognizer.recognize_google(audio_data)
                        st.success(f"📝 Transcribed: **{transcribed}**")

                        # Send to chat
                        with st.spinner("🤖 Getting AI response…"):
                            result = api_chat(transcribed, crop_context=st.session_state.crop_context)
                        response = result.get("response", "")

                        st.markdown("#### 🤖 AI Response")
                        st.markdown(response)

                        # TTS
                        audio_out = api_tts(response, st.session_state.tts_lang)
                        if audio_out:
                            st.markdown("#### 🔊 Voice Response")
                            st.audio(audio_out, format="audio/mp3")

                    except ImportError:
                        st.warning(
                            "🔧 Install `SpeechRecognition` for voice transcription:\n"
                            "`pip install SpeechRecognition`\n\n"
                            "You can type your question in the **AI Chat** tab instead."
                        )
                    except Exception as e:
                        st.warning(f"Voice transcription failed: {e}\n\nType your question in the **Chat** tab.")
        except Exception:
            st.warning(
                "🎙️ Voice input requires Streamlit ≥ 1.37.\n\n"
                "**Alternative:** Type your question in the **💬 AI Chat** tab."
            )

        st.markdown('</div>', unsafe_allow_html=True)

    with col_v2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 🔊 Text-to-Speech Test")
        st.markdown("Type any farming text below to hear it spoken aloud:")
        tts_test_text = st.text_area(
            "Text to speak",
            value="Rice is recommended because your soil and climate conditions are highly suitable.",
            height=100,
        )
        tts_test_lang = st.selectbox("Language", ["English", "Tamil"], key="tts_test_lang")

        if st.button("▶️ Play Voice", use_container_width=True):
            with st.spinner("🔊 Generating audio…"):
                audio = api_tts(tts_test_text, tts_test_lang)
            if audio:
                st.audio(audio, format="audio/mp3")
                st.success("✅ Voice response ready!")
            else:
                st.error(
                    "TTS unavailable. Install gTTS:\n"
                    "`pip install gTTS`"
                )

        st.markdown("---")
        st.markdown("""
**Voice Features:**
- 🎤 Record question via microphone
- 🧠 Auto-transcription (SpeechRecognition)
- 🔊 AI voice response (gTTS)
- 🌐 English + Tamil support

**Install voice dependencies:**
```
pip install gTTS SpeechRecognition
```
""")
        st.markdown('</div>', unsafe_allow_html=True)

"""
dashboard.py
------------
AgroVision Streamlit Dashboard
Run: streamlit run dashboard.py
Make sure the API is running: uvicorn src.api.main:app --reload
"""

import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

API_URL = "http://localhost:8000/api/v1"

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroVision — Smart Crop Advisor",
    page_icon="🌾",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
from styles import inject_custom_css
inject_custom_css()


# ── Crop info dictionary ───────────────────────────────────────────────────
CROP_INFO = {
    "rice":       {"emoji": "🌾", "season": "Kharif",     "water": "High",   "tip": "Best in waterlogged fields"},
    "wheat":      {"emoji": "🌿", "season": "Rabi",       "water": "Medium", "tip": "Ideal in cool dry winters"},
    "maize":      {"emoji": "🌽", "season": "Kharif",     "water": "Medium", "tip": "Great for sandy loam soil"},
    "sugarcane":  {"emoji": "🎋", "season": "Annual",     "water": "High",   "tip": "Needs heavy irrigation"},
    "cotton":     {"emoji": "🌸", "season": "Kharif",     "water": "Low",    "tip": "Thrives in black soil"},
    "soybean":    {"emoji": "🫘", "season": "Kharif",     "water": "Medium", "tip": "Nitrogen-fixing crop"},
    "groundnut":  {"emoji": "🥜", "season": "Kharif",     "water": "Low",    "tip": "Well-drained sandy soil"},
    "black_gram": {"emoji": "🫘", "season": "Kharif",     "water": "Low",    "tip": "Short duration crop"},
    "turmeric":   {"emoji": "🟡", "season": "Kharif",     "water": "Medium", "tip": "High market value spice"},
    "onion":      {"emoji": "🧅", "season": "Rabi",       "water": "Medium", "tip": "Good drainage needed"},
    "potato":     {"emoji": "🥔", "season": "Rabi",       "water": "Medium", "tip": "Cool climate preferred"},
    "tomato":     {"emoji": "🍅", "season": "All season", "water": "Medium", "tip": "High profit vegetable"},
    "banana":     {"emoji": "🍌", "season": "Annual",     "water": "High",   "tip": "Tropical humid climate"},
    "mango":      {"emoji": "🥭", "season": "Annual",     "water": "Low",    "tip": "Deep well-drained soil"},
    "coconut":    {"emoji": "🥥", "season": "Annual",     "water": "Medium", "tip": "Coastal sandy soil"},
}


def get_crop_info(crop):
    return CROP_INFO.get(crop, {"emoji": "🌱", "season": "N/A", "water": "N/A", "tip": "N/A"})


@st.cache_data
def load_region_mapping():
    """Returns a dict mapping {state: [districts]} from the raw soil data."""
    try:
        df = pd.read_csv("data/raw/soil_data.csv")
        mapping = df.groupby("state")["district"].unique().apply(list).to_dict()
        return mapping
    except:
        # Fallback if file not found
        return {"Tamil Nadu": ["Thanjavur", "Coimbatore"]}


@st.cache_data
def get_district_data(state, district):
    """Returns the default soil/climate data for a specific district."""
    try:
        df_soil = pd.read_csv("data/raw/soil_data.csv")
        df_climate = pd.read_csv("data/raw/climate_data.csv")

        # Get soil data
        district_soil = df_soil[(df_soil["state"] == state) & (df_soil["district"] == district)].iloc[0]

        # Get climate data (average across months/years)
        region_id = f"{district.replace(' ', '_')}_{state.replace(' ', '_')}"
        district_climate = df_climate[df_climate["region_id"] == region_id]
        if district_climate.empty:
            # Fallback if region_id doesn't match exactly
            district_climate = df_climate[(df_climate["state"] == state) & (df_climate["district"] == district)]

        avg_climate = district_climate.mean(numeric_only=True)

        return {
            "soil": district_soil.to_dict(),
            "climate": avg_climate.to_dict()
        }
    except:
        return None


def check_api():
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        return r.status_code == 200
    except:
        return False


def get_predictions(payload):
    try:
        r = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None


def get_explanation(payload):
    try:
        r = requests.post(f"{API_URL}/explain", json=payload, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None


# ── API status check early ──────────────────────────────────────────────────
api_ok = check_api()

# ── Header (Hero Section) ──────────────────────────────────────────────────
st.markdown('''
<div class="hero-container">
    <div class="hero-content">
        <h1 class="hero-title">🌾 AgroVision</h1>
        <p class="hero-subtitle">AI-Powered Explainable Crop Intelligence Platform</p>
    </div>
</div>
''', unsafe_allow_html=True)

# ── Layout: sidebar inputs + main results ─────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Control Center")
    if api_ok:
        st.markdown('<div class="status-badge" style="margin-bottom: 15px;">🟢 AI Engine Online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge warning" style="margin-bottom: 15px;">🔴 AI Engine Offline</div>', unsafe_allow_html=True)
        st.error("❌ API is not running. Please start it: `uvicorn src.api.main:app --reload`")
        st.stop()

    st.markdown("### 📍 Region Details")
    mapping = load_region_mapping()
    states = sorted(list(mapping.keys()))
    state = st.selectbox("Select State", options=states, index=0)

    districts = sorted(mapping[state])
    district = st.selectbox("Select District", options=districts, index=0)

    # Load district-specific defaults
    defaults = get_district_data(state, district)


    # Use defaults if available, otherwise fallback to hardcoded
    def_soil = defaults["soil"] if defaults else {}
    def_clim = defaults["climate"] if defaults else {}

    latitude   = st.number_input("Latitude",  value=float(def_soil.get("latitude", 11.1)), min_value=-90.0,  max_value=90.0)
    longitude  = st.number_input("Longitude", value=float(def_soil.get("longitude", 77.5)), min_value=-180.0, max_value=180.0)

    st.markdown("## 🌱 Soil Parameters")
    N  = st.slider("Nitrogen (N) kg/ha",       0,   150, int(def_soil.get("N", 90)))
    P  = st.slider("Phosphorus (P) kg/ha",     0,   100, int(def_soil.get("P", 42)))
    K  = st.slider("Potassium (K) kg/ha",      0,   300, int(def_soil.get("K", 43)))
    pH = st.slider("Soil pH",                  3.5, 9.5, float(def_soil.get("pH", 6.5)))
    moisture       = st.slider("Moisture (%)", 0,   100, int(def_soil.get("moisture", 60)))
    organic_matter = st.slider("Organic Matter (%)", 0.0, 10.0, float(def_soil.get("organic_matter", 2.5)))

    st.markdown("## 🌦️ Climate Parameters")
    # Note: annual rainfall is sum of monthly in data, but we use it as a parameter here
    # If we have monthly data, we can sum it up
    rainfall_sum = def_clim.get("rainfall_mm", 800/12) * 12 # Rough estimate if only monthly mean available
    rainfall       = st.slider("Annual Rainfall (mm)",  0,   3000, int(rainfall_sum))
    temp_max       = st.slider("Max Temperature (°C)",  10,  50,   int(def_clim.get("temp_max", 35)))
    temp_min       = st.slider("Min Temperature (°C)",  0,   45,   int(def_clim.get("temp_min", 22)))
    humidity       = st.slider("Humidity (%)",          0,   100,  int(def_clim.get("humidity", 75)))
    solar_rad      = st.slider("Solar Radiation",       0,   30,   int(def_clim.get("solar_radiation", 18)))
    ndvi           = st.slider("NDVI (Vegetation Index)", -1.0, 1.0, 0.55)

    region_id = f"{district}, {state}"

    top_k = st.selectbox("Number of Recommendations", [3, 5, 8, 10], index=1)

    predict_btn = st.button("🔍 Get Crop Recommendations", type="primary",
                            use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────────────
if predict_btn:
    payload = {
        "region_id": region_id,
        "latitude":  latitude,
        "longitude": longitude,
        "soil": {
            "N": N, "P": P, "K": K,
            "pH": pH, "moisture": moisture,
            "organic_matter": organic_matter,
        },
        "climate": {
            "annual_rainfall_mm": rainfall,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "humidity": humidity,
            "solar_radiation": solar_rad,
        },
        "ndvi_mean": ndvi,
        "top_k": top_k,
    }

    with st.spinner("🤖 AI is analyzing your soil and climate data..."):
        result = get_predictions(payload)
        explanation = get_explanation(payload)

    if result is None:
        st.error("Prediction failed. Make sure the API is running.")
    else:
        recs = result["recommendations"]

        # ── Summary metrics ────────────────────────────────────────────────
        st.markdown("## 🎯 AI Recommendations")
        st.markdown(f"**Region:** `{region_id}` | **Location:** {latitude}°N, {longitude}°E")

        top = recs[0]
        info = get_crop_info(top["crop"])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🥇 Top Crop",       f"{info['emoji']} {top['crop'].replace('_',' ').title()}")
        m2.metric("📊 AI Score",        f"{top['score']:.1%}")
        m3.metric("💰 Profit Index",    f"{top['profit_index']:.1%}")
        m4.metric("🌱 Season",          info["season"])

        st.divider()

        # ── Two columns: cards + chart ─────────────────────────────────────
        col_cards, col_chart = st.columns([1, 1])

        with col_cards:
            st.markdown("### 🌾 Performance Ranking")
            rank_colors = ["#2E7D32", "#43A047", "#66BB6A", "#81C784", "#A5D6A7"]
            for i, rec in enumerate(recs):
                info = get_crop_info(rec["crop"])
                color = rank_colors[i] if i < len(rank_colors) else "#555"
                st.markdown(f"""
                <div class="glass-card" style="border-left: 5px solid {color} !important;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <b style="font-size:1.1rem; color:white;">{info['emoji']} #{rec['rank']} — {rec['crop'].replace('_',' ').title()}</b>
                        <span style="background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; color: #4CAF50;">
                            SCORE: {rec['score']:.3f}
                        </span>
                    </div>
                    <div style="margin-top: 8px; color: #BDBDBD; font-size: 0.9rem;">
                        💰 Profit Potential: <b style="color:#FFA000">{rec['profit_index']:.1%}</b> &nbsp;|&nbsp;
                        🤖 XGB Probability: {rec['xgb_prob']:.3f}<br>
                        📅 Seasonality: {info['season']} &nbsp;|&nbsp;
                        💧 Water Footprint: {info['water']}
                    </div>
                    <div style="background: rgba(255,255,255,0.03); padding: 8px; border-radius: 8px; margin-top: 10px; border-left: 3px solid #4CAF50;">
                        <i style="color:white;">{info['tip']}</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col_chart:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 📈 Analytics Overview")
            crops  = [r["crop"].replace("_", " ").title() for r in recs]
            scores = [r["score"] for r in recs]
            profits = [r["profit_index"] for r in recs]
 
            fig = go.Figure()
            fig.add_trace(go.Bar(name="AI Predictor Score", x=crops, y=scores,
                                 marker_color="#2E7D32", marker_line_color="#4CAF50", marker_line_width=1.5,
                                 hovertemplate="AI Score: %{y:.1%}<extra></extra>"))
            fig.add_trace(go.Bar(name="Profit Index (Expected)", x=crops, y=profits,
                                 marker_color="#FFA000", marker_line_color="#FFB300", marker_line_width=1.5,
                                 hovertemplate="Profit Potential: %{y:.1%}<extra></extra>"))
            fig.update_layout(
                template='plotly_dark',
                barmode="group",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", size=12, family="Inter"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white")),
                margin=dict(t=50, b=50, l=50, r=50),
                height=380,
                xaxis=dict(tickfont=dict(color="white"), gridcolor="rgba(255,255,255,0.08)"),
                yaxis=dict(tickfont=dict(color="white"), gridcolor="rgba(255,255,255,0.08)"),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Pie chart
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 🥧 Resource Allocation")
            fig2 = px.pie(
                values=scores, names=crops,
                color_discrete_sequence=["#1B5E20", "#2E7D32", "#388E3C", "#4CAF50", "#66BB6A", "#81C784", "#A5D6A7"],
                hole=0.4,
            )
            fig2.update_traces(
                textposition='inside',
                textinfo='percent+label',
                insidetextfont=dict(color='white', size=11, family="Inter"),
                outsidetextfont=dict(color='white', size=11, family="Inter"),
                hovertemplate="<b>%{label}</b><br>AI Suitability: %{percent}<extra></extra>"
            )
            fig2.update_layout(
                template='plotly_dark',
                margin=dict(t=60, b=20, l=20, r=20), 
                height=320,
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", family="Inter"),
                legend=dict(font=dict(color="white"))
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── SHAP Explanation ───────────────────────────────────────────────
        if explanation:
            st.divider()
            st.markdown("## 🔍 Why was this crop recommended?")
            st.markdown(f"**Top recommendation: {info['emoji']} {explanation['crop'].replace('_',' ').title()}**")

            col_exp, col_drivers = st.columns([1, 1])

            with col_exp:
                st.info(explanation["explanation"])

            with col_drivers:
                if explanation["top_drivers"]:
                    st.markdown("**✅ Positive Factors:**")
                    for d in explanation["top_drivers"]:
                        st.success(f"**{d['description']}** → impact: +{d['impact']:.4f}")

                if explanation["top_suppressors"]:
                    st.markdown("**⚠️ Limiting Factors:**")
                    for d in explanation["top_suppressors"]:
                        st.warning(f"**{d['description']}** → impact: {d['impact']:.4f}")

        # ── Soil & Climate summary ─────────────────────────────────────────
        st.divider()
        st.markdown("## 📋 Input Summary")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🌱 Soil Data**")
            soil_df = pd.DataFrame({
                "Parameter": ["Nitrogen", "Phosphorus", "Potassium", "pH", "Moisture", "Organic Matter"],
                "Value":     [N, P, K, pH, moisture, organic_matter],
                "Unit":      ["kg/ha", "kg/ha", "kg/ha", "", "%", "%"],
            })
            st.dataframe(soil_df, hide_index=True, use_container_width=True)
        with c2:
            st.markdown("**🌦️ Climate Data**")
            climate_df = pd.DataFrame({
                "Parameter": ["Annual Rainfall", "Max Temp", "Min Temp", "Humidity", "Solar Radiation", "NDVI"],
                "Value":     [rainfall, temp_max, temp_min, humidity, solar_rad, ndvi],
                "Unit":      ["mm", "°C", "°C", "%", "MJ/m²", "index"],
            })
            st.dataframe(climate_df, hide_index=True, use_container_width=True)

else:
    # ── Landing View ──
    col_l1, col_l2 = st.columns([1, 1])
    with col_l1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🚀 Intelligence Suite Standby")
        st.write("The AgroVision prediction engine is ready to analyze your field data. Select a region and adjust soil parameters in the sidebar to begin.")
        st.markdown("""
        - 🌾 **Real-time Crop Suitability Predictions**
        - 📈 **Market Value & Profitability Index Projections**
        - 🔍 **SHAP Feature Importance & Multimodal Explanations**
        - 🛰️ **Satellite NDVI Vegetation Index Analysis**
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_l2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🛰️ Simulation Ecosystem")
        st.write("AgroVision integrates deep soil analysis, regional climate data, and satellite imagery datasets to simulate optimal agricultural roadmaps across the subcontinent.")
        st.markdown('''
        <div style="background: rgba(76, 175, 80, 0.1); border-left: 4px solid #4CAF50; padding: 14px; border-radius: 8px; margin-top: 15px;">
            <b style="color: #81C784;">🌱 Core Status:</b> <span style="color: #E0E0E0;">Operational • Active</span><br>
            <b style="color: #81C784;">🤖 AI Model:</b> <span style="color: #E0E0E0;">Ensemble XGB-LSTM v2.4</span>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card" style="text-align: center; padding: 60px; border: 1px dashed rgba(76, 175, 80, 0.3) !important;">', unsafe_allow_html=True)
    st.markdown("<h2 style='color: #4CAF50; margin-bottom: 10px;'>🌾 Simulation Engine Standby</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #BDBDBD; font-size: 1.1rem; max-width: 600px; margin: 0 auto;'>Configure your soil metrics and regional coordinates, then click <b>Get Crop Recommendations</b> in the control panel to launch precision analytics.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

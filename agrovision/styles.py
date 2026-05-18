import streamlit as st

import streamlit as st

def inject_custom_css():
    st.markdown('<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">', unsafe_allow_html=True)
    
    st.markdown('''<style>
:root {
  --primary: #2E7D32;
  --secondary: #4CAF50;
  --glow: rgba(76, 175, 80, 0.25);
  --bg-1: #050505;
  --bg-2: #0B0F0C;
  --bg-3: #121212;
  --card-bg: rgba(255, 255, 255, 0.06);
  --border: rgba(255, 255, 255, 0.12);
  --text-primary: #FFFFFF;
  --text-secondary: #E0E0E0;
  --text-muted: #BDBDBD;
  --accent-orange: #FFA000;
  --accent-blue: #29B6F6;
}

* {
  font-family: 'Inter', sans-serif;
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Poppins', sans-serif;
  color: var(--text-primary);
}

.stApp {
  background-color: var(--bg-1);
  background-image: 
    radial-gradient(circle at 10% 20%, rgba(46, 125, 50, 0.15) 0%, transparent 40%),
    radial-gradient(circle at 90% 80%, rgba(76, 175, 80, 0.1) 0%, transparent 40%),
    radial-gradient(circle at 50% 50%, rgba(11, 15, 12, 1) 0%, rgba(5, 5, 5, 1) 100%);
  background-attachment: fixed;
  color: var(--text-secondary);
}

/* Sidebar styling */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #050806 0%, #0C100D 100%) !important;
  border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
  color: var(--text-secondary) !important;
}

/* Glassmorphism Cards */
.glass-card {
  background: var(--card-bg) !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
  border: 1px solid var(--border) !important;
  border-radius: 16px !important;
  padding: 24px !important;
  margin-bottom: 20px !important;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
}

.glass-card:hover {
  transform: translateY(-4px) !important;
  border-color: rgba(76, 175, 80, 0.4) !important;
  box-shadow: 0 12px 40px var(--glow) !important;
}

/* Hero Section */
.hero-container {
  background: linear-gradient(135deg, rgba(46, 125, 50, 0.15) 0%, rgba(76, 175, 80, 0.08) 100%);
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 20px;
  padding: 40px 30px;
  text-align: center;
  margin-bottom: 30px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.hero-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(76, 175, 80, 0.15) 0%, transparent 60%);
  animation: rotateGlow 20s linear infinite;
  z-index: 0;
}

@keyframes rotateGlow {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 3rem;
  font-weight: 800;
  background: linear-gradient(135deg, #FFFFFF 30%, #4CAF50 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 10px;
  letter-spacing: -0.5px;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: var(--text-secondary);
  font-weight: 400;
  max-width: 700px;
  margin: 0 auto;
  opacity: 0.9;
}

/* Premium Buttons */
.stButton > button[kind="primary"], .stButton > button[type="primary"] {
  width: 100%;
  border-radius: 12px !important;
  padding: 12px 24px !important;
  background: linear-gradient(135deg, #2E7D32, #4CAF50) !important;
  color: white !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  font-weight: 600 !important;
  font-size: 0.95rem !important;
  text-transform: none !important;
  letter-spacing: 0.5px !important;
  box-shadow: 0 4px 15px rgba(46, 125, 50, 0.3) !important;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
}

.stButton > button[kind="primary"]:hover, .stButton > button[type="primary"]:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.5) !important;
  background: linear-gradient(135deg, #388E3C, #66BB6A) !important;
}

.stButton > button[kind="secondary"], .stButton > button:not([kind="primary"]):not([type="primary"]) {
  width: 100%;
  border-radius: 12px !important;
  padding: 10px 20px !important;
  background: rgba(255, 255, 255, 0.05) !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border) !important;
  font-weight: 500 !important;
  font-size: 0.9rem !important;
  text-transform: none !important;
  letter-spacing: 0.2px !important;
  box-shadow: none !important;
  transition: all 0.3s ease !important;
}

.stButton > button[kind="secondary"]:hover, .stButton > button:not([kind="primary"]):not([type="primary"]):hover {
  transform: translateY(-2px) !important;
  background: rgba(76, 175, 80, 0.15) !important;
  color: #4CAF50 !important;
  border-color: rgba(76, 175, 80, 0.4) !important;
  box-shadow: 0 4px 15px var(--glow) !important;
}

/* Metric styling */
[data-testid="stMetric"] {
  background: var(--card-bg) !important;
  padding: 20px !important;
  border-radius: 16px !important;
  border: 1px solid var(--border) !important;
  backdrop-filter: blur(8px) !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
  transition: all 0.3s ease !important;
}

[data-testid="stMetric"]:hover {
  border-color: rgba(76, 175, 80, 0.3) !important;
  box-shadow: 0 6px 25px rgba(76, 175, 80, 0.15) !important;
  transform: translateY(-2px) !important;
}

[data-testid="stMetricValue"] {
  color: var(--text-primary) !important;
  font-weight: 700 !important;
  font-size: 1.8rem !important;
}

[data-testid="stMetricLabel"] {
  color: var(--text-muted) !important;
  font-size: 0.9rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
}

/* Chat bubble aesthetics */
.msg-container {
  display: flex;
  margin-bottom: 16px;
  width: 100%;
}

.msg-user-box {
  background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 16px 16px 2px 16px !important;
  padding: 14px 18px !important;
  max-width: 80% !important;
  margin-left: auto !important;
  color: white !important;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
}

.msg-ai-box {
  background: rgba(255, 255, 255, 0.05) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid var(--border) !important;
  border-radius: 16px 16px 16px 2px !important;
  padding: 14px 18px !important;
  max-width: 80% !important;
  color: var(--text-secondary) !important;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
}

.msg-content {
  line-height: 1.5;
  font-size: 0.95rem;
}

/* Suggestion chips style */
.stButton button[key*="quick_"] {
  background: rgba(255, 255, 255, 0.05) !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border) !important;
  border-radius: 20px !important;
  padding: 8px 16px !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
  box-shadow: none !important;
  text-transform: none !important;
  letter-spacing: 0px !important;
}

.stButton button[key*="quick_"]:hover {
  background: rgba(76, 175, 80, 0.15) !important;
  color: #4CAF50 !important;
  border-color: #4CAF50 !important;
  transform: translateY(-1px) !important;
}

/* Custom styled weather card */
.weather-card-premium {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.12) 0%, rgba(255, 255, 255, 0.03) 100%) !important;
  border: 1px solid rgba(76, 175, 80, 0.25) !important;
  box-shadow: 0 8px 32px 0 rgba(76, 175, 80, 0.1) !important;
  border-radius: 16px !important;
  padding: 20px !important;
  color: var(--text-secondary) !important;
}

.weather-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 10px;
  margin-bottom: 12px;
}

.alert-card-premium {
  background: linear-gradient(135deg, rgba(255, 160, 0, 0.15) 0%, rgba(255, 255, 255, 0.03) 100%) !important;
  border: 1px solid rgba(255, 160, 0, 0.3) !important;
  box-shadow: 0 8px 32px 0 rgba(255, 160, 0, 0.1) !important;
  border-radius: 12px !important;
  padding: 12px 16px !important;
  margin-top: 10px;
}

/* Custom selectbox and slider styling to match green theme */
div[data-baseweb="select"] {
  background-color: rgba(255, 255, 255, 0.04) !important;
  border-radius: 10px !important;
  border: 1px solid var(--border) !important;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255, 255, 255, 0.03) !important;
  border-radius: 12px !important;
  padding: 6px !important;
  border: 1px solid var(--border) !important;
}

.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-muted) !important;
  border-radius: 8px !important;
  border: none !important;
  padding: 8px 16px !important;
  font-weight: 600 !important;
  transition: all 0.3s ease !important;
}

.stTabs [aria-selected="true"] {
  background: var(--primary) !important;
  color: white !important;
  box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3) !important;
}

/* Status Badge */
.status-badge {
  background: rgba(76, 175, 80, 0.15);
  color: #81C784;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  border: 1px solid rgba(76, 175, 80, 0.25);
  display: inline-block;
}

.status-badge.warning {
  background: rgba(255, 160, 0, 0.15);
  color: #FFB74D;
  border-color: rgba(255, 160, 0, 0.25);
}
</style>''', unsafe_allow_html=True)


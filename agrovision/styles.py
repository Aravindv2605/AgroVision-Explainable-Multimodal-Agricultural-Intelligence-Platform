import streamlit as st

def inject_custom_css():
    st.markdown('<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">', unsafe_allow_html=True)
    
    st.markdown('''<style>
:root {
--primary: #2E7D32;
--primary-light: #4CAF50;
--primary-glow: rgba(46, 125, 50, 0.4);
--secondary: #FFA000;
--bg-dark: #050505;
--card-bg: rgba(255, 255, 255, 0.06);
--card-border: rgba(255, 255, 255, 0.1);
--text-main: #FFFFFF;
--text-dim: #BDBDBD;
}

* { font-family: 'Outfit', sans-serif; }

.stApp {
background-color: var(--bg-dark);
background-image: 
radial-gradient(circle at top left, rgba(46, 125, 50, 0.18), transparent 35%),
radial-gradient(circle at bottom right, rgba(56, 142, 60, 0.12), transparent 35%);
color: var(--text-main);
}

[data-testid="stSidebar"] {
background: linear-gradient(180deg, #080808 0%, #0D0D0D 100%) !important;
border-right: 1px solid var(--card-border);
}

.glass-card {
background: var(--card-bg);
backdrop-filter: blur(12px);
-webkit-backdrop-filter: blur(12px);
border: 1px solid var(--card-border);
border-radius: 20px;
padding: 24px;
margin-bottom: 20px;
box-shadow: 0 8px 32px rgba(0,0,0,0.4);
transition: transform 0.3s ease, border-color 0.3s ease;
}

.glass-card:hover {
transform: translateY(-2px);
border-color: var(--primary-light);
}

.header-title {
font-size: 3.5rem;
font-weight: 700;
color: white !important;
letter-spacing: -1px;
margin-bottom: 0;
}

.header-sub {
font-size: 1.2rem;
color: var(--primary-light) !important;
font-weight: 400;
margin-top: 5px;
opacity: 0.9;
}

.stButton > button {
width: 100%; border-radius: 12px !important; padding: 14px 28px !important;
background: linear-gradient(135deg, #2E7D32, #43A047) !important;
color: white !important; border: none !important;
font-weight: 700 !important;
text-transform: uppercase;
letter-spacing: 1px;
box-shadow: 0 4px 15px var(--primary-glow);
transition: all 0.3s ease !important;
}

.stButton > button:hover {
transform: translateY(-2px);
box-shadow: 0 8px 25px var(--primary-glow);
filter: brightness(1.1);
}

[data-testid="stMetric"] {
background: var(--card-bg);
padding: 24px;
border-radius: 20px;
border: 1px solid var(--card-border);
backdrop-filter: blur(8px);
}

[data-testid="stMetricValue"] { 
color: var(--text-main) !important; 
font-weight: 700 !important;
}

[data-testid="stMetricLabel"] { 
color: var(--text-dim) !important; 
font-size: 1rem !important;
}

.stTabs [data-baseweb="tab-list"] { background: transparent !important; }
.stTabs [data-baseweb="tab"] {
background: var(--card-bg) !important;
color: var(--text-dim) !important;
border-radius: 10px 10px 0 0 !important;
border: 1px solid var(--card-border) !important;
padding: 10px 20px !important;
}

.stTabs [aria-selected="true"] {
background: var(--primary) !important;
color: white !important;
border-color: var(--primary) !important;
}

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg-dark); }
::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }
</style>''', unsafe_allow_html=True)

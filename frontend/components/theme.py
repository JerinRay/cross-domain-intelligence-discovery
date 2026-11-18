
import streamlit as st


def apply_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
        --bg: #080e19;
        --panel: #151e2d;
        --panel-soft: #1b2638;
        --gold: #e7b968;
        --gold-light: #ffe0a1;
        --text: #f4f5fa;
        --muted: #a6afc0;
        --line: rgba(191, 203, 225, 0.17);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text);
    }

    .stApp {
        background:
            radial-gradient(ellipse at 78% 5%, rgba(210,158,82,.14), transparent 35%),
            radial-gradient(ellipse at 5% 90%, rgba(35,65,105,.22), transparent 40%),
            linear-gradient(135deg, #080e19, #101a2a 55%, #080e19);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(8,14,25,.88);
    }

    [data-testid="stToolbar"] {
        background: transparent;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .block-container {
        padding-top: 1.7rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }

    /* Brand */
    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 4px 25px;
        border-bottom: 1px solid var(--line);
        margin-bottom: 25px;
        color: var(--text);
        font-size: 17px;
        font-weight: 800;
    }

    .brand-icon {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        background: linear-gradient(135deg, #ffe0a1, #b9853c);
        display: grid;
        place-items: center;
        color: #17130d;
        font-size: 25px;
        box-shadow: 0 0 22px rgba(231,185,104,.25);
    }

    .brand small {
        display: block;
        color: var(--gold);
        font-size: 9px;
        letter-spacing: 1.5px;
        margin-top: 4px;
    }

    .nav-label {
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1.6px;
        color: #a9aebe;
        margin: 10px 0 13px;
    }

    /* Navigation */
    [data-testid="stSidebar"] {
        background: #0b1422;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        color: #d6dbea;
        font-weight: 600;
    }

    /* System health */
    .status {
        background: rgba(30, 150, 103, .12);
        border: 1px solid rgba(65, 220, 150, .3);
        border-radius: 10px;
        padding: 11px;
        color: #8de9b9;
        font-size: 11px;
        font-weight: 800;
    }

    .status i {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #48e39a;
        margin-right: 8px;
        box-shadow: 0 0 10px #48e39a;
    }

    /* Top header */
    .topline {
        font-size: 9px;
        letter-spacing: 2px;
        color: #c1a575;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .topline span {
        float: right;
        color: #8994a8;
    }

    /* Hero */
    .hero {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 27px 30px;
        border: 1px solid rgba(231,185,104,.28);
        border-radius: 18px;
        background:
            linear-gradient(110deg, rgba(30,39,54,.97), rgba(14,23,37,.94));
        box-shadow: 0 12px 35px rgba(0,0,0,.24);
        margin-bottom: 25px;
    }

    .hero-title {
        font-family: 'Manrope', sans-serif;
        font-size: clamp(26px, 3vw, 39px);
        font-weight: 800;
        letter-spacing: -1.3px;
        color: #f7f7fb;
    }

    .hero-title em {
        color: var(--gold-light);
        font-style: normal;
    }

    .hero-sub {
        color: #b8c0ce;
        font-size: 13px;
        margin-top: 7px;
    }

    .hero-tag {
        border: 1px solid rgba(231,185,104,.4);
        background: rgba(231,185,104,.1);
        color: var(--gold-light);
        padding: 10px 15px;
        border-radius: 30px;
        font-size: 9px;
        font-weight: 800;
        letter-spacing: 1px;
    }

    /* Section headings */
    .section-title {
        font-family: 'Manrope', sans-serif;
        font-size: 19px;
        font-weight: 800;
        color: #f0f2f8;
        margin: 6px 0 5px;
    }

    /* KPI cards */
    .metric {
        min-height: 112px;
        padding: 18px;
        border: 1px solid var(--line);
        border-radius: 15px;
        background: linear-gradient(145deg, #202b40, #121c2c);
        box-shadow: 0 8px 25px rgba(0,0,0,.25);
        transition: .2s ease;
    }

    .metric:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0,0,0,.35);
    }

    .metric.purple {
        border-color: rgba(190,115,255,.55);
        box-shadow: 0 0 18px rgba(165,95,255,.10);
    }

    .metric.blue {
        border-color: rgba(91,151,255,.55);
        box-shadow: 0 0 18px rgba(91,151,255,.10);
    }

    .metric.green {
        border-color: rgba(72,220,143,.48);
        box-shadow: 0 0 18px rgba(72,220,143,.10);
    }

    .metric.gold {
        border-color: rgba(231,185,104,.58);
        box-shadow: 0 0 18px rgba(231,185,104,.12);
    }

    .metric-label {
        font-size: 9px;
        letter-spacing: 1.3px;
        font-weight: 800;
        color: #b7c0d0;
    }

    .metric-value {
        font-family: 'Manrope', sans-serif;
        font-size: 29px;
        font-weight: 800;
        color: #fff0d0;
        margin-top: 10px;
        line-height: 1.1;
    }

    .metric-caption {
        font-size: 10px;
        color: #a3adbf;
        margin-top: 7px;
    }

    /* Main dashboard panels */
    .panel {
        background: linear-gradient(145deg, rgba(31,43,62,.96), rgba(17,27,43,.98));
        border: 1px solid rgba(176,193,220,.20);
        border-radius: 17px;
        padding: 18px;
        box-shadow: 0 10px 28px rgba(0,0,0,.24);
        margin-bottom: 16px;
    }

    .panel-gold {
        border-color: rgba(231,185,104,.42);
        box-shadow: 0 0 20px rgba(231,185,104,.07);
    }

    .panel-title {
        font-family: 'Manrope', sans-serif;
        font-size: 17px;
        font-weight: 800;
        color: #f4f5fa;
        margin-bottom: 12px;
    }

    .divider {
        height: 1px;
        background: var(--line);
        margin: 24px 0;
    }

    /* Charts and tables */
    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(176,193,220,.18);
        border-radius: 13px;
        overflow: hidden;
        background: #141e2e;
    }

    /* Buttons */
    .stDownloadButton button,
    .stButton button {
        background: linear-gradient(135deg, #f2cf91, #b98743);
        color: #17130d;
        border: 1px solid rgba(255,224,161,.55);
        border-radius: 9px;
        font-weight: 800;
    }

    .stDownloadButton button:hover,
    .stButton button:hover {
        background: #ffe0a1;
        color: #17130d;
        border-color: #ffe0a1;
    }

    /* Tabs */
    [data-testid="stTabs"] button {
        color: #bdc6d6;
        font-weight: 600;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--gold-light);
    }

    /* Inputs */
    input, textarea {
        background: #111d2e !important;
        color: #f4f5fa !important;
        border-color: rgba(176,193,220,.25) !important;
    }

    </style>
    """, unsafe_allow_html=True)

from pathlib import Path
from datetime import datetime
import json
import math
import re
import sqlite3
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =========================================================
# CROSS-DOMAIN INTELLIGENCE — DAY 13 FRONTEND (Aurora Gold)
# =========================================================

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Imported after ROOT is on sys.path so `components` resolves from the project root.
try:
    from components.theme import apply_theme
except ImportError:  # keep the page usable even if the shared theme module is missing
    def apply_theme():
        return None

st.set_page_config(
    page_title="Cross-Domain Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()

LOG = ROOT / "logs"
PROCESSED = ROOT / "datasets" / "processed"
PIPELINE_PATH = LOG / "pipeline" / "pipeline_execution_report.json"
ANOMALY_CSV = LOG / "pipeline" / "olist_anomaly_investigation.csv"

FILES = {
    "Customers": "olist_customers_dataset.parquet",
    "Geolocation": "olist_geolocation_dataset.parquet",
    "Order Items": "olist_order_items_dataset.parquet",
    "Payments": "olist_order_payments_dataset.parquet",
    "Reviews": "olist_order_reviews_dataset.parquet",
    "Orders": "olist_orders_dataset.parquet",
    "Products": "olist_products_dataset.parquet",
    "Sellers": "olist_sellers_dataset.parquet",
}

NAV_ITEMS = {
    "Dashboard": "⌂",
    "Data Management": "☷",
    "Discovery Engine": "⌕",
    "Knowledge Graph": "✣",
    "Intelligence": "◬",
    "Reports": "▤",
}

# Palette shared by CSS and Plotly
GOLD = "#e9b765"
GOLD_DEEP = "#b8873a"
PURPLE = "#9d6bff"
BLUE = "#4f86ff"
TEAL = "#22c3d6"
GREEN = "#3fd68a"
RED = "#ff5d6c"
TEXT = "#f3efe6"
MUTED = "#9a9fae"

# ------------------------- CSS ----------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700;800&display=swap');
:root{
  --bg:#06070b;--panel:rgba(16,17,24,.86);--line:rgba(233,183,101,.16);--line2:rgba(255,255,255,.07);
  --gold:#e9b765;--gold2:#b8873a;--text:#f3efe6;--muted:#9a9fae;--green:#3fd68a;--red:#ff5d6c;
}
html,body,[class*="css"]{font-family:'Exo 2',system-ui,-apple-system,'Segoe UI',sans-serif!important;color:var(--text)}
.stApp{
  background:
    radial-gradient(ellipse at 18% 100%,rgba(233,183,101,.13),transparent 40%),
    radial-gradient(ellipse at 55% 0%,rgba(233,183,101,.08),transparent 38%),
    radial-gradient(ellipse at 100% 60%,rgba(120,90,200,.06),transparent 35%),
    linear-gradient(135deg,#050609 0%,#0b0c12 55%,#050609 100%);
  color:var(--text)}
header[data-testid="stHeader"]{background:transparent;height:0;min-height:0}
[data-testid="stToolbar"],#MainMenu,footer{visibility:hidden}
.block-container{max-width:100%;padding:1.1rem 1.3rem 2.2rem;position:relative;z-index:1}
section[data-testid="stSidebar"]{display:none}
div[data-testid="stVerticalBlock"]{gap:.75rem}
.aurora-waves{position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.9}
.aurora-waves svg{width:100%;height:100%}

/* ---------- icon rail ---------- */
.rail{background:linear-gradient(180deg,rgba(20,20,27,.92),rgba(9,10,14,.95));border:1px solid var(--line2);
  border-radius:24px;padding:16px 8px;min-height:880px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.45)}
.rail-logo{font:800 26px 'Exo 2',system-ui,sans-serif;color:var(--gold);padding:8px 0 26px;text-shadow:0 0 22px rgba(233,183,101,.55)}
.rail-ico{font-size:21px;color:#a9adb9;width:48px;height:48px;line-height:48px;margin:10px auto;border-radius:14px}
.rail-ico.active{color:#fff;background:linear-gradient(140deg,rgba(233,183,101,.35),rgba(184,135,58,.18));
  border:1px solid rgba(233,183,101,.55);box-shadow:0 0 22px rgba(233,183,101,.25)}

/* ---------- navigation panel ---------- */
.brand{display:flex;align-items:center;gap:13px;padding:6px 2px 22px;border-bottom:1px solid var(--line2);margin-bottom:18px}
.brand-icon{min-width:46px;height:46px;display:grid;place-items:center;font-size:30px;color:var(--gold);
  text-shadow:0 0 18px rgba(233,183,101,.6)}
.brand-name{font:700 19px/1.15 'Exo 2',system-ui,sans-serif;color:#fff}
.brand-sub{font-size:11px;color:#c9c2b2;margin-top:5px}
.nav-heading{font:600 17px 'Exo 2',system-ui,sans-serif;color:#fff;margin:6px 0 12px 6px}
div[data-testid="stButton"]{margin:0 0 -4px}
div[data-testid="stButton"] button{width:100%;justify-content:flex-start;text-align:left;border:1px solid transparent;
  background:transparent;color:#e6e2d8;border-radius:12px;padding:10px 14px;font-size:14px;font-weight:500;min-height:44px;transition:.2s}
div[data-testid="stButton"] button>div,div[data-testid="stButton"] button span,
div[data-testid="stButton"] button [data-testid="stMarkdownContainer"]{justify-content:flex-start!important;text-align:left!important;width:100%}
div[data-testid="stButton"] button p{text-align:left!important;width:100%;font-size:14px}
div[data-testid="stButton"] button:hover{background:rgba(233,183,101,.08);border-color:rgba(233,183,101,.30);color:#fff}
div[data-testid="stButton"] button[kind="primary"]{background:linear-gradient(100deg,#d9a352,#a87a35);
  border-color:rgba(255,215,150,.6);color:#fff;box-shadow:0 6px 24px rgba(233,183,101,.25)}
div[data-testid="stButton"] button[kind="primary"]:hover{color:#fff}
.health-card{background:rgba(255,255,255,.03);border:1px solid var(--line2);border-radius:18px;padding:16px 14px;margin-top:30px}
.health-top{display:flex;justify-content:space-between;align-items:center}
.health-title{color:#fff;font-size:14px;font-weight:600}
.health-title .dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--green);
  box-shadow:0 0 10px var(--green);margin-right:8px}
.health-pulse{color:var(--green);font-size:20px}
.health-sub{font-size:11px;color:#b6b2a8;margin:4px 0 0 17px}
.health-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-top:16px;text-align:center;
  border-top:1px solid var(--line2);padding-top:14px}
.health-check{background:rgba(63,214,138,.14);color:var(--green);border:1px solid rgba(63,214,138,.45);border-radius:50%;
  width:26px;height:26px;display:grid;place-items:center;margin:auto auto 6px;font-size:13px}
.health-check.warn{background:rgba(233,183,101,.14);color:var(--gold);border-color:rgba(233,183,101,.45)}
.health-label{font-size:11px;color:#ddd8cc}
.version{margin:26px 0 0 14px;color:#b4ad9e;font-size:13px}

/* ---------- top bar ---------- */
.topbar{display:flex;justify-content:flex-end;align-items:center;gap:22px}
.search{display:flex;align-items:center;gap:12px;flex:0 1 470px;border:1px solid rgba(255,255,255,.14);border-radius:999px;
  background:rgba(14,15,21,.8);padding:10px 16px;color:#b9b6ad;font-size:13px}
.search kbd{margin-left:auto;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);border-radius:7px;
  padding:2px 7px;font:600 11px 'Exo 2',system-ui,sans-serif;color:#ddd}
.bell{position:relative;font-size:20px;color:#d8d4ca}
.bell:after{content:'';position:absolute;top:0;right:-2px;width:7px;height:7px;border-radius:50%;background:var(--gold)}
.profile{display:flex;align-items:center;gap:10px}
.avatar{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;font:700 14px 'Exo 2',system-ui,sans-serif;color:#2a1d08;
  background:linear-gradient(140deg,#f4cf8c,#c08c3e)}
.p-name{font-weight:600;font-size:14px;color:#fff;line-height:1.2}.p-role{font-size:11px;color:#a7a399}
.hero-title{font:700 clamp(34px,3.3vw,48px)/1.1 'Exo 2',system-ui,sans-serif;letter-spacing:-.5px;color:#f5f3ee;margin-top:6px}
.hero-title em{font-style:normal;background:linear-gradient(90deg,#f3cd85,#d59b46);-webkit-background-clip:text;
  background-clip:text;color:transparent}
.hero-sub{font-size:15px;color:#cfcabd;margin:6px 0 16px}
.hero-sub b{color:var(--gold);font-weight:400;margin:0 8px}

/* ---------- KPI cards ---------- */
.kpi{margin-bottom:6px;display:flex;align-items:center;gap:16px;border-radius:16px;padding:18px 18px;min-height:96px;position:relative;overflow:hidden;
  border:1px solid;box-shadow:0 14px 34px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.05)}
.kpi-ico{min-width:52px;height:52px;border-radius:14px;display:grid;place-items:center;font-size:24px}
.kpi-body{flex:1;min-width:0}
.kpi-label{color:#e7e3da;font-size:14px;font-weight:500}
.kpi-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:4px}
.kpi-value{font:600 30px/1.1 'Exo 2',system-ui,sans-serif;color:#fff;white-space:nowrap}
.kpi-chip{font-size:11px;font-weight:600;padding:4px 8px;border-radius:8px;white-space:nowrap;
  background:rgba(63,214,138,.12);color:var(--green);border:1px solid rgba(63,214,138,.25)}
.kpi.purple{border-color:rgba(157,107,255,.55);background:linear-gradient(120deg,rgba(80,48,150,.45),rgba(16,14,26,.92) 65%)}
.kpi.purple .kpi-ico{color:#c4a6ff;background:rgba(157,107,255,.16)}
.kpi.blue{border-color:rgba(79,134,255,.55);background:linear-gradient(120deg,rgba(36,64,140,.45),rgba(12,15,28,.92) 65%)}
.kpi.blue .kpi-ico{color:#9dbcff;background:rgba(79,134,255,.16)}
.kpi.green{border-color:rgba(63,214,138,.55);background:linear-gradient(120deg,rgba(24,110,70,.45),rgba(10,20,16,.92) 65%)}
.kpi.green .kpi-ico{color:#7ff0b4;background:rgba(63,214,138,.14)}
.kpi.gold{border-color:rgba(233,183,101,.6);background:linear-gradient(120deg,rgba(130,92,32,.45),rgba(22,17,10,.92) 65%)}
.kpi.gold .kpi-ico{color:#f5cd86;background:rgba(233,183,101,.16)}

/* ---------- panels ---------- */
div[data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(160deg,rgba(20,21,29,.92),rgba(10,11,16,.94))!important;
  border:1px solid rgba(255,255,255,.08)!important;border-radius:20px!important;padding:16px 18px!important;
  box-shadow:0 18px 46px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.05)!important}
div[data-testid="stVerticalBlockBorderWrapper"]>div{background:transparent!important}
.ph{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.ph-title{font:600 19px 'Exo 2',system-ui,sans-serif;color:#fff;display:flex;align-items:center;gap:10px}
.ph-ico{color:var(--gold);font-size:18px}
.ph-link{color:var(--gold);font-size:12px;font-weight:500}
.ph-sub{font-size:11px;color:var(--muted);margin:-4px 0 10px}
.chip-ok{font-size:12px;color:var(--green);border:1px solid rgba(63,214,138,.45);background:rgba(63,214,138,.08);
  padding:3px 10px;border-radius:8px}
.chip-warn{font-size:12px;color:var(--gold);border:1px solid rgba(233,183,101,.45);background:rgba(233,183,101,.08);
  padding:3px 10px;border-radius:8px}

/* tabs as pills (works for old baseweb and new react-aria tab DOM) */
[data-testid="stTabs"] [role="tablist"]{gap:4px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
  border-radius:12px;padding:4px;width:fit-content;border-bottom:1px solid rgba(255,255,255,.08)!important}
[data-testid="stTabs"] [role="tab"]{height:32px;padding:0 16px!important;border-radius:9px;background:transparent;
  display:flex;align-items:center;border:none!important;margin:0!important}
[data-testid="stTabs"] [role="tab"] p{font-size:13px;color:#d6d2c8!important;margin:0}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:linear-gradient(135deg,#e7b866,#b98538)}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p{color:#1d1406!important;font-weight:600}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"],.react-aria-SelectionIndicator{display:none!important}

/* knowledge-graph stats column */
.kg-stats{border-left:1px solid var(--line2);padding-left:14px;margin-top:6px}
.kg-stat{display:flex;align-items:center;gap:12px;padding:9px 0}
.kg-ico{min-width:40px;height:40px;border-radius:11px;display:grid;place-items:center;font-size:18px;
  background:rgba(157,107,255,.13);color:#c7a9ff;border:1px solid rgba(157,107,255,.25)}
.kg-ico.gold{background:rgba(233,183,101,.12);color:var(--gold);border-color:rgba(233,183,101,.3)}
.kg-ico.blue{background:rgba(79,134,255,.13);color:#9dbcff;border-color:rgba(79,134,255,.3)}
.kg-lbl{font-size:12px;color:#c9c5bb}.kg-val{font:600 20px 'Exo 2',system-ui,sans-serif;color:#fff}

/* donut legend */
.legend{padding-top:22px}
.lg{display:flex;align-items:center;gap:10px;font-size:13px;color:#e4e0d6;padding:5px 0}
.lg i{width:11px;height:11px;border-radius:50%;display:inline-block}

/* list rows */
.row{display:flex;align-items:center;gap:13px;padding:10px 0;border-bottom:1px solid var(--line2)}
.row:last-child{border-bottom:none}
.row-ico{min-width:34px;height:34px;border-radius:10px;display:grid;place-items:center;color:var(--gold);
  background:rgba(233,183,101,.10);border:1px solid rgba(233,183,101,.25);font-size:15px}
.row-main{flex:1;font-size:13px;color:#f0ece3}
.row-main small{display:block;color:#9a9fae;font-size:11px;margin-top:3px}
.row-arrow{color:#cfcabd;font-size:18px}
.insight{padding:12px 0;border-bottom:1px solid var(--line2);display:flex;align-items:center}
.insight:last-child{border-bottom:none}
.insight div{flex:1;font-size:13px;color:#ece8de}
.insight b{display:block;color:var(--gold);font:600 17px 'Exo 2',system-ui,sans-serif;margin-top:4px}

/* pipeline flow */
.flow{display:flex;align-items:flex-start;justify-content:space-between;gap:4px;padding:10px 0 14px}
.step{text-align:center;flex:1 1 0;min-width:0}
.step-ico{position:relative;width:46px;height:46px;border-radius:50%;margin:0 auto 8px;display:grid;place-items:center;
  font-size:21px;color:#f1ede4;background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.14),rgba(255,255,255,.03));
  border:1px solid rgba(255,255,255,.18)}
.step-badge{position:absolute;right:-4px;bottom:-3px;width:19px;height:19px;border-radius:50%;display:grid;place-items:center;
  font-size:11px;color:#06120b;background:var(--green);border:2px solid #101118}
.step-badge.warn{background:var(--gold)}
.step-name{font-size:11px;overflow-wrap:normal;color:#e6e2d8;line-height:1.25}
.arrow{color:#8f8b82;font-size:14px;margin-top:16px;flex:0 0 auto}
.flow-foot{display:flex;gap:10px;border-top:1px solid var(--line2);padding-top:12px}
.ff{flex:1;display:flex;gap:10px;align-items:center;font-size:12px;color:#d9d5cb}
.ff span{color:var(--gold);font-size:18px}
.ff small{display:block;color:#a7a399;font-size:11px}

/* anomaly side stats */
.an-side{border-left:1px solid var(--line2);padding-left:14px;margin-top:8px}
.an-lbl{font-size:12px;color:#c9c5bb}
.an-val{font:700 30px 'Exo 2',system-ui,sans-serif;color:var(--red);margin:2px 0 14px}
.an-chip{display:inline-block;font-size:12px;font-weight:600;color:var(--red);background:rgba(255,93,108,.12);
  border:1px solid rgba(255,93,108,.35);border-radius:7px;padding:3px 8px;margin-top:4px}

/* page sections */
.page-title{font:600 24px 'Exo 2',system-ui,sans-serif;color:#fff;margin:4px 0 2px}
.page-sub{font-size:12px;color:var(--muted);margin-bottom:10px}
div[data-testid="stPlotlyChart"]{background:transparent}
div[data-testid="stDataFrame"]{border:1px solid var(--line2);border-radius:12px;overflow:hidden}
.stDownloadButton button{border:1px solid rgba(233,183,101,.45);border-radius:11px;background:rgba(233,183,101,.08);
  color:#f3d39b;font-weight:600}
/* =================== GLASS THEME (overrides) =================== */
html,body,[class*="css"],.stApp,button,input,p,span,div{font-family:'Exo 2',system-ui,sans-serif}
.stApp{background:
  radial-gradient(ellipse at 15% 105%,rgba(233,183,101,.16),transparent 38%),
  radial-gradient(ellipse at 70% -5%,rgba(233,183,101,.10),transparent 40%),
  radial-gradient(ellipse at 45% 45%,rgba(90,70,200,.08),transparent 45%),
  #040509!important}
.orb{position:fixed;border-radius:50%;filter:blur(90px);pointer-events:none;z-index:0}
.orb-gold{width:520px;height:420px;left:-140px;bottom:-160px;background:rgba(233,170,80,.22)}
.orb-violet{width:620px;height:520px;left:38%;top:22%;background:rgba(110,70,230,.12)}
.orb-blue{width:460px;height:420px;right:-120px;top:30%;background:rgba(40,120,230,.10)}

/* frosted panels */
div[data-testid="stVerticalBlockBorderWrapper"],.rail{
  background:linear-gradient(150deg,rgba(255,255,255,.085) 0%,rgba(255,255,255,.03) 38%,rgba(255,255,255,.015) 100%)!important;
  backdrop-filter:blur(28px) saturate(160%);-webkit-backdrop-filter:blur(28px) saturate(160%);
  border:1px solid rgba(255,255,255,.13)!important;border-radius:22px!important;overflow:hidden;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.16),inset 0 -1px 0 rgba(255,255,255,.03),
             0 24px 60px rgba(0,0,0,.55)!important}
.rail{border-radius:26px}
.rail-ico.active{background:linear-gradient(145deg,rgba(255,214,150,.35),rgba(184,135,58,.22));
  border:1px solid rgba(255,214,150,.55);box-shadow:0 0 26px rgba(233,183,101,.35),inset 0 1px 0 rgba(255,255,255,.25)}
.health-card{background:linear-gradient(150deg,rgba(255,255,255,.07),rgba(255,255,255,.02))!important;
  backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.12)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12)}
div[data-testid="stButton"] button[kind="primary"]{
  background:linear-gradient(100deg,rgba(236,180,95,.95),rgba(160,115,45,.75))!important;
  border:1px solid rgba(255,220,160,.65)!important;
  box-shadow:0 8px 28px rgba(233,183,101,.30),inset 0 1px 0 rgba(255,255,255,.35)!important}

/* glossy KPI cards with coloured glass tint */
.kpi{backdrop-filter:blur(24px) saturate(160%);-webkit-backdrop-filter:blur(24px) saturate(160%)}
.kpi:before{content:'';position:absolute;inset:0;border-radius:inherit;pointer-events:none;
  background:linear-gradient(180deg,rgba(255,255,255,.12),rgba(255,255,255,0) 48%)}
.kpi.purple{background:linear-gradient(115deg,rgba(140,85,255,.38),rgba(255,255,255,.03) 72%);
  border-color:rgba(175,135,255,.75);box-shadow:0 0 34px rgba(140,85,255,.28),inset 0 1px 0 rgba(255,255,255,.2)}
.kpi.blue{background:linear-gradient(115deg,rgba(60,120,255,.38),rgba(255,255,255,.03) 72%);
  border-color:rgba(110,160,255,.75);box-shadow:0 0 34px rgba(60,120,255,.26),inset 0 1px 0 rgba(255,255,255,.2)}
.kpi.green{background:linear-gradient(115deg,rgba(50,200,120,.34),rgba(255,255,255,.03) 72%);
  border-color:rgba(90,230,150,.75);box-shadow:0 0 34px rgba(50,200,120,.24),inset 0 1px 0 rgba(255,255,255,.2)}
.kpi.gold{background:linear-gradient(115deg,rgba(225,165,70,.38),rgba(255,255,255,.03) 72%);
  border-color:rgba(245,195,120,.8);box-shadow:0 0 34px rgba(225,165,70,.26),inset 0 1px 0 rgba(255,255,255,.2)}
.kpi-ico{background:rgba(255,255,255,.08)!important;border:1px solid rgba(255,255,255,.12);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.15)}
.kpi-value{font-weight:600;font-size:clamp(22px,1.75vw,30px)}
.search{background:rgba(255,255,255,.05);backdrop-filter:blur(18px);border-color:rgba(255,255,255,.18)}
.step-ico,.row-ico,.kg-ico{backdrop-filter:blur(10px);box-shadow:inset 0 1px 0 rgba(255,255,255,.14)}
.hero-title{font-weight:700;letter-spacing:0}
.hero-title em{background-image:linear-gradient(90deg,#f6d394,#e2a957 60%,#c98f3d);-webkit-background-clip:text;background-clip:text;color:transparent}

/* pill selector (Graph / Communities / Domains) in the panel header */
div[data-testid="stRadio"]{display:flex;justify-content:flex-end}
div[data-testid="stRadio"] [role="radiogroup"]{gap:2px;flex-wrap:nowrap;width:fit-content;padding:4px;border-radius:12px;
  background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);backdrop-filter:blur(14px)}
div[data-testid="stRadio"] label{margin:0!important;padding:5px 16px;border-radius:9px;cursor:pointer;transition:.2s}
div[data-testid="stRadio"] [role="radiogroup"] label div:not([data-testid="stMarkdownContainer"]):not(:has([data-testid="stMarkdownContainer"])){display:none!important}
div[data-testid="stRadio"] [role="radiogroup"] label>div{display:flex!important;margin:0!important;padding:0!important}
div[data-testid="stRadio"] label p{font-size:13px;color:#dcd7cc;margin:0;white-space:nowrap}
div[data-testid="stRadio"] label:has(input:checked){background:linear-gradient(135deg,#efc070,#b98538);
  box-shadow:0 4px 14px rgba(233,183,101,.3),inset 0 1px 0 rgba(255,255,255,.35)}
div[data-testid="stRadio"] label:has(input:checked) p{color:#1d1406;font-weight:600}

/* =================== GLASS v2 + LARGER TYPE =================== */
/* frosted glass panels — old Streamlit wrapper + new keyed containers */
div[data-testid="stVerticalBlockBorderWrapper"],[class*="st-key-glass"]{
  position:relative;overflow:hidden;
  background:linear-gradient(155deg,rgba(255,255,255,.12) 0%,rgba(255,255,255,.05) 32%,rgba(255,255,255,.02) 70%,rgba(255,255,255,.045) 100%)!important;
  backdrop-filter:blur(34px) saturate(185%) brightness(1.08);-webkit-backdrop-filter:blur(34px) saturate(185%) brightness(1.08);
  border:1px solid rgba(255,255,255,.17)!important;border-radius:24px!important;padding:20px 22px!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.28),inset 1px 0 0 rgba(255,255,255,.07),
             inset 0 -24px 48px rgba(0,0,0,.20),0 30px 70px rgba(0,0,0,.55)!important}
div[data-testid="stVerticalBlockBorderWrapper"]::before,[class*="st-key-glass"]::before{
  content:'';position:absolute;inset:0;border-radius:inherit;pointer-events:none;z-index:0;
  background:linear-gradient(118deg,rgba(255,255,255,.13) 0%,rgba(255,255,255,.02) 26%,rgba(255,255,255,0) 60%,rgba(255,255,255,.05) 100%)}
div[data-testid="stVerticalBlockBorderWrapper"]::after,[class*="st-key-glass"]::after{
  content:'';position:absolute;top:0;left:8%;right:8%;height:1px;pointer-events:none;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.55),transparent)}
[class*="st-key-glass"]>*{position:relative;z-index:1}
.rail{background:linear-gradient(170deg,rgba(255,255,255,.11),rgba(255,255,255,.03) 45%,rgba(255,255,255,.02))!important;
  backdrop-filter:blur(34px) saturate(185%);border:1px solid rgba(255,255,255,.17)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.28),0 30px 70px rgba(0,0,0,.55)!important}
.kpi{backdrop-filter:blur(30px) saturate(190%);-webkit-backdrop-filter:blur(30px) saturate(190%)}
.kpi:before{background:linear-gradient(180deg,rgba(255,255,255,.18),rgba(255,255,255,.02) 50%,rgba(255,255,255,0))}
.kpi:after{content:'';position:absolute;top:0;left:10%;right:10%;height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.7),transparent)}
.kpi-ico,.row-ico,.kg-ico,.step-ico,.health-check{background:rgba(255,255,255,.09)!important;
  border:1px solid rgba(255,255,255,.18)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.25)}
.health-card{background:linear-gradient(155deg,rgba(255,255,255,.10),rgba(255,255,255,.025))!important;
  backdrop-filter:blur(26px) saturate(180%);box-shadow:inset 0 1px 0 rgba(255,255,255,.22)}
div[data-testid="stButton"] button[kind="secondary"]:hover{background:rgba(255,255,255,.07);
  border-color:rgba(255,255,255,.18);backdrop-filter:blur(12px)}

/* larger typography */
html,body{font-size:17px}
.hero-title{font-size:clamp(40px,3.8vw,58px)!important}
.hero-sub{font-size:18px!important}
.brand-name{font-size:21px!important}.brand-sub{font-size:13px!important}
.nav-heading{font-size:19px!important}
div[data-testid="stButton"] button{min-height:50px!important}
div[data-testid="stButton"] button p{font-size:16px!important}
.search{font-size:15px!important;padding:12px 18px!important}
.p-name{font-size:16px!important}.p-role{font-size:13px!important}
.kpi{min-height:112px;margin-bottom:12px!important}
.kpi-label{font-size:16px!important}
.kpi-value{font-size:clamp(26px,2vw,36px)!important}
.kpi-chip{font-size:12.5px!important}
.kpi-ico{min-width:58px!important;height:58px!important;font-size:27px!important}
.ph-title{font-size:22px!important}.ph-ico{font-size:20px!important}
.ph-link{font-size:14px!important}.ph-sub{font-size:13px!important}
.chip-ok,.chip-warn{font-size:13.5px!important}
.kg-lbl{font-size:14px!important}.kg-val{font-size:24px!important}
.kg-ico{min-width:46px!important;height:46px!important;font-size:20px!important}
.lg{font-size:15px!important}
.row-main{font-size:15px!important}.row-main small{font-size:12.5px!important}
.row-ico{min-width:38px!important;height:38px!important}
.insight div{font-size:15px!important}.insight b{font-size:20px!important}
.step-name{font-size:12px!important;line-height:1.3;overflow-wrap:normal;word-break:normal;hyphens:none}
.step{min-width:0!important}
.flow{gap:0!important}
.step-ico{width:48px!important;height:48px!important}
.arrow{font-size:12px!important;margin:16px -2px 0!important}
.step-ico{width:52px!important;height:52px!important;font-size:22px!important}
.ff{font-size:14px!important}.ff small{font-size:12.5px!important}
.an-lbl{font-size:14px!important}.an-val{font-size:36px!important}.an-chip{font-size:14px!important}
.health-title{font-size:16px!important}.health-sub{font-size:13px!important}.health-label{font-size:12.5px!important}
.version{font-size:14px!important}
.page-title{font-size:30px!important}.page-sub{font-size:15px!important}
div[data-testid="stRadio"] label p{font-size:15px!important}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{font-size:13.5px!important}
[data-testid="stMarkdownContainer"] p{font-size:16px}

/* =================== TYPE SCALE v3 (larger) =================== */
html,body{font-size:19px}
[data-testid="stMarkdownContainer"] p{font-size:18px}
.hero-title{font-size:clamp(46px,4.3vw,66px)!important}
.hero-sub{font-size:20px!important}
.brand-name{font-size:23px!important}.brand-sub{font-size:14.5px!important}
.nav-heading{font-size:21px!important}
div[data-testid="stButton"] button{min-height:54px!important}
div[data-testid="stButton"] button p{font-size:18px!important}
.search{font-size:16.5px!important}
.p-name{font-size:18px!important}.p-role{font-size:14.5px!important}
.kpi-label{font-size:18px!important}
.kpi-value{font-size:clamp(30px,2.3vw,42px)!important}
.kpi-chip{font-size:14px!important}
.ph-title{font-size:25px!important}.ph-ico{font-size:22px!important}
.ph-link{font-size:15.5px!important}.ph-sub{font-size:14.5px!important}
.chip-ok,.chip-warn{font-size:15px!important}
.kg-lbl{font-size:15.5px!important}.kg-val{font-size:27px!important}
.lg{font-size:17px!important}
.row-main{font-size:17px!important}.row-main small{font-size:14px!important}
.insight div{font-size:17px!important}.insight b{font-size:23px!important}
.step-name{font-size:14px!important}
.ff{font-size:15.5px!important}.ff small{font-size:14px!important}
.an-lbl{font-size:15.5px!important;white-space:nowrap}.an-val{font-size:42px!important}.an-chip{font-size:15.5px!important}
.health-title{font-size:18px!important}.health-sub{font-size:14.5px!important}.health-label{font-size:14px!important}
.version{font-size:15.5px!important}
.page-title{font-size:34px!important}.page-sub{font-size:17px!important}
div[data-testid="stRadio"] label p{font-size:16.5px!important}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{font-size:15px!important}

/* =================== DATA EXPLORER TEXT VISIBILITY FIX =================== */

/* Widget labels */
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] *,
.stApp [data-testid="stWidgetLabel"] p,
.stApp div[data-testid="stTextInput"] label,
.stApp div[data-testid="stSelectbox"] label,
.stApp div[data-testid="stMultiSelect"] label,
.stApp div[data-testid="stNumberInput"] label {
    color: #e8dfcf !important;
    opacity: 1 !important;
}

/* KPI labels and values */
.stApp [data-testid="stMetricLabel"],
.stApp [data-testid="stMetricLabel"] *,
.stApp [data-testid="stMetricValue"],
.stApp [data-testid="stMetricValue"] *,
.stApp [data-testid="stMetricDelta"] {
    color: #f3efe6 !important;
    opacity: 1 !important;
}

/* Input text */
.stApp input,
.stApp textarea {
    color: #ffffff !important;
}

/* Placeholder text */
.stApp input::placeholder,
.stApp textarea::placeholder {
    color: #a9a9b5 !important;
    opacity: 1 !important;
}

/* Selectbox and multiselect */
.stApp [data-baseweb="select"] *,
.stApp [data-baseweb="select"] input {
    color: #f3efe6 !important;
}

/* Captions */
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] p {
    color: #c9c4b9 !important;
}

/* Divider */
.stApp hr {
    border-color: rgba(255,255,255,0.18) !important;
}

</style>
""", unsafe_allow_html=True)


def wave_background():
    """Glowing golden silk waves (top sweep + bottom-left) and soft colour orbs behind the glass."""
    top, bottom = [], []
    for i in range(22):
        o = i * 6
        top.append(
            f'<path d="M380 {70 + o} C 700 {-40 + o * .6}, 980 {200 + o * .4}, 1250 {90 + o * .8} '
            f'S 1520 {-10 + o * .5}, 1680 {40 + o}" stroke="url(#gt)" '
            f'stroke-opacity="{0.10 + 0.035 * (22 - i) / 22 * 10 / 10:.3f}" stroke-width="{1.4 if i % 5 == 0 else .8}" fill="none"/>'
        )
    for i in range(24):
        o = i * 7
        bottom.append(
            f'<path d="M-60 {640 + o} C 160 {540 + o}, 330 {820 + o * .3}, 560 {800 + o * .5} '
            f'S 900 {930 + o * .2}, 1120 {960}" stroke="url(#gb)" '
            f'stroke-opacity="{0.12 + 0.03 * (24 - i) / 24 * 10 / 10:.3f}" stroke-width="{1.4 if i % 6 == 0 else .8}" fill="none"/>'
        )
    svg = (
        '<div class="orb orb-gold"></div><div class="orb orb-violet"></div><div class="orb orb-blue"></div>'
        '<div class="aurora-waves"><svg viewBox="0 0 1600 900" preserveAspectRatio="none" '
        'xmlns="http://www.w3.org/2000/svg"><defs>'
        '<linearGradient id="gt" x1="0" x2="1"><stop offset="0" stop-color="#e9b765" stop-opacity="0"/>'
        '<stop offset=".45" stop-color="#ffd38a"/><stop offset=".8" stop-color="#e9b765"/>'
        '<stop offset="1" stop-color="#e9b765" stop-opacity=".2"/></linearGradient>'
        '<linearGradient id="gb" x1="0" x2="1"><stop offset="0" stop-color="#ffd38a"/>'
        '<stop offset=".55" stop-color="#e9b765" stop-opacity=".7"/>'
        '<stop offset="1" stop-color="#e9b765" stop-opacity="0"/></linearGradient>'
        '<filter id="glow" x="-10%" y="-10%" width="120%" height="120%">'
        '<feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
        '<g filter="url(#glow)">' + "".join(top) + "".join(bottom) + "</g></svg></div>"
    )
    st.markdown(svg, unsafe_allow_html=True)


wave_background()

# ---------------------- HELPERS ---------------------------


def html(markup):
    """Render HTML without Markdown turning indented lines into code blocks."""
    st.markdown(markup, unsafe_allow_html=True)


def glass_panel(name):
    """Bordered container that gets the frosted-glass style.

    Newer Streamlit renders bordered containers without the old wrapper test-id,
    so a `glass_*` key adds a CSS class (st-key-glass_*) to target.  Older
    versions without the `key` argument fall back to the plain container.
    """
    try:
        return st.container(border=True, key=f"glass_{name}")
    except TypeError:
        return st.container(border=True)


def read_json(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}


def locate(filename):
    for path in (PROCESSED / filename, PROCESSED / "olist" / filename):
        if path.exists():
            return path
    return None


@st.cache_data(show_spinner=False)
def load_inventory():
    rows = []
    for name, filename in FILES.items():
        path = locate(filename)
        if path:
            try:
                frame = pd.read_parquet(path)
                rows.append({
                    "Dataset": name, "Rows": len(frame), "Columns": len(frame.columns),
                    "Size (MB)": round(path.stat().st_size / 1048576, 2), "Path": str(path),
                })
            except Exception:
                continue
    return pd.DataFrame(rows)


def kpi(icon, label, value, chip, tone):
    chip_html = f'<div class="kpi-chip">{chip}</div>' if chip else ""
    html(
        f'<div class="kpi {tone}"><div class="kpi-ico">{icon}</div><div class="kpi-body">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-row"><div class="kpi-value">{value}</div>{chip_html}</div>'
        f'</div></div>'
    )


def panel_header(icon, title, right="", subtitle=""):
    html(
        f'<div class="ph"><div class="ph-title"><span class="ph-ico">{icon}</span>{title}</div>'
        f'<div>{right}</div></div>' + (f'<div class="ph-sub">{subtitle}</div>' if subtitle else "")
    )


def page_header(title, subtitle):
    html(f'<div class="page-title">{title}</div><div class="page-sub">{subtitle}</div>')


def latest_discovery_file():
    folder = LOG / "cross_domain"
    files = sorted(folder.glob("cross_domain_report_*.json")) if folder.exists() else []
    return files[-1] if files else None


def time_ago(path):
    if not path or not Path(path).exists():
        return "—"
    seconds = (datetime.now() - datetime.fromtimestamp(Path(path).stat().st_mtime)).total_seconds()
    if seconds < 3600:
        return f"{max(int(seconds // 60), 1)} min ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    return f"{int(seconds // 86400)} days ago"


def format_duration(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"
    minutes, secs = divmod(int(round(value)), 60)
    return f"{minutes} min {secs} sec" if minutes else f"{secs} sec"


def first_key(source, *keys):
    for key in keys:
        if isinstance(source, dict) and source.get(key) not in (None, ""):
            return source[key]
    return None


def prepare_fts_query(value):
    """Build a safe FTS5 prefix query from ordinary user-entered text."""
    tokens = re.findall(r"[A-Za-z0-9_]+", str(value or "").lower())
    if not tokens:
        return ""
    return " AND ".join(f'"{token}"*' for token in tokens[:12])


def search_graph_index(query, table, limit=25):
    """Search the local SQLite FTS5 graph index without loading the full graph."""
    fts_query = prepare_fts_query(query)
    if not fts_query:
        return []

    database_path = LOG / "knowledge_graph_search.sqlite"
    if not database_path.exists():
        return []

    allowed_tables = {
        "entities_fts": "entity_id, entity_type, searchable",
        "relationships_fts": "source_id, target_id, relationship_type, searchable",
    }
    if table not in allowed_tables:
        return []

    columns = allowed_tables[table]
    try:
        connection = sqlite3.connect(
            f"file:{database_path.resolve()}?mode=ro", uri=True, timeout=5
        )
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                f"SELECT {columns} FROM {table} "
                f"WHERE {table} MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, min(max(int(limit), 1), 100)),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()
    except (sqlite3.Error, OSError, ValueError):
        return []


def search_pipeline_stages(query, pipeline_stages):
    """Find stages whose names, status, errors or result details match the query."""
    term = str(query or "").strip().lower()
    matches = []
    if not term or not isinstance(pipeline_stages, dict):
        return matches

    for stage_name, stage_info in pipeline_stages.items():
        stage_info = stage_info if isinstance(stage_info, dict) else {}
        searchable_text = " ".join([
            str(stage_name),
            str(stage_info.get("status", "")),
            str(stage_info.get("error", "")),
            json.dumps(stage_info.get("result", {}), ensure_ascii=False, default=str),
        ]).lower()
        if term in searchable_text:
            matches.append({
                "Pipeline Stage": str(stage_name).replace("_", " ").title(),
                "Status": stage_info.get("status", "UNKNOWN"),
                "Details": str(stage_info.get("error") or "Stage details matched your search")[:240],
            })
    return matches


def make_schema_graph(entity_counts, height=480):
    """Neural-network view of the knowledge graph.

    Each entity type is a glowing neuron (soma) with branching dendrites; curved,
    multi-strand axons carry it to the central knowledge core and to related
    entities.  Hover a soma for the real entity count.  Smaller satellite neurons
    and signal pulses are decorative, so the browser never draws all the nodes.
    """
    import base64
    import random

    rng = random.Random(7)
    names = sorted(entity_counts, key=entity_counts.get, reverse=True)
    total = sum(entity_counts.values())
    palette = [  # (core colour, light tint)
        ("#a76bff", "#eadcff"), ("#3f8fff", "#d3e7ff"), ("#f3b649", "#fff1cc"),
        ("#26cbd8", "#d4fcff"), ("#ff7ccf", "#ffe1f4"), ("#7c64ff", "#ddd6ff"),
        ("#52d69a", "#d8f9e8"), ("#ff9d5c", "#ffe5d1"),
    ]
    widths = [3.0, 2.0, 1.3, 0.8]

    def rgba(hex_colour, alpha):
        h = hex_colour.lstrip("#")
        return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"

    fibres = {}       # (colour, width) -> (xs, ys)
    terminals = {}    # colour -> [(x, y)]
    pulses = []       # (x, y, colour)

    def add_fibre(colour, width, pts):
        xs, ys = fibres.setdefault((colour, width), ([], []))
        xs.extend([p[0] for p in pts] + [None])
        ys.extend([p[1] for p in pts] + [None])

    def dendrite(x, y, ang, length, depth, colour, max_depth):
        pts, a = [(x, y)], ang
        for _ in range(6):
            a += rng.uniform(-.28, .28)
            x += math.cos(a) * length / 6
            y += math.sin(a) * length / 6
            pts.append((x, y))
        add_fibre(colour, widths[min(depth, 3)], pts)
        if depth < max_depth:
            for _ in range(rng.choice([2, 2, 3]) if depth == 0 else 2):
                dendrite(x, y, a + rng.uniform(-.8, .8), length * rng.uniform(.55, .75),
                         depth + 1, colour, max_depth)
        else:
            terminals.setdefault(colour, []).append((x, y))

    def axon(p0, p1, colour, bend=.16, strands=3, main_width=1.3, pulse=True):
        (x0, y0), (x1, y1) = p0, p1
        length = math.hypot(x1 - x0, y1 - y0) or 1
        nx, ny = -(y1 - y0) / length, (x1 - x0) / length
        for s in range(strands):
            off = (bend + (s - (strands - 1) / 2) * .035) * length
            cx, cy = (x0 + x1) / 2 + nx * off, (y0 + y1) / 2 + ny * off
            pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
                    (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1)
                   for t in [i / 28 for i in range(29)]]
            add_fibre(colour, main_width if s == 0 else .8, pts)
            if pulse and s == 0:
                t = rng.uniform(.3, .7)
                pulses.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
                               (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1, colour))

    fig = go.Figure()

    # ---- ambient field: soft nebula glow + drifting particles --------------
    for r, colour in [(1.1, "rgba(90,70,220,.035)"), (.95, "rgba(80,110,230,.04)"),
                      (.75, "rgba(120,90,255,.05)"), (.5, "rgba(150,110,255,.06)"),
                      (.3, "rgba(240,190,110,.06)")]:
        fig.add_shape(type="circle", x0=-r, y0=-r * .92, x1=r, y1=r * .92,
                      line=dict(width=0), fillcolor=colour, layer="below")
    dx, dy, dc, ds = [], [], [], []
    for _ in range(320):
        a, r = rng.uniform(0, 2 * math.pi), 1.15 * math.sqrt(rng.random())
        dx.append(math.cos(a) * r * 1.2)
        dy.append(math.sin(a) * r * .9)
        dc.append(f"rgba(180,195,255,{rng.uniform(.08, .45):.2f})")
        ds.append(rng.choice([1.5, 2, 2, 3]))
    fig.add_trace(go.Scatter(x=dx, y=dy, mode="markers", hoverinfo="skip", showlegend=False,
                             marker=dict(size=ds, color=dc)))

    # ---- build neurons ------------------------------------------------------
    k = len(names)
    somas, small = {}, []
    for idx, name in enumerate(names):
        colour, light = palette[idx % len(palette)]
        ang = math.radians(140) - 2 * math.pi * idx / max(k, 1)
        sx, sy = (math.cos(ang) * .72, math.sin(ang) * .64) if k > 1 else (0, 0)
        somas[name] = (sx, sy, colour, light)

        # main dendritic tree, biased away from the core
        out = math.atan2(sy, sx)
        for d in range(6):
            dendrite(sx, sy, out + (d - 2.5) * .62 + rng.uniform(-.2, .2),
                     rng.uniform(.13, .19), 0, colour, 3)

        # two or three small satellite neurons wired back to the soma
        for j in range(rng.choice([2, 3])):
            a2 = out + rng.uniform(-1.6, 1.6)
            r2 = rng.uniform(.24, .34)
            px, py = sx + math.cos(a2) * r2, sy + math.sin(a2) * r2 * .9
            small.append((px, py, colour, light))
            for d in range(4):
                dendrite(px, py, rng.uniform(0, 2 * math.pi), rng.uniform(.06, .09), 1, colour, 3)
            axon((px, py), (sx, sy), colour, bend=rng.choice([-.2, .2]), strands=2,
                 main_width=.8, pulse=False)

        # axon bundle to the central knowledge core
        axon((sx, sy), (0, 0), colour, bend=.14 if idx % 2 else -.14)

    # golden dendrites around the core
    for d in range(9):
        dendrite(0, 0, 2 * math.pi * d / 9 + rng.uniform(-.2, .2), rng.uniform(.13, .17),
                 1, GOLD, 3)

    # real schema relationships between entity neurons
    known_links = [("Customer", "Order"), ("Order", "OrderItem"), ("OrderItem", "Product"),
                   ("OrderItem", "Seller"), ("Order", "Payment"), ("Order", "Review"),
                   ("Customer", "Location"), ("Seller", "Location")]
    link_hover = []
    for a, b in known_links:
        if a in somas and b in somas:
            (x0, y0, c0, _), (x1, y1, _, _) = somas[a], somas[b]
            axon((x0, y0), (x1, y1), c0, bend=.22, strands=2, main_width=1.0)
            link_hover.append(((x0 + x1) / 2, (y0 + y1) / 2, f"{a} → {b}"))

    # ---- draw fibres: wide faint glow, medium glow, bright core ----------
    for (colour, width), (xs, ys) in fibres.items():
        for w_mul, alpha in [(4.5, .06), (2.2, .16), (1.0, .85)]:
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", hoverinfo="skip", showlegend=False,
                                     line=dict(color=rgba(colour, alpha), width=width * w_mul,
                                               shape="spline", smoothing=.6)))

    # synaptic terminals (glowing boutons at dendrite tips)
    for colour, pts in terminals.items():
        tx, ty = [p[0] for p in pts], [p[1] for p in pts]
        fig.add_trace(go.Scatter(x=tx, y=ty, mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(size=11, color=rgba(colour, .22))))
        fig.add_trace(go.Scatter(x=tx, y=ty, mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(size=4, color="#ffffff",
                                             gradient=dict(type="radial", color=colour))))

    # signal pulses travelling along axons
    if pulses:
        fig.add_trace(go.Scatter(x=[p[0] for p in pulses], y=[p[1] for p in pulses], mode="markers",
                                 hoverinfo="skip", showlegend=False,
                                 marker=dict(size=16, color=[rgba(p[2], .35) for p in pulses])))
        fig.add_trace(go.Scatter(x=[p[0] for p in pulses], y=[p[1] for p in pulses], mode="markers",
                                 hoverinfo="skip", showlegend=False,
                                 marker=dict(size=6, color="#fffaf0")))

    # small satellite somas
    for px, py, colour, light in small:
        fig.add_trace(go.Scatter(x=[px], y=[py], mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(size=26, color=rgba(colour, .18))))
        fig.add_trace(go.Scatter(x=[px], y=[py], mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(size=11, color="#ffffff", gradient=dict(type="radial", color=colour),
                                             line=dict(color=rgba(light, .7), width=.8))))

    # relationship hover points
    if link_hover:
        fig.add_trace(go.Scatter(x=[h[0] for h in link_hover], y=[h[1] for h in link_hover], mode="markers",
                                 marker=dict(size=14, color="rgba(0,0,0,0)"), showlegend=False,
                                 text=[h[2] for h in link_hover], hovertemplate="%{text}<extra></extra>"))

    # main entity somas with real counts
    for name, (x, y, colour, light) in somas.items():
        for size, alpha in [(78, .06), (54, .13), (36, .28)]:
            fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers", hoverinfo="skip", showlegend=False,
                                     marker=dict(size=size, color=rgba(colour, alpha))))
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers", showlegend=False,
            marker=dict(size=25, color="#ffffff", gradient=dict(type="radial", color=colour),
                        line=dict(color=rgba(light, .95), width=1.4)),
            customdata=[[name, entity_counts[name], entity_counts[name] / total * 100 if total else 0]],
            hovertemplate="<b>%{customdata[0]}</b><br>Entities: %{customdata[1]:,}"
                          "<br>Share: %{customdata[2]:.1f}%<extra></extra>"))
        norm = math.hypot(x, y) or 1
        fig.add_annotation(
            x=x + x / norm * .34, y=y + y / norm * .27, showarrow=False,
            text=f"<span style='color:{colour}'>●</span>  {name}",
            font=dict(size=16, color="#f6f2ea", family="Exo 2, sans-serif"),
            bgcolor="rgba(14,16,28,.62)", bordercolor=rgba(colour, .9), borderwidth=1.3, borderpad=8)

    # ---- central knowledge core ------------------------------------------
    for size, colour in [(160, "rgba(150,110,255,.06)"), (118, "rgba(165,125,255,.12)"),
                         (90, "rgba(242,190,110,.22)")]:
        fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(size=size, color=colour)))
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers", showlegend=False,
        marker=dict(size=72, color="#e3d8ff", gradient=dict(type="radial", color="#4a2db3"),
                    line=dict(color="#f2c27a", width=3)),
        hovertemplate=f"<b>Knowledge core</b><br>{total:,} entities · {k} entity types<extra></extra>"))
    layers_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" '
        'stroke-width="1.6" stroke-linejoin="round"><path d="M12 3 2.5 8 12 13l9.5-5z"/>'
        '<path d="m2.5 12 9.5 5 9.5-5"/><path d="m2.5 16 9.5 5 9.5-5"/></svg>'
    )
    fig.add_layout_image(dict(
        source="data:image/svg+xml;base64," + base64.b64encode(layers_svg.encode()).decode(),
        x=0, y=0, xref="x", yref="y", sizex=.17, sizey=.17,
        xanchor="center", yanchor="middle", layer="above"))

    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[-1.3, 1.3], fixedrange=True),
        yaxis=dict(visible=False, range=[-1.1, 1.1], fixedrange=True, scaleanchor="x"),
        showlegend=False,
        hoverlabel=dict(bgcolor="rgba(16,18,28,.95)", bordercolor="#e9b765",
                        font=dict(color="#f3efe6", family="Exo 2, sans-serif", size=16)),
    )
    return fig


def make_donut(entity_counts, entities):
    ordered = sorted(entity_counts.items(), key=lambda kv: kv[1], reverse=True)
    top, rest = ordered[:4], ordered[4:]
    labels = [k for k, _ in top] + (["Others"] if rest else [])
    values = [v for _, v in top] + ([sum(v for _, v in rest)] if rest else [])
    colors = [PURPLE, BLUE, TEAL, GOLD, "#8a8f9c"][:len(labels)]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=.72, sort=False,
        marker=dict(colors=colors, line=dict(color="#0d0e14", width=3)),
        textinfo="none", hovertemplate="%{label}: %{value:,} (%{percent})<extra></extra>",
    ))
    centre = f"{entities / 1000:.0f}K" if entities >= 1000 else f"{entities:,}"
    fig.update_layout(
        height=240, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(text=f"<b>{centre}</b><br><span style='font-size:17px'>Entities</span>",
                          x=.5, y=.5, showarrow=False, font=dict(size=34, color="white", family="Exo 2, sans-serif"))],
    )
    total = sum(values) or 1
    legend = "".join(
        f'<div class="lg"><i style="background:{c}"></i>{l} ({v / total * 100:.1f}%)</div>'
        for l, v, c in zip(labels, values, colors)
    )
    return fig, f'<div class="legend">{legend}</div>'


# ----------------------- LOAD REPORTS ---------------------

report = read_json(PIPELINE_PATH)
stages = report.get("stages", {})
summary = report.get("summary", {})
graph_result = stages.get("KNOWLEDGE_GRAPH", {}).get("result", {})
graph_summary = graph_result.get("graph_summary", {})
validation = graph_result.get("validation", {})
anomaly = stages.get("ANOMALY_DETECTION", {}).get("result", {})
data = load_inventory()
discovery_path = latest_discovery_file()
discovery = read_json(discovery_path) if discovery_path else {}

status = summary.get("overall_status", "REPORT NOT FOUND")
success_count = summary.get("successful_stages", 0)
stage_count = summary.get("total_stages", len(stages))
entity_counts = validation.get("entity_type_counts", {})
relationship_counts = validation.get("relationship_type_counts", {})
entities = graph_summary.get("total_entities", validation.get("total_nodes", 0)) or 0
relationships = graph_summary.get("total_relationships", validation.get("total_edges", 0)) or 0
record_count = int(data["Rows"].sum()) if not data.empty else 0
success_pct = round(success_count / stage_count * 100) if stage_count else 0
avg_degree = (2 * relationships / entities) if entities else 0

last_run = first_key(summary, "end_time", "completed_at", "timestamp", "start_time") or first_key(
    report, "timestamp", "generated_at", "end_time")
if not last_run and PIPELINE_PATH.exists():
    last_run = datetime.fromtimestamp(PIPELINE_PATH.stat().st_mtime).strftime("%b %d, %Y %I:%M %p")
duration = format_duration(first_key(summary, "total_duration_seconds", "duration_seconds",
                                     "total_execution_time", "execution_time_seconds"))


def stage_ok(*names):
    """True when every named stage that exists in the report succeeded."""
    present = [stages[n] for n in names if n in stages]
    return bool(present) and all(s.get("status") == "SUCCESS" for s in present)


# ----------------------- NAV STATE -------------------------

if "active_page" not in st.session_state:
    st.session_state.active_page = "Dashboard"
page = st.session_state.active_page

# ----------------------- LAYOUT ---------------------------

rail_col, nav_col, main_col = st.columns([0.055, 0.19, 0.755], gap="small")

with rail_col:
    rail = '<div class="rail"><div class="rail-logo">⋀</div>'
    for item, icon in NAV_ITEMS.items():
        rail += f'<div class="rail-ico{" active" if page == item else ""}" title="{item}">{icon}</div>'
    rail += '<div class="rail-ico">⛉</div><div class="rail-ico">⚙</div></div>'
    html(rail)

with nav_col:
    with glass_panel("p1"):
        html(
            '<div class="brand"><div class="brand-icon">◈</div><div>'
            '<div class="brand-name">Cross-Domain<br>Intelligence</div>'
            '<div class="brand-sub">Data Discovery Platform</div></div></div>'
            '<div class="nav-heading">Navigation</div>'
        )
        for item, icon in NAV_ITEMS.items():
            label = f"{icon}   {item}" + ("" if item == "Dashboard" else "   ›")
            if st.button(label, key=f"navigation_{item}", use_container_width=True,
                         type="primary" if item == page else "secondary"):
                st.session_state.active_page = item
                st.rerun()

        checks = [
            ("Ingest", stage_ok("INGESTION")),
            ("Process", stage_ok("DATA_UNDERSTANDING", "DATA_DISCOVERY", "NLP_PROCESSING")),
            ("Graph", stage_ok("KNOWLEDGE_GRAPH")),
            ("Model", stage_ok("ANOMALY_DETECTION")),
        ]
        all_ok = all(ok for _, ok in checks)
        grid = "".join(
            f'<div><div class="health-check{"" if ok else " warn"}">{"✓" if ok else "!"}</div>'
            f'<div class="health-label">{name}</div></div>' for name, ok in checks
        )
        html(
            '<div class="health-card"><div class="health-top">'
            '<div class="health-title"><span class="dot"></span>System Health</div>'
            '<div class="health-pulse">∿</div></div>'
            f'<div class="health-sub">{"All services operational" if all_ok else "Some stages need attention"}</div>'
            f'<div class="health-grid">{grid}</div></div>'
            '<div class="version">v1.0.0 &nbsp;&nbsp;|&nbsp;&nbsp; Day 13</div>'
        )


    
with main_col:
    search_col, bell_col, profile_col = st.columns([6, 0.5, 2])

    with search_col:
        global_search = st.text_input(
            "Global Search",
            placeholder="Search datasets, entities, relations, pipelines...",
            label_visibility="collapsed",
            key="global_search"
        )

    with bell_col:
        st.markdown("<div class='bell'>🔔</div>", unsafe_allow_html=True)

    with profile_col:
        html(
            '<div class="profile"><div class="avatar">JR</div>'
            '<div><div class="p-name">Jerin Ray</div>'
            '<div class="p-role">AI &amp; DS Engineer</div></div>'
            '<span style="color:#d8d4ca">⌄</span></div>'
        )

    html(
        '<div class="hero-title">Cross-Domain <em>Intelligence</em></div>'
        '<div class="hero-sub">Autonomous Data Discovery<b>•</b>Knowledge Graph<b>•</b>'
        'Anomaly Intelligence<b>•</b>Cross-Domain Analysis</div>'
    )

    
    # ================= GLOBAL SEARCH =================
    search_term = str(global_search or "").strip()

    if search_term:
        st.markdown("### 🔎 Global Search Results")
        st.caption(
            "Searching processed datasets, indexed knowledge-graph entities, "
            "relationships and pipeline stages."
        )

        # 1. Dataset metadata search
        st.markdown("#### 📁 Datasets")
        if not data.empty:
            dataset_mask = data.astype(str).apply(
                lambda column: column.str.contains(
                    search_term, case=False, na=False, regex=False
                )
            ).any(axis=1)
            dataset_results = data.loc[dataset_mask]
        else:
            dataset_results = pd.DataFrame()

        if not dataset_results.empty:
            st.success(f"{len(dataset_results)} dataset match(es)")
            display_columns = [
                column for column in ["Dataset", "Rows", "Columns", "Size (MB)"]
                if column in dataset_results.columns
            ]
            st.dataframe(
                dataset_results[display_columns],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No dataset metadata matched this search.")

        # 2. Knowledge-graph entity search (SQLite FTS5 index)
        st.markdown("#### ✣ Knowledge Graph Entities")
        entity_results = search_graph_index(search_term, "entities_fts", limit=25)
        if entity_results:
            st.success(f"{len(entity_results)} entity match(es) shown")
            st.dataframe(
                pd.DataFrame(entity_results).rename(columns={
                    "entity_id": "Entity ID",
                    "entity_type": "Entity Type",
                    "searchable": "Indexed Content",
                }),
                use_container_width=True,
                hide_index=True,
            )
        elif not (LOG / "knowledge_graph_search.sqlite").exists():
            st.info(
                "Knowledge-graph search index is not available yet. "
                "Run the backend pipeline to build it."
            )
        else:
            st.caption("No graph entities matched this search.")

        # 3. Knowledge-graph relationship search
        st.markdown("#### ⛓ Knowledge Graph Relationships")
        relationship_results = search_graph_index(
            search_term, "relationships_fts", limit=25
        )
        if relationship_results:
            st.success(f"{len(relationship_results)} relationship match(es) shown")
            st.dataframe(
                pd.DataFrame(relationship_results).rename(columns={
                    "source_id": "Source Entity",
                    "target_id": "Target Entity",
                    "relationship_type": "Relationship Type",
                    "searchable": "Indexed Content",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No graph relationships matched this search.")

        # 4. Pipeline stage search
        st.markdown("#### ⚙ Pipeline Stages")
        stage_results = search_pipeline_stages(search_term, stages)
        summary_text = json.dumps(summary, ensure_ascii=False, default=str).lower()
        if stage_results:
            st.success(f"{len(stage_results)} pipeline stage match(es)")
            st.dataframe(
                pd.DataFrame(stage_results),
                use_container_width=True,
                hide_index=True,
            )
        elif search_term.lower() in summary_text:
            st.info("The search term appears in the overall pipeline summary.")
            st.json(summary)
        else:
            st.caption("No pipeline stages matched this search.")

        total_matches = (
            len(dataset_results) + len(entity_results)
            + len(relationship_results) + len(stage_results)
        )
        if total_matches == 0:
            st.warning(
                "No matches found. Try a dataset name, entity ID, entity type, "
                "relationship name (for example PLACED), or pipeline stage."
            )

# ================= DASHBOARD =================
    if page == "Dashboard" and not search_term:
        k1, k2, k3, k4 = st.columns(4, gap="medium")
        with k1:
            kpi("⛁", "Datasets", f"{len(data):,}", f"✓ {len(data)}/{len(FILES)} loaded", "purple")
        with k2:
            kpi("▤", "Total Records", f"{record_count:,}", "", "blue")
        with k3:
            kpi("⟲", "Pipeline Success", f"{success_count} / {stage_count}", f"◷ {success_pct}%", "green")
        with k4:
            kpi("✣", "Graph Entities", f"{entities:,}",
                "", "gold")

        left, right = st.columns([1.72, 1], gap="medium")

        with left:
            with glass_panel("p2"):
                h_left, h_right = st.columns([1.25, 1])
                with h_left:
                    panel_header("", "Knowledge Graph")
                with h_right:
                    kg_view = st.radio("Knowledge graph view", ["Graph", "Communities", "Domains"],
                                       horizontal=True, label_visibility="collapsed", key="kg_view")

                if kg_view == "Graph":
                    if entity_counts:
                        g_col, s_col = st.columns([2.8, 1])
                        with g_col:
                            st.plotly_chart(make_schema_graph(entity_counts), use_container_width=True,
                                            config={"displayModeBar": False})
                        with s_col:
                            html(
                                '<div class="kg-stats">'
                                f'<div class="kg-stat"><div class="kg-ico">✣</div><div><div class="kg-lbl">Entities</div><div class="kg-val">{entities:,}</div></div></div>'
                                f'<div class="kg-stat"><div class="kg-ico blue">⛓</div><div><div class="kg-lbl">Relationships</div><div class="kg-val">{relationships:,}</div></div></div>'
                                '<div class="kg-stat"><div class="kg-ico gold">◈</div><div><div class="kg-lbl">Communities</div><div class="kg-val">—</div></div></div>'
                                f'<div class="kg-stat"><div class="kg-ico">▦</div><div><div class="kg-lbl">Domains</div><div class="kg-val">{len(entity_counts)}</div></div></div>'
                                f'<div class="kg-stat"><div class="kg-ico gold">↗</div><div><div class="kg-lbl">Avg. Degree</div><div class="kg-val">{avg_degree:.2f}</div></div></div>'
                                '</div>'
                            )
                    else:
                        st.info("Graph entity statistics are not available in the saved pipeline report.")

                
                elif kg_view == "Communities":
                    from src.knowledge_graph.community_analyzer import CommunityAnalyzer

                    st.markdown("### Knowledge Graph Communities")
                    st.caption(
                        "Sample-based Louvain community detection "
                        "using connected Olist customer relationships."
                    )

                    if st.button(
                        "Run Community Detection",
                        key="run_community_detection",
                        type="primary",
                    ):
                        with st.spinner("Analyzing connected graph sample..."):
                            analyzer = CommunityAnalyzer()
                            result = analyzer.analyze()

                            st.session_state["community_analysis_result"] = result

                            if result.get("status") == "success":
                                analyzer.save_report(result)
                            else:
                                st.warning(result.get("message", "Analysis failed."))

                    community_result = st.session_state.get(
                        "community_analysis_result"
                    )

                    if community_result:
                        if community_result.get("status") == "success":
                            c1, c2, c3, c4 = st.columns(4)

                            c1.metric(
                                "Communities",
                                f"{community_result.get('total_communities', 0):,}",
                            )
                            c2.metric(
                                "Analyzed Nodes",
                                f"{community_result.get('analyzed_nodes', 0):,}",
                            )
                            c3.metric(
                                "Relationships",
                                f"{community_result.get('analyzed_edges', 0):,}",
                            )
                            c4.metric(
                                "Connected Components",
                                f"{community_result.get('connected_components', 0):,}",
                            )

                            st.success(community_result.get("message"))

                            st.info(
                                f"Analysis scope: {community_result.get('analysis_scope')} | "
                                f"Sampled customers: "
                                f"{community_result.get('sampled_customers', 0):,}"
                            )

                            community_rows = []

                            for community in community_result.get("communities", []):
                                community_rows.append({
                                    "Community ID": community["community_id"],
                                    "Size": community["size"],
                                    "Entity Types": ", ".join(
                                        f"{key}: {value}"
                                        for key, value in community["entity_types"].items()
                                    ),
                                    "Sample Entities": ", ".join(
                                        community["sample_entities"]
                                    ),
                                })

                            if community_rows:
                                st.dataframe(
                                    community_rows,
                                    use_container_width=True,
                                    hide_index=True,
                                )

                        else:
                            st.error(
                                community_result.get(
                                    "message",
                                    "Community analysis failed.",
                                )
                            )
                    else:
                        st.info(
                            "Click 'Run Community Detection' to analyze "
                            "a connected sample of the knowledge graph."
                        )


                else:
                    if not data.empty:
                        st.dataframe(data[["Dataset", "Rows", "Columns", "Size (MB)"]], hide_index=True,
                                     use_container_width=True)
                    else:
                        st.info("No processed datasets were found.")

        with right:
            with glass_panel("p3"):
                panel_header("", "Domain Distribution", '<span class="ph-link">↗</span>')
                if entity_counts:
                    donut, legend = make_donut(entity_counts, entities)
                    d_col, l_col = st.columns([1.1, 1])
                    with d_col:
                        st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False})
                    with l_col:
                        html(legend)
                else:
                    st.info("Entity type counts are unavailable.")

            with glass_panel("p4"):
                panel_header("◈", "Recent Discoveries", '<span class="ph-link">View All →</span>')
                meta = discovery.get("metadata", discovery)
                if meta:
                    when = time_ago(discovery_path)
                    rows = [
                        (f"{meta.get('dataset_pair_count', '—')} dataset pairs analysed", when),
                        (f"{meta.get('connected_dataset_pair_count', '—')} connected dataset pairs found", when),
                        (f"{meta.get('total_relationship_candidates', '—')} relationship candidates to validate", when),
                    ]
                    html("".join(
                        f'<div class="row"><div class="row-ico">▤</div><div class="row-main">{t}<small>{w}</small></div>'
                        f'<div class="row-arrow">›</div></div>' for t, w in rows
                    ))
                else:
                    st.info("No cross-domain discovery report found.")
                st.caption("Candidates are hypotheses, not verified relationships.")

        pipe_col, anomaly_col, insights_col = st.columns([1.65, 1.1, .95], gap="medium")

        with pipe_col:
            with glass_panel("p5"):
                chip = ('<span class="chip-ok">✓ Completed</span>' if stage_count and success_count == stage_count
                        else f'<span class="chip-warn">{status}</span>')
                panel_header("▷", "Pipeline Execution", chip)
                icons = {"INGESTION": "⤓", "DATA_UNDERSTANDING": "⚙", "DATA_DISCOVERY": "⌕",
                         "ANOMALY_DETECTION": "◬", "NLP_PROCESSING": "¶", "KNOWLEDGE_GRAPH": "✣"}
                short_names = {"INGESTION": "Ingest", "DATA_UNDERSTANDING": "Understand",
                               "DATA_DISCOVERY": "Discover", "ANOMALY_DETECTION": "Anomaly",
                               "NLP_PROCESSING": "NLP", "KNOWLEDGE_GRAPH": "Graph"}
                if stages:
                    steps = []
                    for stage_name, info in stages.items():
                        ok = info.get("status") == "SUCCESS"
                        steps.append(
                            f'<div class="step"><div class="step-ico">{icons.get(stage_name, "•")}'
                            f'<div class="step-badge{"" if ok else " warn"}">{"✓" if ok else "!"}</div></div>'
                            f'<div class="step-name">{short_names.get(stage_name, stage_name.replace("_", " ").title())}</div></div>'
                        )
                    html(
                        '<div class="flow">' + '<div class="arrow">→</div>'.join(steps) + '</div>'
                        '<div class="flow-foot">'
                        f'<div class="ff"><span>▦</span><div><small>Last Run</small>{last_run or "—"}</div></div>'
                        f'<div class="ff"><span>◷</span><div><small>Duration</small>{duration}</div></div>'
                        f'<div class="ff"><span>⛁</span><div><small>Processed Records</small>{record_count:,}</div></div>'
                        '</div>'
                    )
                else:
                    st.warning("Pipeline report not found.")

        with anomaly_col:
            with glass_panel("p6"):
                panel_header("⊟", "Anomaly Detection", '<span class="ph-link">↗</span>')
                anomaly_count = anomaly.get("anomaly_count", 0) or 0
                normal_count = anomaly.get("normal_count", 0) or 0
                total = anomaly.get("total_records") or (anomaly_count + normal_count)
                rate = anomaly_count / total * 100 if total else 0
                c_col, s_col = st.columns([1.6, 1])
                with c_col:
                    drawn = False
                    if ANOMALY_CSV.exists():
                        try:
                            frame = pd.read_csv(ANOMALY_CSV)
                            numeric = frame.select_dtypes(include="number").columns.tolist()
                            if numeric:
                                chosen = "approval_delay_hours" if "approval_delay_hours" in numeric else numeric[0]
                                series = frame[chosen].dropna().head(150).reset_index(drop=True)
                                series = series.rolling(5, min_periods=1).mean()
                                peak = int(series.idxmax()) if len(series) else 0
                                trend = go.Figure()
                                trend.add_trace(go.Scatter(
                                    y=series, mode="lines", line=dict(color="#b57bff", width=2, shape="spline"),
                                    fill="tozeroy", fillcolor="rgba(157,107,255,.22)",
                                    hovertemplate=f"{chosen}: %{{y:,.2f}}<extra></extra>"))
                                trend.add_trace(go.Scatter(
                                    x=[peak], y=[series.iloc[peak]] if len(series) else [], mode="markers",
                                    marker=dict(size=11, color="#ffe3b0", line=dict(color=GOLD, width=3)),
                                    hoverinfo="skip"))
                                trend.update_layout(
                                    height=150, margin=dict(l=0, r=0, t=6, b=0), showlegend=False,
                                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                    xaxis=dict(visible=False), yaxis=dict(visible=False))
                                st.plotly_chart(trend, use_container_width=True, config={"displayModeBar": False})
                                drawn = True
                        except Exception as exc:
                            st.caption(f"Anomaly chart unavailable: {exc}")
                    if not drawn:
                        st.caption("No investigation CSV found for the trend chart.")
                with s_col:
                    html(
                        '<div class="an-side"><div class="an-lbl">Anomalies</div>'
                        f'<div class="an-val">{anomaly_count:,}</div>'
                        '<div class="an-lbl">Anomaly Rate</div>'
                        f'<div class="an-chip">{rate:.2f}%</div></div>'
                    )
                st.caption(f"{normal_count:,} records normal · Anomaly ≠ confirmed fraud.")

        with insights_col:
            with glass_panel("p7"):
                panel_header("✧", "Insights", '<span class="ph-link">View All →</span>')
                items = []
                for rel, count in list(relationship_counts.items())[:2]:
                    items.append((f"{rel.replace('_', ' ').title()} relationships", f"{count:,}"))
                if anomaly.get("anomaly_count"):
                    items.append(("Transactional anomalies (Order) detected", f"{anomaly['anomaly_count']:,} events"))
                if items:
                    html("".join(
                        f'<div class="insight"><div>{t}<b>{v}</b></div><span class="row-arrow">›</span></div>'
                        for t, v in items[:3]
                    ))
                else:
                    st.info("Relationship statistics unavailable.")
                st.caption("Connectivity does not establish causation.")

    
    # =================== DATA MANAGEMENT ===================
    elif page == "Data Management":
        with glass_panel("p8"):
            page_header(
                "Dataset Explorer",
                "Search, filter, inspect and download processed datasets."
            )

            if data.empty:
                st.warning("No matching processed Parquet datasets found.")
            else:
                dataset_search = st.text_input(
                    "Search datasets",
                    placeholder="Type a dataset name..."
                )

                if dataset_search.strip():
                    available_datasets = data[
                        data["Dataset"].astype(str).str.contains(
                            dataset_search.strip(),
                            case=False,
                            na=False,
                            regex=False
                        )
                    ]["Dataset"].tolist()
                else:
                    available_datasets = []

                if not dataset_search.strip():
                    st.info("Type a dataset name to search.")
                elif not available_datasets:
                     st.warning("No datasets match your search.")
                else:
                    selected = st.selectbox(
                        "Select dataset",
                        available_datasets
                    )

                    selected_path = Path(
                        data.loc[
                            data["Dataset"] == selected,
                            "Path"
                        ].iloc[0]
                    )

                    frame = pd.read_parquet(selected_path)

                    # Dataset statistics
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Rows", f"{len(frame):,}")
                    m2.metric("Total Columns", len(frame.columns))

                    memory_mb = (
                        frame.memory_usage(deep=True).sum() / (1024 ** 2)
                    )
                    m3.metric("Memory Usage", f"{memory_mb:.2f} MB")

                    st.caption(f"Source file: {selected_path.name}")
                    st.divider()

                    # Global search
                    
                    st.markdown("#### Search records")

                    record_search = st.text_input(
                        "Search across all columns",
                        placeholder="Enter an ID, city, status or value...",
                        key="record_search"
                    )

                    filtered = frame.copy()

                    if record_search.strip():
                        search_mask = filtered.astype(str).apply(
                            lambda column: column.str.contains(
                                record_search.strip(),
                                case=False,
                                na=False,
                                regex=False
                            )
                        ).any(axis=1)

    

                        filtered = filtered.loc[search_mask]

                    # Column filter
                    st.markdown("#### Column filter")
                    filter_col, filter_val_col = st.columns([1, 2])

                    with filter_col:
                        filter_column = st.selectbox(
                            "Choose a column",
                            ["No filter"] + list(frame.columns)
                        )

                    with filter_val_col:
                        filter_value = st.text_input(
                            "Filter value",
                            placeholder="Enter a value to filter..."
                        )

                    if filter_column != "No filter" and filter_value.strip():
                        column_mask = filtered[filter_column].astype(
                            "string"
                        ).str.contains(
                            filter_value.strip(),
                            case=False,
                            na=False,
                            regex=False
                        )
                        filtered = filtered.loc[column_mask]

                    st.caption(
                        f"{len(filtered):,} records match your search and filters."
                    )

                    # Column selection
                    st.markdown("#### Display settings")
                    selected_columns = st.multiselect(
                        "Choose columns to display",
                        list(frame.columns),
                        default=list(frame.columns)
                    )

                    if not selected_columns:
                        st.warning("Select at least one column to display.")
                    else:
                        # Pagination
                        page_col, size_col = st.columns(2)

                        with size_col:
                            page_size = st.selectbox(
                                "Rows per page",
                                [50, 100, 500],
                                index=1
                            )

                        total_pages = max(
                            1,
                            (len(filtered) + page_size - 1) // page_size
                        )

                        with page_col:
                            current_page = st.number_input(
                                "Page",
                                min_value=1,
                                max_value=total_pages,
                                value=1,
                                step=1,
                                key="dataset_explorer_page"
                            )

                        start = (int(current_page) - 1) * page_size
                        end = start + page_size
                        page_data = filtered.iloc[start:end][selected_columns]

                        st.markdown("#### Dataset preview")
                        st.dataframe(
                            page_data,
                            use_container_width=True,
                            height=420
                        )

                        st.caption(
                            f"Page {current_page} of {total_pages} · "
                            f"Showing {len(page_data):,} rows "
                            f"out of {len(filtered):,} filtered records."
                        )

                        # Download filtered data
                        csv_data = filtered[selected_columns].to_csv(
                            index=False
                        ).encode("utf-8")

                        st.download_button(
                            "Download filtered CSV",
                            data=csv_data,
                            file_name=(
                                f"{selected.lower().replace(' ', '_')}_filtered.csv"
                            ),
                            mime="text/csv",
                            use_container_width=False
                        )


    
    # ================= DISCOVERY ENGINE =================
    elif page == "Discovery Engine":
        page_header(
            "Discovery Engine",
            "Cross-domain relationship discovery, confidence analysis and validation evidence."
        )

        if discovery:
            meta = discovery.get("metadata", discovery)

            dataset_names = meta.get("dataset_names", [])
            pair_analysis = meta.get("dataset_pair_analysis", [])
            confidence = meta.get("confidence_summary", {})

            total_candidates = meta.get("total_relationship_candidates", 0)
            total_pairs = meta.get("dataset_pair_count", 0)
            connected_pairs = meta.get("connected_dataset_pair_count", 0)

            # KPI CARDS
            col1, col2, col3 = st.columns(3, gap="medium")

            with col1:
                kpi(
                    "⛁", "Datasets Analysed",
                    meta.get("dataset_count", len(dataset_names)),
                    "Source datasets", "purple"
                )

            with col2:
                kpi(
                    "⇄", "Dataset Pairs",
                    total_pairs,
                    f"{connected_pairs} connected pairs", "blue"
                )

            with col3:
                kpi(
                    "✣", "Relationship Candidates",
                    total_candidates,
                    "Require validation", "gold"
                )

            st.caption(
                f"Engine: {meta.get('engine', 'Cross-Domain Pattern Discovery Engine')} "
                f"· Status: {meta.get('status', 'UNKNOWN')} "
                f"· Generated: {meta.get('generated_at', 'Not available')}"
            )

            st.divider()

            # CONFIDENCE DISTRIBUTION
            st.markdown("### Confidence Distribution")

            levels = ["HIGH", "MEDIUM", "LOW"]
            values = [confidence.get(level, 0) for level in levels]

            chart_col, summary_col = st.columns([1.6, 1])

            with chart_col:
                fig = go.Figure(
                    go.Bar(
                        x=levels,
                        y=values,
                        text=values,
                        textposition="outside",
                        marker=dict(
                            color=["#43c995", "#648cf5", "#d5a85e"]
                        ),
                        hovertemplate="%{x}: %{y} candidates<extra></extra>"
                    )
                )

                fig.update_layout(
                    height=300,
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=30, b=20),
                    xaxis_title="Confidence Level",
                    yaxis_title="Candidate Count",
                    showlegend=False
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

            with summary_col:
                with glass_panel("discovery_confidence"):
                    panel_header("◈", "Confidence Summary")

                    for level in levels:
                        count = confidence.get(level, 0)
                        st.markdown(f"**{level}**")
                        st.progress(
                            count / max(total_candidates, 1)
                        )
                        st.caption(f"{count} candidates")

            st.divider()

            # BUILD RELATIONSHIP TABLE
            relationship_rows = []

            for pair in pair_analysis:
                for rel in pair.get("relationships", []):
                    relationship_rows.append({
                        "Dataset A": rel.get(
                            "dataset_a", pair.get("dataset_a", "")
                        ),
                        "Dataset B": rel.get(
                            "dataset_b", pair.get("dataset_b", "")
                        ),
                        "Column A": rel.get("column_a", ""),
                        "Column B": rel.get("column_b", ""),
                        "Relationship Type": rel.get(
                            "relationship_type", "UNKNOWN"
                        ),
                        "Confidence": rel.get("confidence", "UNKNOWN"),
                        "Validation": rel.get(
                            "validation_status", "UNVERIFIED"
                        ),
                        "Name Similarity": rel.get("name_similarity", 0),
                        "Overlap": rel.get("overlap_coefficient", 0),
                        "Uniqueness A": rel.get("uniqueness_ratio_a", 0),
                        "Uniqueness B": rel.get("uniqueness_ratio_b", 0)
                    })

            relationships_df = pd.DataFrame(relationship_rows)

            # RELATIONSHIP EXPLORER
            st.markdown("### Relationship Candidate Explorer")

            if not relationships_df.empty:
                search_col, confidence_col, validation_col = st.columns(
                    [2, 1, 1]
                )

                with search_col:
                    search_text = st.text_input(
                        "Search relationships",
                        placeholder="Search dataset, column or relationship...",
                        key="discovery_search"
                    )

                with confidence_col:
                    confidence_filter = st.selectbox(
                        "Confidence",
                        ["ALL", "HIGH", "MEDIUM", "LOW"],
                        key="discovery_confidence_filter"
                    )

                with validation_col:
                    validation_options = ["ALL"] + sorted(
                        relationships_df["Validation"].dropna().unique().tolist()
                    )

                    validation_filter = st.selectbox(
                        "Validation Status",
                        validation_options,
                        key="discovery_validation_filter"
                    )

                filtered = relationships_df.copy()

                if search_text.strip():
                    mask = filtered.astype("string").apply(
                        lambda column: column.str.contains(
                            search_text.strip(),
                            case=False,
                            na=False,
                            regex=False
                        )
                    ).any(axis=1)

                    filtered = filtered.loc[mask]

                if confidence_filter != "ALL":
                    filtered = filtered[
                        filtered["Confidence"] == confidence_filter
                    ]

                if validation_filter != "ALL":
                    filtered = filtered[
                        filtered["Validation"] == validation_filter
                    ]

                st.caption(
                    f"Showing {len(filtered)} of "
                    f"{len(relationships_df)} relationship candidates."
                )

                st.dataframe(
                    filtered,
                    width="stretch",
                    hide_index=True,
                    height=460,
                    row_height=38

                )

                st.download_button(
                    "Download filtered candidates CSV",
                    data=filtered.to_csv(index=False).encode("utf-8"),
                    file_name="cross_domain_relationship_candidates.csv",
                    mime="text/csv",
                    key="discovery_csv_download"
                )

            else:
                st.info("No relationship candidates are available.")

            st.divider()

            # DATASET PAIR ANALYSIS
            st.markdown("### Dataset Pair Analysis")

            pair_rows = []

            for pair in pair_analysis:
                candidate_count = pair.get("candidate_count", 0)

                pair_rows.append({
                    "Dataset A": pair.get("dataset_a", ""),
                    "Dataset B": pair.get("dataset_b", ""),
                    "Candidate Count": candidate_count,
                    "Status": (
                        "Candidates Found"
                        if candidate_count > 0
                        else "No Candidates"
                    )
                })

            pair_df = pd.DataFrame(pair_rows)

            if not pair_df.empty:
                st.dataframe(
                    pair_df,
                    use_container_width=True,
                    hide_index=True,
                    height=350
                )

            with st.expander("View analysed datasets"):
                st.write(dataset_names)

            with st.expander("View complete discovery report"):
                st.json(discovery)

            st.warning(
                "Relationship candidates are hypotheses based on sampled "
                "value overlap, column-name similarity and uniqueness. "
                "They are not verified joins or evidence of causation. "
                "Validate candidates against the full datasets before use."
            )

        else:
            st.info(
                "No cross-domain discovery report found under logs/cross_domain."
            )

    

    # ==================== KNOWLEDGE GRAPH ==================
    elif page == "Knowledge Graph":
        page_header("Knowledge Graph", "Seven-dataset graph integration summary.")
        a, b, c = st.columns(3, gap="medium")
        with a:
            kpi("✣", "Entities", f"{entities:,}", "Nodes", "purple")
        with b:
            kpi("⛓", "Relationships", f"{relationships:,}", "Directed edges", "blue")
        with c:
            kpi("✓", "Validation", "VALID" if validation.get("is_valid") else "NOT VERIFIED",
                f"Isolated: {validation.get('isolated_nodes', '—')}", "green")
        if entity_counts:
            with glass_panel("p10"):
                panel_header("✣", "Schema Constellation")
                st.plotly_chart(make_schema_graph(entity_counts), use_container_width=True,
                                config={"displayModeBar": False})
        left, right = st.columns(2, gap="medium")
        with left:
            with glass_panel("p11"):
                panel_header("◈", "Entity types")
                st.dataframe(pd.DataFrame([{"Entity": k, "Count": v} for k, v in entity_counts.items()]),
                             hide_index=True, use_container_width=True)
        with right:
            with glass_panel("p12"):
                panel_header("⛓", "Relationship types")
                st.dataframe(pd.DataFrame([{"Relationship": k, "Count": v} for k, v in relationship_counts.items()]),
                             hide_index=True, use_container_width=True)
        st.info("The complete graph is large. The dashboard displays aggregate statistics to keep the browser responsive.")

    # ====================== INTELLIGENCE ====================
    elif page == "Intelligence":
        page_header("Anomaly Intelligence", "Isolation Forest findings. Anomaly does not mean fraud or confirmed error.")
        a, b, c = st.columns(3, gap="medium")
        with a:
            kpi("▤", "Records Analysed", f'{anomaly.get("total_records", 0):,}', "Orders", "blue")
        with b:
            kpi("◬", "Anomalies Flagged", f'{anomaly.get("anomaly_count", 0):,}', "Investigate", "gold")
        with c:
            kpi("⚙", "Detection Method", anomaly.get("method", "—"), "Unsupervised", "purple")
        with glass_panel("p13"):
            panel_header("✧", "Model details")
            st.write("**Features:** " + (", ".join(anomaly.get("features", [])) or "Not available"))
            st.caption(anomaly.get("interpretation", "No interpretation in report."))
            if ANOMALY_CSV.exists():
                with st.expander("Preview investigated records"):
                    frame = pd.read_csv(ANOMALY_CSV)
                    st.dataframe(frame.head(100), use_container_width=True)
                    st.download_button("Download anomaly results", ANOMALY_CSV.read_bytes(),
                                       file_name=ANOMALY_CSV.name, mime="text/csv")

    # ========================= REPORTS ======================
    elif page == "Reports":
        page_header("Reports & Audit", "Saved outputs from the backend pipeline.")
        with glass_panel("p14"):
            panel_header("▤", "Pipeline report")
            if PIPELINE_PATH.exists():
                st.download_button("Download pipeline JSON", PIPELINE_PATH.read_bytes(),
                                   file_name=PIPELINE_PATH.name, mime="application/json")
                with st.expander("Inspect pipeline report"):
                    st.json(report)
            else:
                st.warning("Pipeline report is not available.")
        with glass_panel("p15"):
            panel_header("◈", "Recent log files")
            report_files = sorted(
                [p for p in LOG.rglob("*") if p.is_file() and p.suffix in {".json", ".csv"}],
                key=lambda p: p.stat().st_mtime, reverse=True,
            )[:30] if LOG.exists() else []
            if report_files:
                html("".join(
                    f'<div class="row"><div class="row-ico">▤</div><div class="row-main">{p.relative_to(ROOT)}'
                    f'<small>{p.stat().st_size / 1024:.1f} KB · {time_ago(p)}</small></div></div>'
                    for p in report_files
                ))
            else:
                st.info("No log files found.")

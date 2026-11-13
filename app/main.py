from __future__ import annotations

import json
import hashlib
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from src.regions import REGIONS, VARIABLES
from src.nasa_power import fetch_daily
from src.cleaning import monthly_aggregate, coverage_summary
from src.statistics import analyze_trend
from src.ai_engine import explain_result
from src.live_weather import get_current_conditions, commercial_api_configured
from src.ai_assistant import assistant_configured, ask_earthwise
from src.user_datasets import (
    DatasetStorageError, UploadValidationError, create_workspace_token,
    database_configured, delete_dataset, list_datasets, load_dataset,
    parse_uploaded_file, save_dataset, validate_workspace_token,
)


# ---------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------
@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def retrieve_climate_data(city, latitude, longitude, start_date, end_date, variable):
    """Cache a dataset by its complete request identity, including date range."""
    return fetch_daily(
        city, latitude, longitude, start_date, end_date, parameters=(variable,)
    )


def get_dataset_key(city, variable, start_year, end_year):
    return (city, variable, int(start_year), int(end_year))


def build_ai_context(city, variable, start_year, end_year, weather, monthly, result):
    context = {
        "selected_city": city,
        "province_or_region": REGIONS[city]["province"],
        "indicator": VARIABLES[variable]["label"],
        "NASA_POWER_parameter": variable,
        "requested_period": f"{start_year}-01-01 to {end_year}-12-31",
        "data_source_note": "NASA POWER gridded satellite/model-assisted estimates, not local weather-station observations.",
        "important_limitations": [
            "Historical trends are not forecasts.",
            "The basic Kendall trend test does not correct for monthly seasonality or serial autocorrelation.",
            "This product is not an emergency warning or disaster prediction service.",
        ],
    }
    if weather:
        context["current_model_conditions"] = weather
    if monthly is not None and not monthly.empty:
        context["monthly_observation_count"] = int(len(monthly))
        context["first_month"] = str(monthly["date"].min().date())
        context["last_month"] = str(monthly["date"].max().date())
    if result:
        context["trend_statistics"] = result
    return context


# ---------------------------------------------------------------------
# Visual components
# ---------------------------------------------------------------------
def render_globe(selected_city: str):
    points = [
        {"name": name, "lat": info["latitude"], "lng": info["longitude"],
         "province": info["province"]}
        for name, info in REGIONS.items()
    ]
    html = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
      html,body{margin:0;background:#06111d;color:#dff7ff;font-family:Arial,sans-serif;overflow:hidden}
      #globe{width:100%;height:520px;position:relative}
      #load{position:absolute;inset:0;display:grid;place-items:center;color:#8ceafa;font-size:13px;letter-spacing:.1em}
      .hint{position:absolute;left:18px;bottom:12px;font-size:11px;letter-spacing:.08em;color:#91b6c9;pointer-events:none}
    
</style></head><body>
    <div id="globe"><div id="load">LOADING EARTH VISUALIZATION…</div></div>
    <div class="hint">DRAG TO ROTATE · SCROLL TO ZOOM · SELECTED CITY HIGHLIGHTED</div>
    <script>
    const points=__POINTS__, selected=__SELECTED__;
    const el=document.getElementById('globe');
    const fallback=()=>{document.getElementById('load').textContent='3D GLOBE UNAVAILABLE — CHECK NETWORK OR CDN ACCESS';};
    const timer=setTimeout(fallback,12000);
    const script=document.createElement('script');
    script.src='https://unpkg.com/globe.gl';
    script.onerror=fallback;
    script.onload=()=>{
      try{
        const globe=Globe()(el)
          .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
          .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
          .backgroundColor('#06111d').showAtmosphere(true)
          .atmosphereColor('#55c9ed').atmosphereAltitude(.16)
          .pointsData(points).pointLat(d=>d.lat).pointLng(d=>d.lng)
          .pointColor(d=>d.name===selected?'#ffd36a':'#6ce7f4')
          .pointAltitude(.018).pointRadius(.12).pointResolution(12)
          .pointLabel(d=>'<b>'+d.name+'</b><br>'+d.province)
          .width(el.clientWidth).height(520);
        globe.pointOfView({lat:29.5,lng:69.5,altitude:2.05},1200);
        globe.controls().autoRotate=true;globe.controls().autoRotateSpeed=.22;
        globe.controls().enableDamping=true;
        clearTimeout(timer);document.getElementById('load').remove();
        window.addEventListener('resize',()=>globe.width(el.clientWidth));
      }catch(e){fallback();}
    };
    document.head.appendChild(script);
    </script></body></html>"""
    html = html.replace("__POINTS__", json.dumps(points)).replace(
        "__SELECTED__", json.dumps(selected_city)
    )
    components.html(html, height=540, scrolling=False)


def render_satellite_map(imagery_date):
    points = [
        {"name": name, "lat": info["latitude"], "lng": info["longitude"],
         "province": info["province"]}
        for name, info in REGIONS.items()
    ]
    html = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <style>html,body,#map{height:100%;margin:0;background:#071522;color:#dff7ff}
    .leaflet-popup-content-wrapper,.leaflet-popup-tip{background:#0b1d2d;color:#eaf8ff}
    #fallback{padding:24px;font:14px Arial,sans-serif}</style></head><body>
    <div id="map"><div id="fallback">Loading NASA satellite map…</div></div>
    <script>
    const points=__POINTS__, mapEl=document.getElementById('map');
    const fail=()=>{mapEl.innerHTML='<div id="fallback">Satellite map could not load. Check network access and try again.</div>';};
    const css=document.querySelector('link');css.onerror=fail;
    const js=document.createElement('script');js.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';js.onerror=fail;
    js.onload=()=>{
      try{
        mapEl.innerHTML='';
        const map=L.map('map',{zoomControl:true,worldCopyJump:true}).setView([29.5,69.5],5);
        L.tileLayer('https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/__DATE__/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg',{
          maxZoom:9,attribution:'Imagery: NASA/GSFC/ESDIS GIBS · VIIRS SNPP True Color'
        }).addTo(map);
        const pins=L.featureGroup();
        points.forEach(p=>L.circleMarker([p.lat,p.lng],{radius:5,color:'#b7f6ff',weight:1,fillColor:'#35cce8',fillOpacity:.9})
          .bindPopup('<b>'+p.name+'</b><br>'+p.province).addTo(pins));
        pins.addTo(map);L.control.scale({imperial:false}).addTo(map);
        setTimeout(()=>map.invalidateSize(),250);
      }catch(e){fail();}
    };
    document.head.appendChild(js);
    </script></body></html>"""
    html = html.replace("__POINTS__", json.dumps(points)).replace(
        "__DATE__", imagery_date.isoformat()
    )
    components.html(html, height=570, scrolling=False)


def render_empty_state():
    st.markdown("""
    <div class="ew-empty">
      <div class="ew-empty-icon">◌</div>
      <div class="ew-empty-title">Your climate workspace is ready</div>
      <div class="ew-empty-copy">Choose a location and indicator, set a time range, then retrieve the NASA POWER dataset to unlock analysis and ask EARTHWISE AI about the evidence.</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Page configuration and design system
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="EARTHWISE AI — Earth Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root{--bg:#07111d;--panel:#0d1b2a;--line:rgba(151,190,218,.14);--cyan:#67dceb;--muted:#91a8bb;--white:#f1f7fb}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:radial-gradient(ellipse at 80% -10%,rgba(24,111,153,.18),transparent 36%),linear-gradient(145deg,#060d17,#091827 58%,#07111d);color:var(--white)}
[data-testid="stHeader"]{background:rgba(5,13,23,.78);backdrop-filter:blur(16px)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0c1b2b,#081421);border-right:1px solid var(--line)}
[data-testid="stSidebar"] *{color:#e6f0f7}
.block-container{max-width:1440px;padding-top:1.35rem;padding-bottom:3rem}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.035em}
.ew-top{display:flex;align-items:center;justify-content:space-between;gap:16px;margin:0 0 20px}
.ew-brand{font:700 .82rem 'Space Grotesk';letter-spacing:.18em;color:#e9f8ff}
.ew-brand span{color:var(--cyan)}
.ew-status{border:1px solid rgba(103,220,235,.2);background:rgba(12,55,70,.28);border-radius:30px;padding:7px 11px;color:#a9eaf1;font-size:.66rem;letter-spacing:.11em;font-weight:700}
.ew-hero{position:relative;overflow:hidden;border:1px solid rgba(119,185,214,.2);border-radius:22px;padding:clamp(24px,4vw,40px);background:linear-gradient(112deg,rgba(13,42,63,.96),rgba(9,26,43,.96) 65%,rgba(10,36,52,.9));margin-bottom:22px}
.ew-hero:after{content:'';position:absolute;width:330px;height:330px;right:-90px;top:-165px;border:1px solid rgba(103,220,235,.14);border-radius:50%;box-shadow:0 0 0 28px rgba(103,220,235,.025),0 0 0 58px rgba(103,220,235,.018);pointer-events:none}
.ew-eyebrow{color:#78dce9;font-size:.67rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase}
.ew-title{font:700 clamp(2.2rem,5vw,3.55rem)/1.04 'Space Grotesk';letter-spacing:-.065em;color:#f5fbff;margin:12px 0;max-width:780px}
.ew-sub{color:#b0c5d5;max-width:720px;line-height:1.7;font-size:.94rem}
.ew-chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}
.ew-chip{border:1px solid rgba(111,199,225,.2);background:rgba(7,27,43,.6);padding:7px 10px;border-radius:7px;color:#bdebf4;font-size:.64rem;letter-spacing:.09em}
.ew-section{font:600 1.17rem 'Space Grotesk';color:#edf7ff;margin:.7rem 0 .5rem}
.ew-muted{color:#92aabd;font-size:.82rem;line-height:1.6}
.ew-card{border:1px solid var(--line);border-radius:15px;background:linear-gradient(145deg,rgba(15,34,52,.88),rgba(9,23,38,.92));padding:17px 18px;height:100%}
.ew-card-label{font-size:.65rem;color:#9bb5c8;letter-spacing:.13em;text-transform:uppercase;font-weight:700}
.ew-card-value{font:700 1.45rem 'Space Grotesk';color:#f4fbff;margin-top:8px}
.ew-card-note{font-size:.74rem;color:#92aabd;margin-top:5px;line-height:1.5}
.ew-empty{border:1px dashed rgba(132,181,208,.27);border-radius:18px;padding:38px 22px;text-align:center;background:rgba(10,26,42,.45);margin:12px 0}
.ew-empty-icon{font-size:2rem;color:#72d9e8}
.ew-empty-title{font:600 1.15rem 'Space Grotesk';color:#edf7ff;margin:10px 0}
.ew-empty-copy{color:#91aabd;max-width:600px;margin:auto;line-height:1.7;font-size:.85rem}
.ew-ai-banner{border:1px solid rgba(103,220,235,.23);border-radius:17px;padding:20px 22px;background:linear-gradient(120deg,rgba(11,49,66,.92),rgba(10,24,41,.96));margin:8px 0 18px}
.ew-ai-kicker{font-size:.64rem;color:#70dce9;font-weight:700;letter-spacing:.2em}
.ew-ai-title{font:600 1.35rem 'Space Grotesk';color:#f2fbff;margin:7px 0}
.ew-ai-copy{font-size:.81rem;color:#a4bdce;line-height:1.6}
div[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(15,35,53,.9),rgba(9,23,38,.94));border:1px solid var(--line);border-radius:13px;padding:13px 15px}
div[data-testid="stMetricLabel"]{color:#9db5c7}
div[data-testid="stMetricValue"]{color:#f4faff;font-family:'Space Grotesk',sans-serif}
div.stButton>button,div.stDownloadButton>button{border-radius:9px;border:1px solid rgba(103,220,235,.3);background:linear-gradient(105deg,#12647d,#22558d);color:white;font-weight:700;min-height:2.65rem;transition:all .18s ease}
div.stButton>button:hover,div.stDownloadButton>button:hover{transform:translateY(-1px);border-color:#9beaf3;color:white;box-shadow:0 8px 20px rgba(31,142,186,.16)}
.stSelectbox>div>div,.stNumberInput>div>div{background:rgba(7,20,34,.9);border-color:var(--line);border-radius:9px}
[data-testid="stExpander"]{border:1px solid var(--line);border-radius:12px;background:rgba(9,25,41,.45)}
.stAlert{border-radius:11px}
[data-testid="stChatMessage"]{background:rgba(12,29,46,.72);border:1px solid var(--line);border-radius:14px}
[data-testid="stChatInput"]{border-color:rgba(103,220,235,.28)}
.ew-footer{color:#718da3;font-size:.67rem;letter-spacing:.07em;text-align:center;padding:20px 0 5px}
footer{visibility:hidden}
@media(max-width:700px){.block-container{padding:1rem .8rem 2rem}.ew-title{font-size:2.15rem}.ew-hero{padding:23px 19px}.ew-top{align-items:flex-start;flex-direction:column}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
/* Product polish: stronger hierarchy, consistent surfaces, and responsive controls */
:root{color-scheme:dark;--bg:#071321;--panel:#0d2031;--line:rgba(153,194,219,.16);--cyan:#58d5e7;--muted:#91aabd;--white:#f3f8fc;--amber:#ffbd72}
.stApp{background:radial-gradient(ellipse at 86% 0%,rgba(36,139,168,.16),transparent 31%),radial-gradient(ellipse at 0% 60%,rgba(39,83,139,.10),transparent 38%),#071321}
.block-container{max-width:1480px;padding-top:1.1rem}
[data-testid="stSidebar"]{min-width:285px!important;background:linear-gradient(180deg,#0d2031 0%,#091725 100%)}
[data-testid="stSidebar"] [data-testid="stRadio"] label{font-size:.88rem;font-weight:600}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"]{gap:5px}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label{padding:8px 10px;border:1px solid transparent;border-radius:9px;transition:background .18s ease,border-color .18s ease}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked){background:rgba(62,174,199,.12);border-color:rgba(88,213,231,.25)}
.ew-top{padding:5px 2px 13px;border-bottom:1px solid rgba(153,194,219,.10);margin-bottom:18px}
.ew-brand{font-size:.78rem;letter-spacing:.16em}
.ew-status{background:rgba(20,95,112,.18);border-color:rgba(88,213,231,.24);white-space:nowrap}


.ew-title{font-size:clamp(2.15rem,4.8vw,3.35rem);max-width:740px}
.ew-sub{max-width:680px}
.ew-hero-aside{position:relative;z-index:1;min-width:190px;padding:17px 19px;border:1px solid rgba(130,205,220,.19);border-radius:14px;background:rgba(4,19,32,.42);backdrop-filter:blur(8px)}
.ew-hero-aside-label{font-size:.61rem;letter-spacing:.16em;color:#83dce8;font-weight:700}
.ew-hero-aside-value{font:600 1.05rem 'Space Grotesk';color:#f2fbff;margin-top:8px}
.ew-hero-aside-note{font-size:.7rem;color:#9bb7c8;margin-top:5px;line-height:1.5}
.ew-section{display:flex;align-items:center;gap:10px;margin:1.2rem 0 .55rem}
.ew-section:before{content:'';display:block;width:3px;height:17px;border-radius:5px;background:linear-gradient(180deg,#67e0e9,#3b91bd)}
.ew-card{box-shadow:0 10px 28px rgba(0,0,0,.10);transition:transform .18s ease,border-color .18s ease}
.ew-card:hover{transform:translateY(-2px);border-color:rgba(88,213,231,.28)}
div[data-testid="stMetric"]{min-height:112px;box-shadow:0 8px 24px rgba(0,0,0,.08)}
div[data-testid="stMetricLabel"] p{font-size:.72rem;letter-spacing:.035em}
div[data-testid="stMetricValue"]{font-size:1.65rem}
[data-testid="stTabs"] button{font-weight:600}
[data-testid="stTabs"] button[aria-selected="true"]{color:#70e0eb!important;border-bottom-color:#58d5e7!important}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}
[data-testid="stChatMessage"]{padding:14px 16px}
[data-testid="stChatInput"] textarea{background:rgba(7,20,34,.85)}
[data-testid="stSelectbox"] label,[data-testid="stDateInput"] label,[data-testid="stRadio"] label{color:#c5d7e4}
.stCaption{color:#8faabd}
.ew-footer{border-top:1px solid rgba(153,194,219,.10);line-height:1.9}
@media(max-width:850px){.ew-hero{grid-template-columns:1fr}.ew-hero-aside{max-width:280px}.ew-status{font-size:.58rem}}
@media(max-width:560px){[data-testid="stSidebar"]{min-width:unset!important}.ew-hero{padding:23px 19px}.ew-hero-aside{width:100%;max-width:none}.ew-title{font-size:2.05rem}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------
if "frames" not in st.session_state:
    st.session_state.frames = {}
if "ai_messages" not in st.session_state:
    st.session_state.ai_messages = []
if "weather_cache_local" not in st.session_state:
    st.session_state.weather_cache_local = {}
if "workspace_token" not in st.session_state:
    st.session_state.workspace_token = create_workspace_token()

# ---------------------------------------------------------------------
# Sidebar: navigation + global controls
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌍 EARTHWISE **AI**")
    st.caption("EARTH INTELLIGENCE PLATFORM")
    st.divider()
    page = st.radio(
        "WORKSPACE",
        ["Mission Control", "Climate Intelligence", "AI Earth Scientist", "Earth Explorer", "Data Library"],
        label_visibility="visible",
    )
    st.divider()
    st.markdown("### Location")
    provinces = ["All regions"] + sorted({item["province"] for item in REGIONS.values()})
    province = st.selectbox("Province / region", provinces, key="province_filter")
    city_options = sorted([
        name for name, info in REGIONS.items()
        if province == "All regions" or info["province"] == province
    ])
    city = st.selectbox("City", city_options, key="selected_city")
    st.caption(
        f"{REGIONS[city]['province']} · {REGIONS[city]['latitude']:.3f}° N, "
        f"{REGIONS[city]['longitude']:.3f}° E"
    )
    st.divider()
    st.markdown("### Climate dataset")
    variable = st.selectbox(
        "Indicator", list(VARIABLES),
        format_func=lambda key: f"{VARIABLES[key]['label']} · {VARIABLES[key]['unit']}",
    )
    current_year = date.today().year
    years = list(range(1981, current_year + 1))
    default_start = 2001 if 2001 in years else years[0]
    start_year = st.selectbox("Start year", years, index=years.index(default_start))
    end_years = [year for year in years if year >= start_year]
    preferred_end = min(current_year - 1, 2025)
    end_index = end_years.index(preferred_end) if preferred_end in end_years else len(end_years) - 1
    end_year = st.selectbox("End year", end_years, index=end_index)
    retrieve = st.button("Retrieve climate dataset", type="primary", use_container_width=True)
    st.divider()
    st.caption("HISTORICAL SOURCE · NASA POWER Daily Point API")
    st.caption(f"{len(REGIONS)} mapped urban centres · Not the complete national locality gazetteer")
    st.caption("Modelled/gridded estimates · Not station observations")
    if not commercial_api_configured():
        st.caption("Open-Meteo free endpoint: non-commercial evaluation only.")

if retrieve:
    coords = REGIONS[city]
    with st.spinner(f"Retrieving {city} climate records from NASA POWER…"):
        try:
            frame, metadata = retrieve_climate_data(
                city, coords["latitude"], coords["longitude"],
                f"{int(start_year)}0101", f"{int(end_year)}1231", variable,
            )
            key = get_dataset_key(city, variable, start_year, end_year)
            st.session_state.frames[key] = {"data": frame, "metadata": metadata}
            st.toast(f"{city} dataset is ready", icon="🌍")
        except Exception:
            st.error("NASA POWER could not return this dataset. Check your connection, date range, and try again.")

dataset_key = get_dataset_key(city, variable, start_year, end_year)
dataset = st.session_state.frames.get(dataset_key)
df = dataset["data"] if dataset else None
metadata = dataset["metadata"] if dataset else {}
monthly = monthly_aggregate(df, variable) if df is not None else None
trend = analyze_trend(monthly, variable) if monthly is not None else None
analysis_unit = "mm/month" if variable == "PRECTOTCORR" else VARIABLES[variable]["unit"]

# Weather is fetched only for the selected city, with provider-side module cache.
weather = None
try:
    weather = get_current_conditions(
        REGIONS[city]["latitude"], REGIONS[city]["longitude"], city
    )
except Exception:
    weather = None

ai_context = build_ai_context(
    city, variable, start_year, end_year, weather, monthly, trend
)

# Keep the assistant transcript aligned with the evidence currently on screen.
# A conversation started for another city/indicator/period must not silently
# carry over into a new analytical context.
ai_context_signature = (city, variable, int(start_year), int(end_year))
if st.session_state.get("ai_context_signature") != ai_context_signature:
    st.session_state.ai_messages = []
    st.session_state.ai_context_signature = ai_context_signature

# ---------------------------------------------------------------------
# Shared header
# ---------------------------------------------------------------------
st.markdown(f"""
<div class="ew-top">
  <div class="ew-brand">EARTHWISE <span>AI</span> &nbsp; / &nbsp; EARTH INTELLIGENCE</div>
  <div class="ew-status">PAKISTAN-FIRST PLATFORM &nbsp; · &nbsp; DATA ON DEMAND</div>
</div>
<section class="ew-hero">
  <div>
    <div class="ew-eyebrow">EARTH OBSERVATION · CLIMATE INTELLIGENCE · AI</div>
    <div class="ew-title">Earth intelligence for {city}.</div>
    <div class="ew-sub">Explore environmental signals for {REGIONS[city]["province"]}, investigate historical climate evidence, and ask better questions about our changing planet.</div>
    <div class="ew-chips">
      <span class="ew-chip">NASA POWER HISTORICAL DATA</span>
      <span class="ew-chip">MODEL-BASED CONDITIONS</span>
      <span class="ew-chip">CONVERSATIONAL AI</span>
    </div>
  </div>
  <aside class="ew-hero-aside">
    <div class="ew-hero-aside-label">ACTIVE LOCATION</div>
    <div class="ew-hero-aside-value">{city}</div>
    <div class="ew-hero-aside-note">{REGIONS[city]["province"]} · Pakistan<br>{REGIONS[city]["latitude"]:.2f}° N, {REGIONS[city]["longitude"]:.2f}° E</div>
  </aside>
</section>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Mission Control
# ---------------------------------------------------------------------
if page == "Mission Control":
    st.markdown('<div class="ew-section">Mission Control</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ew-muted">{city}, {REGIONS[city]["province"]} · '
        f'Your selected location and live model conditions at a glance.</div>',
        unsafe_allow_html=True,
    )
    if weather:
        w1, w2, w3, w4 = st.columns(4)
        w1.metric("Air temperature", f'{weather["temperature_2m"]:.1f} °C',
                  f'Feels like {weather["apparent_temperature"]:.1f} °C' if weather.get("apparent_temperature") is not None else None)
        w2.metric("Relative humidity", f'{weather["relative_humidity_2m"]:.0f}%')
        w3.metric("Wind speed", f'{weather["wind_speed_10m"]:.1f} km/h')
        w4.metric("Precipitation", f'{weather["precipitation"]:.1f} mm')
        st.caption(
            f'{weather["condition_text"]} · Provider timestamp: {weather["provider_time"]} '
            f'({weather["timezone"]}) · {weather["source"]} · '
            'Model-based conditions, not a local station observation.'
        )
    else:
        st.info("Current conditions are temporarily unavailable. Historical climate analysis remains available.")
    st.markdown('<div class="ew-section">Your intelligence workspace</div>', unsafe_allow_html=True)
    if df is not None and monthly is not None:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Valid daily records", f'{coverage_summary(df, variable)["valid_rows"]:,}')
        c2.metric("Monthly observations", f"{len(monthly):,}")
        c3.metric("Data coverage", f'{coverage_summary(df, variable)["coverage_pct"]:.1f}%')
        c4.metric("Analysis period", f'{metadata.get("requested_start", "")[:4]}–{metadata.get("requested_end", "")[:4]}')
        fig = px.line(monthly, x="date", y=variable, labels={
            "date": "Month", variable: f"{VARIABLES[variable]['label']} ({analysis_unit})"
        })
        fig.update_traces(line=dict(color="#67dceb", width=2.4))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,23,38,.45)",
            font=dict(color="#b8cbd8", family="DM Sans"), height=330,
            margin=dict(l=5, r=10, t=15, b=5), xaxis_title=None,
            yaxis=dict(gridcolor="rgba(145,180,205,.12)", title=analysis_unit),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
    else:
        render_empty_state()
        st.info("Use the controls in the left panel to choose a city, indicator and time range, then retrieve the historical dataset.")
    st.markdown('<div class="ew-section">Explore the platform</div>', unsafe_allow_html=True)
    quick = st.columns(3)
    quick[0].markdown('<div class="ew-card"><div class="ew-card-label">01 / Climate intelligence</div><div class="ew-card-value">Read the signal</div><div class="ew-card-note">Historical trends, scientific context, and downloadable evidence.</div></div>', unsafe_allow_html=True)
    quick[1].markdown('<div class="ew-card"><div class="ew-card-label">02 / AI Earth Scientist</div><div class="ew-card-value">Ask deeper questions</div><div class="ew-card-note">A conversational assistant grounded in the selected location and dataset.</div></div>', unsafe_allow_html=True)
    quick[2].markdown('<div class="ew-card"><div class="ew-card-label">03 / Earth Explorer</div><div class="ew-card-value">Explore our planet</div><div class="ew-card-note">Interactive globe, NASA imagery and mapped Pakistan cities.</div></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Climate Intelligence
# ---------------------------------------------------------------------
elif page == "Climate Intelligence":
    st.markdown('<div class="ew-section">Climate Intelligence</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ew-muted">{city} · {VARIABLES[variable]["label"]} · '
        f'{analysis_unit} · {start_year}–{end_year}</div>',
        unsafe_allow_html=True,
    )
    if df is None or monthly is None:
        render_empty_state()
        st.info("Retrieve the selected dataset using the left panel to unlock the analysis.")
    else:
        coverage = coverage_summary(df, variable)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Data coverage", f'{coverage["coverage_pct"]:.1f}%')
        m2.metric("Valid daily records", f'{coverage["valid_rows"]:,}')
        m3.metric("Monthly observations", f"{len(monthly):,}")
        m4.metric("Available records", f'{coverage["first_date"] or "—"} → {coverage["last_date"] or "—"}')
        chart = px.area(monthly, x="date", y=variable, labels={
            "date": "Month", variable: f"{VARIABLES[variable]['label']} ({analysis_unit})"
        })
        chart.update_traces(
            line=dict(color="#67dceb", width=2.4),
            fillcolor="rgba(74,196,224,.12)",
            hovertemplate="%{x|%b %Y}<br>%{y:.2f}<extra></extra>",
        )
        chart.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(7,20,34,.35)",
            font=dict(family="DM Sans", color="#b7cbd9"),
            margin=dict(l=5, r=10, t=18, b=5), height=390, hovermode="x unified",
            xaxis=dict(showgrid=False, zeroline=False, title=None),
            yaxis=dict(gridcolor="rgba(145,180,205,.12)", zeroline=False, title=analysis_unit),
        )
        st.plotly_chart(chart, use_container_width=True, config={"displaylogo": False, "responsive": True})
        st.caption("Monthly precipitation is summed; all other indicators are monthly means.")
        st.markdown('<div class="ew-section">Trend assessment</div>', unsafe_allow_html=True)
        if trend and trend.get("status") == "ok":
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("Direction", trend["direction"].title())
            t2.metric("Sen slope / decade", f'{trend["sen_slope_per_decade"]:.4g} {analysis_unit}')
            p_value = trend.get("p_value")
            t3.metric("Kendall p-value", f"{p_value:.4g}" if p_value is not None else "Unavailable")
            sig = trend.get("significant_005")
            t4.metric("Significant at 0.05", "Yes" if sig is True else "No" if sig is False else "Unavailable")
            st.markdown('<div class="ew-ai-banner"><div class="ew-ai-kicker">EARTHWISE INTELLIGENCE</div><div class="ew-ai-title">Evidence-led trend interpretation</div><div class="ew-ai-copy">A transparent summary of computed statistics. This historical analysis is not a forecast and does not establish causation.</div></div>', unsafe_allow_html=True)
            st.markdown(explain_result(city, VARIABLES[variable]["label"], analysis_unit, trend))
            ci = trend.get("slope_ci95_per_year")
            if ci and len(ci) == 2:
                st.caption(f"Sen slope 95% confidence interval: {ci[0] * 10:.4g} to {ci[1] * 10:.4g} {analysis_unit} per decade.")
        else:
            st.warning((trend or {}).get("message", "Not enough valid observations to calculate a reliable trend."))
        with st.expander("Methodology and scientific limitations"):
            st.write("Trend method: Kendall tau significance test and Sen's slope.")
            st.write("The current simple trend test does not correct for monthly seasonality or serial autocorrelation.")
            st.write("NASA POWER is a gridded satellite/model-assisted product, not a substitute for local weather-station observations.")
            st.write("The analysis describes historical patterns. It is not a forecast, attribution study, or disaster warning.")
        st.download_button(
            "Download monthly dataset (CSV)", monthly.to_csv(index=False),
            f"{city.lower().replace(' ', '_')}_{variable.lower()}_{start_year}_{end_year}.csv",
            "text/csv", use_container_width=False,
        )
        with st.expander("Data provenance"):
            st.write("Source: NASA POWER Daily Point API")
            st.write("Coordinates:", REGIONS[city])
            st.write("Requested period:", metadata.get("requested_start"), "to", metadata.get("requested_end"))
            st.write("NASA parameter:", variable)
            st.markdown("[NASA POWER API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)")

# ---------------------------------------------------------------------
# Conversational AI
# ---------------------------------------------------------------------
elif page == "AI Earth Scientist":
    st.markdown('<div class="ew-ai-banner"><div class="ew-ai-kicker">EARTHWISE AI · CONVERSATIONAL INTELLIGENCE</div><div class="ew-ai-title">Meet your AI Earth Scientist</div><div class="ew-ai-copy">Ask questions about climate, environmental signals, the selected city, or your retrieved dataset. Answers are instructed to distinguish evidence from uncertainty.</div></div>', unsafe_allow_html=True)
    st.caption(f"Active context: {city}, {REGIONS[city]['province']} · {VARIABLES[variable]['label']} · {start_year}–{end_year}")
    if not assistant_configured():
        st.warning("Conversational AI is not connected yet. Add Neon AI Gateway credentials or an OpenAI fallback key in the app's private Secrets.")
        st.code(
            'NEON_AI_GATEWAY_BASE_URL = "https://YOUR-BRANCH-api.ai.YOUR-REGION.aws.neon.tech"\n'
            'NEON_AI_GATEWAY_TOKEN = "your-neon-scoped-credential"\n'
            'NEON_AI_MODEL = "gpt-5-mini"\n\n'
            '# Optional direct OpenAI fallback\n'
            'OPENAI_API_KEY = "your-openai-api-key"\n'
            'OPENAI_MODEL = "gpt-4.1-mini"',
            language="toml",
        )
        st.markdown("[OpenAI API platform](https://platform.openai.com/api-keys) · [API billing](https://platform.openai.com/settings/organization/billing)")
        st.caption("Never paste credentials into chat or commit them to GitHub. Add them only in Streamlit Cloud → App settings → Secrets.")
    else:
        st.success("AI engine configured · Provider credentials are read server-side from app Secrets.")
    for message in st.session_state.ai_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if assistant_configured():
        prompt = st.chat_input("Ask EARTHWISE AI about climate, data, or our planet…")
        if prompt:
            st.session_state.ai_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("EARTHWISE AI is thinking…"):
                    try:
                        answer = ask_earthwise(
                            prompt, ai_context, st.session_state.ai_messages[:-1]
                        )
                        st.markdown(answer)
                        st.session_state.ai_messages.append({"role": "assistant", "content": answer})
                    except RuntimeError as exc:
                        st.error(str(exc))
    if st.session_state.ai_messages and st.button("Clear conversation"):
        st.session_state.ai_messages = []
        st.rerun()
    with st.expander("What this assistant can and cannot do"):
        st.write("It can explain climate indicators, interpret the currently loaded statistics, help explore scientific concepts, and summarize supplied context.")
        st.write("It cannot independently verify sensor data, issue official alerts, prove causes, or turn historical trends into forecasts. Answers can be wrong; check important claims against cited primary sources.")

# ---------------------------------------------------------------------
# Earth Explorer — only the selected visualization is mounted
# ---------------------------------------------------------------------
elif page == "Earth Explorer":
    st.markdown('<div class="ew-section">Earth Explorer</div>', unsafe_allow_html=True)
    view = st.radio("Explore", ["3D Earth", "NASA satellite imagery", "Pakistan city atlas"], horizontal=True)
    if view == "3D Earth":
        st.caption("Interactive textured Earth with mapped Pakistan urban centres. The texture is a visual basemap, not live satellite video.")
        render_globe(city)
    elif view == "NASA satellite imagery":
        imagery_date = st.date_input(
            "Imagery date", value=date.today() - timedelta(days=3),
            min_value=date(2012, 1, 1), max_value=date.today(),
            help="NASA VIIRS true-colour imagery is a daily composite. The latest date may not yet be processed.",
        )
        st.caption("NASA GIBS · VIIRS Suomi-NPP corrected reflectance · Daily composite, not live video.")
        render_satellite_map(imagery_date)
        st.caption("Cloud cover, acquisition gaps and processing delays can affect imagery availability.")
    else:
        map_df = pd.DataFrame([
            {"City": name, "Province": info["province"], "Latitude": info["latitude"],
             "Longitude": info["longitude"], "Selected": "Selected" if name == city else "Other"}
            for name, info in REGIONS.items()
        ])
        fig = px.scatter_geo(
            map_df, lat="Latitude", lon="Longitude", color="Selected", hover_name="City",
            hover_data={"Province": True, "Latitude": ":.3f", "Longitude": ":.3f", "Selected": False},
            color_discrete_map={"Selected": "#67dceb", "Other": "#4d8dff"},
        )
        fig.update_geos(
            scope="asia", projection_type="natural earth",
            center={"lat": 29.5, "lon": 69.5}, lataxis_range=[23, 38], lonaxis_range=[60, 78],
            showland=True, landcolor="#10283b", showocean=True, oceancolor="#071522",
            showcountries=True, countrycolor="#31536b", showcoastlines=True,
            coastlinecolor="#31536b", showframe=False, bgcolor="rgba(0,0,0,0)",
        )
        fig.update_traces(marker=dict(size=7, opacity=.85, line=dict(width=.7, color="#c9f8ff")))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#a9c2d5", family="DM Sans"),
            margin=dict(l=0, r=0, t=8, b=0), height=520,
            legend=dict(orientation="h", y=1.05, x=0),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
        st.caption(f"{len(REGIONS)} mapped urban centres. Approximate city-centre coordinates; not the complete PBS 657-locality directory.")

# ---------------------------------------------------------------------
# Data Library
# ---------------------------------------------------------------------
elif page == "Data Library":
    st.markdown('<div class="ew-section">Data Library</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="ew-muted">Upload, validate, privately store and revisit your own environmental datasets. '
        'CSV, Excel and JSON files are supported.</div>',
        unsafe_allow_html=True,
    )

    workspace_token = st.session_state.workspace_token
    with st.expander("Private workspace recovery key", expanded=False):
        st.warning(
            "This key grants access to every dataset saved in this workspace. "
            "Copy it somewhere private. Anyone who has it can open or delete these uploads."
        )
        st.code(workspace_token, language=None)
        recovery_key = st.text_input(
            "Open an existing workspace with its recovery key",
            type="password",
            key="workspace_recovery_input",
            placeholder="Paste your ew1_ recovery key",
        )
        if st.button("Open saved workspace", key="open_saved_workspace"):
            if validate_workspace_token(recovery_key.strip()):
                st.session_state.workspace_token = recovery_key.strip()
                st.session_state.pop("pending_user_upload", None)
                st.session_state.pop("saved_dataset_preview", None)
                st.session_state.pop("selected_saved_dataset_id", None)
                st.success("Workspace key accepted.")
                st.rerun()
            else:
                st.error("That recovery key is not valid. Check that you copied the complete key.")

    st.markdown('<div class="ew-section">Upload a dataset</div>', unsafe_allow_html=True)
    if not database_configured():
        st.warning(
            "Permanent uploads need a PostgreSQL database. The upload interface is ready, "
            "but saving is disabled until the database connection is configured."
        )
        st.code(
            'EARTHWISE_DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"',
            language="toml",
        )
        st.caption(
            "Create a hosted PostgreSQL database (for example, with Neon or Supabase), "
            "then add its private connection string in Streamlit Cloud → App settings → Secrets. "
            "Never put database credentials in GitHub or in this page."
        )
    else:
        uploaded_file = st.file_uploader(
            "Choose CSV, Excel or JSON",
            type=["csv", "xlsx", "xls", "xlsm", "json"],
            max_upload_size=15,
            help="Maximum 15 MB, 100,000 rows and 100 columns. Excel imports the first worksheet.",
        )
        upload_fingerprint = None
        if uploaded_file is not None:
            raw_upload = uploaded_file.getvalue()
            upload_fingerprint = hashlib.sha256(raw_upload).hexdigest()
            st.caption(f"{uploaded_file.name} · {len(raw_upload) / (1024 * 1024):.2f} MB")
            if st.button("Validate file and preview", type="secondary", key="validate_user_upload"):
                try:
                    validated_frame = parse_uploaded_file(uploaded_file.name, raw_upload)
                    st.session_state.pending_user_upload = {
                        "fingerprint": upload_fingerprint,
                        "filename": uploaded_file.name,
                        "data": validated_frame,
                    }
                    st.success("File validation passed. Review the preview before saving.")
                except UploadValidationError as exc:
                    st.session_state.pop("pending_user_upload", None)
                    st.error(str(exc))
                except Exception:
                    st.session_state.pop("pending_user_upload", None)
                    st.error("The file could not be validated. Check its format and try again.")

        pending = st.session_state.get("pending_user_upload")
        if pending and pending.get("fingerprint") == upload_fingerprint:
            preview = pending["data"]
            metric1, metric2, metric3 = st.columns(3)
            metric1.metric("Validated rows", f"{len(preview):,}")
            metric2.metric("Columns", f"{len(preview.columns):,}")
            metric3.metric("Missing cells", f"{int(preview.isna().sum().sum()):,}")
            st.caption("Preview · first 20 rows")
            st.dataframe(preview.head(20), use_container_width=True, hide_index=True)
            if st.button("Save permanently to my workspace", type="primary", key="save_user_upload"):
                try:
                    with st.spinner("Saving your dataset to secure persistent storage…"):
                        stored_id = save_dataset(
                            st.session_state.workspace_token,
                            pending["filename"],
                            preview,
                        )
                    st.session_state.pop("pending_user_upload", None)
                    st.session_state.pop("saved_dataset_preview", None)
                    st.success(f"Dataset saved successfully · Reference {stored_id}")
                    st.rerun()
                except DatasetStorageError as exc:
                    st.error(str(exc))
        elif pending:
            st.session_state.pop("pending_user_upload", None)

    st.markdown('<div class="ew-section">My saved datasets</div>', unsafe_allow_html=True)
    saved_datasets = []
    if database_configured():
        try:
            saved_datasets = list_datasets(st.session_state.workspace_token)
            if saved_datasets:
                st.dataframe(
                    pd.DataFrame([
                        {
                            "File": item["filename"],
                            "Format": item["format"],
                            "Rows": item["rows"],
                            "Uploaded (UTC)": item["uploaded_at"],
                        }
                        for item in saved_datasets
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )
                dataset_options = {item["id"]: item for item in saved_datasets}
                selected_saved_id = st.selectbox(
                    "Select a saved dataset",
                    list(dataset_options),
                    format_func=lambda key: (
                        f'{dataset_options[key]["filename"]} · '
                        f'{dataset_options[key]["rows"]:,} rows · {dataset_options[key]["format"]}'
                    ),
                    key="selected_saved_dataset_id",
                )
                action_col1, action_col2 = st.columns(2)
                with action_col1:
                    if st.button("Open selected dataset", use_container_width=True):
                        try:
                            selected_frame = load_dataset(
                                st.session_state.workspace_token, selected_saved_id
                            )
                            st.session_state.saved_dataset_preview = {
                                "id": selected_saved_id,
                                "data": selected_frame,
                            }
                        except DatasetStorageError as exc:
                            st.error(str(exc))
                with action_col2:
                    if st.button("Delete selected dataset", use_container_width=True):
                        try:
                            if delete_dataset(st.session_state.workspace_token, selected_saved_id):
                                st.session_state.pop("saved_dataset_preview", None)
                                st.success("Dataset deleted from this workspace.")
                                st.rerun()
                            else:
                                st.warning("That dataset was not found in this workspace.")
                        except DatasetStorageError as exc:
                            st.error(str(exc))
                saved_preview = st.session_state.get("saved_dataset_preview")
                if saved_preview and saved_preview.get("id") == selected_saved_id:
                    st.markdown("#### Saved dataset preview")
                    saved_frame = saved_preview["data"]
                    st.caption(f'{len(saved_frame):,} rows · {len(saved_frame.columns):,} columns')
                    st.dataframe(saved_frame, use_container_width=True, hide_index=True, height=420)
                    st.download_button(
                        "Download saved dataset (CSV)",
                        saved_frame.to_csv(index=False),
                        f'{Path(dataset_options[selected_saved_id]["filename"]).stem}_export.csv',
                        "text/csv",
                    )
            else:
                st.info("No saved uploads in this workspace yet. Validate a file above to get started.")
        except DatasetStorageError as exc:
            st.error(str(exc))
    else:
        st.caption("Saved datasets will appear here after PostgreSQL storage is connected.")

    st.markdown('<div class="ew-section">NASA POWER research dataset</div>', unsafe_allow_html=True)
    if df is None:
        st.info("No NASA POWER dataset is loaded for the current sidebar selection.")
    else:
        st.markdown(f"**{city} · {VARIABLES[variable]['label']} · {start_year}–{end_year}**")
        st.dataframe(df, use_container_width=True, hide_index=True, height=360)
        st.download_button(
            "Download daily source data (CSV)", df.to_csv(index=False),
            f"{city.lower().replace(' ', '_')}_{variable.lower()}_{start_year}_{end_year}_daily.csv",
            "text/csv",
        )
        if monthly is not None:
            st.markdown("#### Monthly aggregate")
            st.dataframe(monthly, use_container_width=True, hide_index=True)
            st.download_button(
                "Download monthly aggregate (CSV)", monthly.to_csv(index=False),
                f"{city.lower().replace(' ', '_')}_{variable.lower()}_{start_year}_{end_year}_monthly.csv",
                "text/csv",
            )
        with st.expander("NASA POWER dataset metadata"):
            st.json(metadata)

# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------
st.divider()
st.markdown("""
<div class="ew-footer">
  EARTHWISE AI · PAKISTAN-FIRST EARTH INTELLIGENCE<br>
  Created by Muhammad Abbubakar · Founder<br>
  Historical research and data exploration · Not an emergency monitoring service
</div>
""", unsafe_allow_html=True)

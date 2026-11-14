"""EARTHWISE AI — Premium rebuild (Streamlit).
Preserves the original backend exactly (src/nasa_power, cleaning, statistics,
anomalies, ai_engine, live_weather, regions) and adds real-data modules:
  src/air_quality.py  — Open-Meteo / CAMS air quality, no key
  src/risk.py         — transparent risk screening from computed trend + live data
  src/ai_assistant.py — evidence-bound assistant, answers only from loaded data
No fake / sample data anywhere. Every number is labelled with source + time.
Only env var: OPEN_METEO_API_KEY (optional, commercial weather use).
"""
from pathlib import Path
import sys, json, html
from datetime import date, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from src.regions import REGIONS, VARIABLES
from src.nasa_power import fetch_daily, save_city_data
from src.cleaning import monthly_aggregate, coverage_summary
from src.statistics import analyze_trend
from src.ai_engine import explain_result
from src.anomalies import seasonal_anomalies
from src.live_weather import get_current_conditions, get_weather_forecast, get_national_weather_snapshot, commercial_api_configured, WEATHER_CODES
from src.air_quality import get_air_quality
from src.risk import compute_risk, project_trend
from src.ai_assistant import answer_question
from src.advisory import advisory_summary, daily_health_verdict, farmer_advisory, rain_warning
from src.animations import ANIMATION_CSS, DESIGN_CSS, INTRO_CSS, build_ticker_items, demo_is_default, forecast_cards_html, hero_now_html, hero_symbol_html, intro_html, ticker_html, weather_animation_class
from src.geolocation import (
    GEO_QUERY_LAT, GEO_QUERY_LON, GEO_QUERY_STATUS,
    parse_geo_query_params, resolve_detected_location, reverse_geocode,
)

def weather_symbol(code):
    try: code = int(code)
    except (TypeError, ValueError): return "🌤️"
    if code == 0: return "☀️"
    if code in (1, 2): return "🌤️"
    if code == 3: return "☁️"
    if code in (45, 48): return "🌫️"
    if 51 <= code <= 67: return "🌧️"
    if 71 <= code <= 77: return "❄️"
    if 80 <= code <= 82: return "🌦️"
    if 85 <= code <= 86: return "🌨️"
    if 95 <= code <= 99: return "⛈️"
    return "🌤️"

def kpi(label, value, note="", accent="#7ee8d6", delay_ms=0):
    st.markdown(f'<div class="kpi" style="animation-delay:{int(delay_ms)}ms"><div class="kpi-label">{label}</div><div class="kpi-value" style="color:{accent}">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)

def section(title, sub=""):
    st.markdown(f'<div class="ew-section">{title}</div>' + (f'<p class="ew-sub2">{sub}</p>' if sub else ""), unsafe_allow_html=True)

def _answer_html(text):
    """Render an assistant answer inside a raw-HTML bubble.

    Answers are written in Markdown (**bold**), but Streamlit does not
    parse Markdown inside a raw-HTML div — the ** markers showed literally
    in the example answer and chat bubbles. Escape everything first, then
    turn **...** into <b>...</b> so bold renders and no HTML from the
    answer can leak through.
    """
    import re
    safe_text = html.escape(str(text))
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe_text)

def _stat(label, value):
    """One compact stat tile (value wraps, never truncates)."""
    return f'<div class="ew-stat"><div class="ew-stat-label">{html.escape(str(label))}</div><div class="ew-stat-value">{html.escape(str(value))}</div></div>'

def _num(v, fmt):
    return fmt.format(v) if isinstance(v, (int, float)) else "—"

def safe(fn, label):
    try: return fn()
    except Exception as exc:
        st.warning(f"{label} is temporarily unavailable: {exc}")
        return None

def render_earth_globe(selected_city):
    points = [{"name": n, "lat": i["latitude"], "lng": i["longitude"], "province": i["province"]} for n, i in REGIONS.items()]
    html = """<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
html,body,#globe{width:100%;height:100%;margin:0;padding:0;background:#06111d;overflow:hidden}
.hint{position:absolute;left:14px;bottom:10px;z-index:2;color:#a8c8d8;font:600 10px Arial,sans-serif;letter-spacing:.12em;background:rgba(5,17,29,.72);padding:7px 9px;border:1px solid rgba(125,205,225,.18);border-radius:6px;pointer-events:none}
</style></head><body><div id="globe"><div id="load" style="color:#a8c8d8;font:600 11px Arial;padding:20px">INITIALIZING EARTH VISUALIZATION…</div></div>
<div class="hint">DRAG TO ROTATE · SCROLL TO ZOOM · HOVER OVER PINS</div>
<script src="https://unpkg.com/globe.gl"></script><script>
const cityPoints = __CITY_DATA__; const selectedCity = __SELECTED_CITY__; const el = document.getElementById('globe');
try { const globe = Globe()(el).globeImageUrl('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg').bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png').backgroundColor('#06111d').showAtmosphere(true).atmosphereColor('#55c9ed').atmosphereAltitude(0.16).pointsData(cityPoints).pointLat(d=>d.lat).pointLng(d=>d.lng).pointColor(d=>d.name===selectedCity?'#ffd36a':'#6ce7f4').pointAltitude(0.018).pointRadius(0.12).pointResolution(12).pointsMerge(true).pointLabel(d=>'<b>'+d.name+'</b><br/>'+d.province).width(el.clientWidth).height(530);
globe.pointOfView({lat:29.5,lng:69.5,altitude:2.05},1200); globe.controls().autoRotate=true; globe.controls().autoRotateSpeed=0.28; globe.controls().enableDamping=true; document.getElementById('load').remove(); window.addEventListener('resize',()=>globe.width(el.clientWidth)); }
catch(e){ document.getElementById('load').textContent='3D GLOBE COULD NOT LOAD — CHECK NETWORK ACCESS'; }
</script></body></html>"""
    html = html.replace("__CITY_DATA__", json.dumps(points)).replace("__SELECTED_CITY__", json.dumps(selected_city))
    components.html(html, height=550, scrolling=False)

def render_nasa_satellite_map(imagery_date, layer_id, layer_name, attribution, opacity=0.82):
    points = [{"name": n, "lat": i["latitude"], "lng": i["longitude"], "province": i["province"]} for n, i in REGIONS.items()]
    html = """<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><style>
html,body,#map{height:100%;margin:0;background:#071522}.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:#0b1d2d;color:#eaf8ff}.map-stamp{position:absolute;z-index:500;top:12px;left:12px;padding:8px 11px;color:#eaf8ff;background:rgba(5,16,29,.88);border:1px solid rgba(130,205,225,.25);border-radius:8px;font:600 11px Arial,sans-serif;letter-spacing:.06em}
</style></head><body><div id="map"><div class="map-stamp" id="stamp"></div></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
const points = __CITY_DATA__; const layerId = __LAYER_ID__; const layerName = __LAYER_NAME__; const attribution = __ATTRIBUTION__; const mapDate='__DATE__'; const opacity=__OPACITY__;
document.getElementById('stamp').textContent = layerName+' / '+mapDate;
const map = L.map('map',{zoomControl:true,worldCopyJump:true}).setView([29.5,69.5],5);
const tileExt = layerId.indexOf('IMERG_')===0?'png':'jpg';
const tileUrl='https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/'+layerId+'/default/'+mapDate+'/GoogleMapsCompatible_Level9/{z}/{y}/{x}.'+tileExt;
L.tileLayer(tileUrl,{maxZoom:9,opacity:opacity,crossOrigin:true,attribution:attribution+' · NASA GIBS'}).addTo(map);
const pins=L.featureGroup(); points.forEach(p=>L.circleMarker([p.lat,p.lng],{radius:5,color:'#b7f6ff',weight:1,fillColor:'#35cce8',fillOpacity:.9}).bindPopup('<b>'+p.name+'</b><br>'+p.province).addTo(pins)); pins.addTo(map); L.control.scale({imperial:false}).addTo(map);
</script></body></html>"""
    html = (html.replace("__CITY_DATA__", json.dumps(points)).replace("__LAYER_ID__", json.dumps(layer_id)).replace("__LAYER_NAME__", json.dumps(layer_name)).replace("__ATTRIBUTION__", json.dumps(attribution)).replace("__DATE__", imagery_date.isoformat()).replace("__OPACITY__", str(float(opacity))))
    components.html(html, height=590, scrolling=False)

@st.cache_data(ttl=24*60*60, show_spinner=False)
def retrieve_climate_data(city, latitude, longitude, start_date, end_date, variable):
    return fetch_daily(city, latitude, longitude, start_date, end_date, parameters=(variable,))

st.set_page_config(page_title="EARTHWISE AI | Pakistan Earth Intelligence", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--page:#060f18;--surface:#0d1f2e;--surface2:#102a3d;--border:rgba(164,193,211,.14);--text:#eef6f9;--muted:#9db2c0;--accent:#7ee8d6}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:radial-gradient(1100px 500px at 85% -10%,rgba(64,190,220,.14),transparent 60%),radial-gradient(900px 480px at -10% 0%,rgba(126,232,214,.10),transparent 55%),var(--page);color:var(--text)}
[data-testid="stHeader"]{background:rgba(6,15,24,.9);border-bottom:1px solid rgba(164,193,211,.08)}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer{visibility:hidden}
.block-container{max-width:1500px;padding:1.2rem clamp(1rem,3vw,2.6rem) 3rem}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.03em;color:var(--text)}
.ew-top{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:2px 0 14px;margin-bottom:18px;border-bottom:1px solid var(--border)}
.ew-brand{font:700 .9rem 'Space Grotesk';letter-spacing:.14em}.ew-brand span{color:var(--accent)}
.ew-live{display:inline-flex;align-items:center;gap:8px;padding:7px 12px;border:1px solid rgba(126,232,214,.25);border-radius:999px;background:rgba(126,232,214,.08);color:#a9e8df;font-size:.65rem;font-weight:700;letter-spacing:.1em}
.ew-live i{width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent);animation:pulse 2s infinite}
@keyframes pulse{50%{opacity:.4}}
.ew-hero{padding:clamp(22px,3vw,36px);margin-bottom:22px;border:1px solid var(--border);border-radius:20px;background:linear-gradient(135deg,rgba(16,42,61,.9),rgba(9,24,36,.85));box-shadow:0 18px 40px rgba(0,0,0,.25)}
.ew-eyebrow{color:var(--accent);font-size:.66rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase}
.ew-title{font:700 clamp(1.9rem,4vw,3rem)/1.05 'Space Grotesk';letter-spacing:-.05em;margin:10px 0}
.ew-sub{max-width:720px;color:#b0c2ce;font-size:.93rem;line-height:1.7}
.ew-sub2{color:var(--muted);font-size:.8rem;margin:-4px 0 12px}
.ew-chip{display:inline-block;padding:6px 10px;border:1px solid var(--border);border-radius:7px;background:rgba(255,255,255,.03);color:#b7c9d3;font-size:.63rem;font-weight:600;letter-spacing:.06em;margin:4px 4px 0 0}
.ew-section{display:flex;align-items:center;gap:10px;margin:1.6rem 0 .4rem;font:600 1.15rem 'Space Grotesk'}
.ew-section:before{content:'';width:3px;height:1.05rem;border-radius:3px;background:var(--accent)}
.kpi{height:100%;padding:16px 18px;border:1px solid var(--border);border-radius:14px;background:linear-gradient(180deg,var(--surface2),var(--surface));transition:transform .15s,border-color .15s}
.kpi:hover{transform:translateY(-2px);border-color:rgba(126,232,214,.35)}
.kpi-label{color:var(--muted);font-size:.64rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
.kpi-value{font:600 1.55rem 'Space Grotesk';margin-top:8px;letter-spacing:-.03em}
.kpi-note{color:var(--muted);font-size:.74rem;margin-top:4px;line-height:1.5}
.card{padding:18px;border:1px solid var(--border);border-radius:14px;background:var(--surface)}
[data-testid="stSidebar"]{min-width:300px!important;max-width:300px!important;background:#081624;border-right:1px solid var(--border)}
[data-testid="stSidebar"] *{color:#dce8ee}
[data-testid="stSidebar"] h3{font-size:.66rem;color:var(--accent);font-weight:700;letter-spacing:.14em;text-transform:uppercase}
[data-testid="stSidebar"] label{font-size:.77rem;color:#b5c6d0;font-weight:600}
div[data-testid="stMetric"]{padding:14px 16px;border:1px solid var(--border);border-radius:13px;background:var(--surface)}
.stButton>button,.stDownloadButton>button{min-height:42px;border:1px solid var(--border)!important;border-radius:9px!important;background:#172b3b!important;color:#e8f1f5!important;font-size:.82rem!important;font-weight:600!important}
.stButton>button:hover,.stDownloadButton>button:hover{background:#20394b!important;border-color:rgba(126,232,214,.4)!important}
.stButton>button[kind="primary"]{background:var(--accent)!important;border-color:var(--accent)!important;color:#06201e!important}
.stSelectbox [data-baseweb="select"]>div,.stTextInput input,.stNumberInput input{background:#0b1b29!important;border-color:var(--border)!important;border-radius:8px!important;color:var(--text)!important}
.stTabs [data-baseweb="tab-list"]{gap:5px;padding:5px;border:1px solid var(--border);border-radius:10px;background:#091824;overflow-x:auto;flex-wrap:nowrap}
.stTabs [data-baseweb="tab"]{height:39px;padding:0 13px;border-radius:7px;color:#a9bdc9;font-size:.78rem;font-weight:600;white-space:nowrap}
.stTabs [aria-selected="true"]{background:#173747!important;color:#9ce9df!important}
[data-testid="stExpander"]{border:1px solid var(--border);border-radius:11px;background:rgba(13,31,46,.6)}
[data-testid="stPlotlyChart"],[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:12px;overflow:hidden}
.stAlert{border-radius:10px}
.ew-ai{padding:18px 20px;border:1px solid rgba(126,232,214,.22);border-left:3px solid var(--accent);border-radius:13px;background:#102b38}
.chat-q{background:#12283a;border:1px solid var(--border);border-radius:12px;padding:12px 14px;margin:6px 0}
.chat-a{background:#0e2a33;border:1px solid rgba(126,232,214,.2);border-radius:12px;padding:12px 14px;margin:6px 0}
.ew-foot{padding:18px 0 4px;color:#8299a8;font-size:.68rem;text-align:center}
@media(max-width:700px){.block-container{padding:.85rem .75rem 1.8rem!important}.ew-top{flex-direction:column;align-items:flex-start;gap:9px}.stButton>button,.stDownloadButton>button{width:100%}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>
""", unsafe_allow_html=True)
# Live animations (CSS only) + interface polish: consistent hover, focus, card rhythm.
st.markdown(f"<style>{ANIMATION_CSS}{DESIGN_CSS}{INTRO_CSS}"
"""
/* Interface polish — same dark premium look, no new deps */
.ew-sub2{color:#b0c2ce}
.card{min-height:118px}
.card:hover{border-color:rgba(126,232,214,.28)}
.stTabs [data-baseweb="tab"]:hover{color:#d6e8f0}
div[data-testid="stMetric"]{min-height:86px}
.stDownloadButton>button{width:100%}
[data-testid="stSidebar"] .stButton>button{margin-bottom:2px}
.ew-chip{transition:border-color .15s}
.ew-chip:hover{border-color:rgba(126,232,214,.45);color:#d9f2ec}
</style>
""", unsafe_allow_html=True)
if "frames" not in st.session_state: st.session_state.frames = {}
if "chat" not in st.session_state: st.session_state.chat = []
# Opening intro splash — once per session, ~3s, instead of a blank load.
# Shown BEFORE any live fetch, so the first thing a visitor sees is the
# brand, not a spinner. Reduced-motion users see a near-static splash.
# The splash is rendered in this SAME first run, overlaying the app with
# position:fixed, and its CSS fade-out (3.1s) runs from the moment the
# browser paints it — no server-side sleep + rerun. (The old sleep/rerun
# pattern raced the browser paint: on slow connections / cold Streamlit
# starts the rerun could replace the page before the splash was ever
# painted, so visitors saw it flash or not at all.)
if not st.session_state.get("intro_seen"):
    st.session_state["intro_seen"] = True
    st.markdown(intro_html(), unsafe_allow_html=True)
st.markdown('<div class="ew-top"><div class="ew-brand">EARTHWISE&nbsp;<span>AI</span>&nbsp;&nbsp;<span class="ew-brand-sub">/ PAKISTAN INTELLIGENCE</span></div><div class="ew-live"><i></i> LIVE DATA WORKSPACE</div></div>', unsafe_allow_html=True)

def empty_state(title, body, steps):
    """Designed empty state: a bordered card with steps, not a bare notice."""
    steps_html = "".join(f'<div class="ew-step">{s}</div>' for s in steps)
    st.markdown(f'<div class="ew-empty"><h3>{title}</h3><p>{body}</p>{steps_html}</div>', unsafe_allow_html=True)

def fetch_current_dataset():
    """Fetch the sidebar city/indicator/period from NASA POWER and store it.
    Returns True on success. Used by the empty-state fetch button."""
    coords = REGIONS[city]
    try:
        with st.spinner(f"Fetching {city} climate data from NASA POWER…"):
            df_new, metadata = retrieve_climate_data(city, coords["latitude"], coords["longitude"], f"{int(start_year)}0101", f"{int(end_year)}1231", variable)
            slug = f"{city.lower().replace(' ', '_').replace('(', '').replace(')', '')}_{variable.lower()}"
            save_city_data(df_new, metadata, slug)
            st.session_state.frames[(city, variable)] = df_new
        st.toast(f"{city} dataset is ready", icon="🌍")
        return True
    except Exception as exc:
        st.error(f"NASA POWER request failed: {exc}")
        return False

# Top-nav tap (mobile): a nav button below stores the target page in
# "_nav_target" and reruns. Apply it BEFORE the keyed radio is created,
# so the radio adopts the new page and the two always agree.
if "_nav_target" in st.session_state:
    st.session_state["page"] = st.session_state.pop("_nav_target")

def _on_sidebar_city_change():
    # Keep the main-area picker in sync with the sidebar picker.
    st.session_state["city_main"] = st.session_state["City"]

def _on_main_city_change():
    # Keep the sidebar picker in sync with the main-area picker, and reset
    # the province filter so the picked city is always in its options.
    st.session_state["City"] = st.session_state["city_main"]
    st.session_state["Province / Region"] = "All regions"

def _request_geo():
    # "Use my location" tapped: arm a fresh detection. geo_attempted is
    # reset so the new result is applied when it arrives.
    st.session_state["geo"] = None
    st.session_state["geo_note"] = None
    st.session_state["geo_attempted"] = False
    st.session_state["geo_request"] = True
    st.session_state["geo_request_id"] = int(st.session_state.get("geo_request_id", 0)) + 1

def _clear_geo():
    # "Change" tapped: drop the exact-position override, keep the city.
    # geo_attempted stays True so the app does not auto-prompt again.
    st.session_state["geo"] = None
    st.session_state["geo_note"] = None
    st.session_state["geo_request"] = False

# ---------- Auto location detect ----------
# Two channels feed the same apply step, and both are consumed at most
# once per session:
#  (1) the vendored custom component (components/geolocation) — the in-tab
#      channel. Its JS calls navigator.geolocation and returns the coords
#      with Streamlit.setComponentValue. A plain components.html snippet
#      CANNOT do this: its iframe sandbox has no allow-top-navigation, so
#      passing coords back via ?geo_lat= query params is blocked (verified
#      2026-11-14 in headless Chromium — assigning window.parent.location
#      throws "does not have permission to navigate the target frame").
#      The component's postMessage bridge is not affected by the sandbox.
#  (2) ?geo_lat=&geo_lon=&geo_status= query params — fallback channel, used
#      by tests and by any link carrying a detected position. Consumed here,
#      then cleared from the URL so a visitor's coordinates are never left
#      in a shareable link.
# Denial / timeout / unavailable fall back silently to the manual picker
# with a small note — never an error popup. Location is used only in this
# browser session, never stored, uploaded or shared except as coordinates
# sent to the same weather APIs the app already uses (Open-Meteo / CAMS).
_GEO_COMPONENT_DIR = Path(__file__).resolve().parents[1] / "components" / "geolocation"
_geo_component = components.declare_component("earthwise_geolocation", path=str(_GEO_COMPONENT_DIR))

def _apply_detected_location(latitude, longitude):
    """Resolve coords to a catalogue city and switch the app to it.

    Exact coords are kept for live weather/AQI; climate history uses the
    matched catalogue city. Points both pickers at the matched city (the
    province filter is reset so the city is always in the sidebar options).
    Called before the sidebar widgets are created, so they adopt it.
    """
    try:
        locality = reverse_geocode(latitude, longitude)
    except Exception:
        locality = None
    resolved = resolve_detected_location(latitude, longitude, locality)
    st.session_state["geo"] = resolved
    st.session_state["geo_attempted"] = True
    st.session_state["geo_request"] = False
    st.session_state["Province / Region"] = "All regions"
    st.session_state["City"] = resolved["city"]
    st.session_state["city_main"] = resolved["city"]
    return True

def _note_geo_declined(status):
    st.session_state["geo_attempted"] = True
    st.session_state["geo_request"] = False
    st.session_state["geo_note"] = {
        "denied": "Location access declined — pick a city below.",
        "timeout": "Location request timed out — pick a city below.",
        "unavailable": "Location is unavailable on this device or browser — pick a city below.",
    }.get(status, "Location is unavailable — pick a city below.")

# Channel (2): query params first — they are explicit and testable.
# Consumed once; always cleared from the URL afterwards so a visitor's
# coordinates are never left in a shareable link.
_geo_qp = parse_geo_query_params(st.query_params)
if _geo_qp is not None:
    if not st.session_state.get("geo_attempted"):
        if _geo_qp["status"] == "ok":
            _apply_detected_location(_geo_qp["latitude"], _geo_qp["longitude"])
        else:
            _note_geo_declined(_geo_qp["status"])
    st.query_params.clear()

# Channel (1): the custom component. request=True only while no detection
# has been attempted yet, or the visitor just tapped "Use my location".
_geo_want_request = (not st.session_state.get("geo_attempted")) or bool(st.session_state.get("geo_request"))
_geo_result = _geo_component(
    request=_geo_want_request,
    request_id=int(st.session_state.get("geo_request_id", 0)),
    key="earthwise_geolocation",
    default=None,
)
if isinstance(_geo_result, dict) and not st.session_state.get("geo_attempted"):
    if _geo_result.get("status") == "ok" and _geo_result.get("latitude") is not None:
        _apply_detected_location(_geo_result["latitude"], _geo_result["longitude"])
    elif _geo_result.get("status") in ("denied", "timeout", "unavailable"):
        _note_geo_declined(_geo_result["status"])

# ---------- Sidebar: navigation + controls ----------
PAGES = ["Overview", "Climate Analytics", "Air Quality", "Weather & Maps", "Daily Advisory", "AI Assistant", "Risk & Outlook", "Data & Downloads"]
with st.sidebar:
    st.markdown("## 🌍 EARTHWISE AI")
    st.caption("PAKISTAN EARTH INTELLIGENCE · FORGE CYBER LAB")
    # Keyed radio: Streamlit owns the navigation state. (The previous
    # index-from-session-state pattern made the radio snap back to the old
    # page on some reruns / in AppTest navigation.)
    page = st.radio("Navigate", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    st.markdown("### Location")
    provinces = ["All regions"] + sorted({v["province"] for v in REGIONS.values()})
    province = st.selectbox("Province / Region", provinces)
    city_options = sorted([c for c, v in REGIONS.items() if province == "All regions" or v["province"] == province])
    city_search = st.text_input("Find a city", placeholder="Search by city name…")
    if city_search.strip():
        city_options = [c for c in city_options if city_search.casefold() in c.casefold()]
    if not city_options:
        st.warning("No matching city. Showing all cities — try another spelling or region.")
        city_options = sorted(REGIONS)
    default_city = "Lahore" if "Lahore" in city_options else city_options[0]
    city = st.selectbox("City", city_options, index=city_options.index(default_city),
                        key="City", on_change=_on_sidebar_city_change)
    st.caption(f"{REGIONS[city]['province']} · {REGIONS[city]['latitude']:.4f}° N, {REGIONS[city]['longitude']:.4f}° E")
    st.caption(f"Directory: {len(REGIONS)} mapped urban centres · PBS Census 2023 records 657 urban localities nationally.")
    st.divider()
    st.markdown("### Climate signal")
    variable = st.selectbox("Indicator", list(VARIABLES), format_func=lambda k: f"{VARIABLES[k]['label']} · {VARIABLES[k]['unit']}")
    current_year = date.today().year
    start_year = st.number_input("Start year", min_value=1981, max_value=current_year, value=2015)
    end_year = st.number_input("End year", min_value=int(start_year), max_value=current_year, value=max(int(start_year), min(current_year - 1, 2025)))
    fetch = st.button("↗  Retrieve climate data", type="primary", use_container_width=True)
    if st.button("↻  Refresh live weather / AQI", use_container_width=True):
        get_current_conditions.clear(); get_weather_forecast.clear(); get_air_quality.clear()
        st.session_state["just_refreshed"] = True
        st.rerun()
    st.divider()
    st.caption("SOURCE / NASA POWER Daily Point API · Open-Meteo · CAMS · NASA GIBS")
    st.caption("Historical gridded estimates · Not station observations")
    with st.expander("Data provenance & limits"):
        st.markdown("- **NASA POWER** — daily gridded estimates (MERRA-2 / GEOS-IT), not station observations. [Docs](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)")
        st.markdown("- **Open-Meteo** — model-based current weather & forecast. Free endpoint is non-commercial evaluation only; commercial use needs `OPEN_METEO_API_KEY`. [Docs](https://open-meteo.com/en/docs)")
        st.markdown("- **Open-Meteo Air Quality (CAMS)** — model air-quality estimates, no key. [Docs](https://open-meteo.com/en/docs/air-quality-api)")
        st.markdown("- **NASA GIBS** — VIIRS / GPM IMERG satellite tiles, not live video or flood forecasts.")
        st.markdown("- **Official warnings** — Pakistan Meteorological Department: [weather.gov.pk](https://weather.gov.pk/)")
    if not commercial_api_configured():
        st.caption("Prototype mode: free Open-Meteo endpoint only. Set OPEN_METEO_API_KEY for commercial use.")

# A manual city change drops the exact-position override — the detected
# coordinates belong to the detected city, not the newly picked one.
_geo = st.session_state.get("geo")
if _geo and _geo.get("city") != city:
    st.session_state["geo"] = None
    _geo = None

# ---------- Top navigation — visible on mobile, where the sidebar is hidden ----------
# Plain buttons (not a second stateful widget): a tap stores the target page
# in "_nav_target" and reruns; the keyed sidebar radio adopts it on the
# next run (see above), so the two always agree and the keyed-radio fix is
# untouched. Active page is highlighted with the primary button style.
# Two rows (4 + 4) so the buttons stay tap-friendly on a phone screen.
for _nav_row in (PAGES[:4], PAGES[4:]):
    _nav_cols = st.columns(len(_nav_row))
    for _nav_col, _nav_page in zip(_nav_cols, _nav_row):
        with _nav_col:
            if st.button(_nav_page, key=f"nav_{_nav_page}",
                         type="primary" if _nav_page == page else "secondary",
                         use_container_width=True):
                st.session_state["_nav_target"] = _nav_page
                st.rerun()

# ---------- Location bar — visible on mobile, no sidebar needed ----------
# The sidebar city picker is hidden on phones, so the same controls live
# here in the main content: a city search + picker synced with the sidebar
# (on_change callbacks above keep the two in sync), and the "Use my
# location" button. Detection state comes from the geo block above.
_loc_c1, _loc_c2, _loc_c3 = st.columns([3, 2, 2])
with _loc_c1:
    _main_search = st.text_input("Find a city", placeholder="Search by city name…", key="city_search_main")
with _loc_c2:
    _main_options = sorted(REGIONS)
    if _main_search.strip():
        _main_options = [c for c in _main_options if _main_search.casefold() in c.casefold()]
    if not _main_options or city not in _main_options:
        _main_options = sorted(REGIONS)
    st.selectbox("City", _main_options, index=_main_options.index(city),
                 key="city_main", on_change=_on_main_city_change, label_visibility="collapsed")
with _loc_c3:
    if _geo:
        st.button("✕  Change", key="geo_change", use_container_width=True, on_click=_clear_geo)
    else:
        st.button("📍  Use my location", key="geo_use", type="primary", use_container_width=True, on_click=_request_geo)
if _geo:
    _geo_label = _geo.get("locality") or _geo["city"]
    if _geo["method"] == "reverse-geocode":
        st.caption(f"📍 Detected near: {_geo_label} · live weather uses your exact position ({_geo['latitude']:.4f}° N, {_geo['longitude']:.4f}° E)")
    else:
        st.caption(f"📍 Nearest city in our catalogue: {_geo['city']} ({_geo['distance_km']:.0f} km away) · live weather uses your exact position ({_geo['latitude']:.4f}° N, {_geo['longitude']:.4f}° E)")
else:
    # A detection is in flight (auto-prompt on first load, or the visitor
    # just tapped "Use my location") and no result has arrived yet: say so,
    # so the button never looks dead. It clears itself when the component
    # reports ok/denied/timeout/unavailable.
    if not st.session_state.get("geo_attempted") and _geo_result is None:
        st.caption("📍 Locating… please allow location access in your browser, or pick a city below.")
    _geo_note = st.session_state.get("geo_note")
    if _geo_note:
        st.caption(_geo_note)
    st.caption("Your location stays in this browser session — used only to pick your city and fetch its weather (Open-Meteo / CAMS). It is never stored, uploaded or shared.")

# ---------- Fetch climate data ----------
if fetch:
    coords = REGIONS[city]
    with st.status("Connecting to NASA POWER…", expanded=True) as status:
        try:
            st.write("Requesting daily climate records.")
            df_new, metadata = retrieve_climate_data(city, coords["latitude"], coords["longitude"], f"{int(start_year)}0101", f"{int(end_year)}1231", variable)
            slug = f"{city.lower().replace(' ', '_').replace('(', '').replace(')', '')}_{variable.lower()}"
            csv_path, meta_path = save_city_data(df_new, metadata, slug)
            st.session_state.frames[(city, variable)] = df_new
            status.update(label="Climate dataset retrieved", state="complete", expanded=False)
            st.toast(f"{city} dataset is ready — saved to {csv_path}", icon="🌍")
        except Exception as exc:
            status.update(label="Data retrieval failed", state="error", expanded=True)
            st.error(f"NASA POWER request failed: {exc}")

df = st.session_state.frames.get((city, variable))
demo_dataset = False
if df is None:
    slug = f"{city.lower().replace(' ', '_').replace('(', '').replace(')', '')}_{variable.lower()}"
    candidate = Path("data/raw") / f"{slug}_nasa_power_daily.csv"
    if candidate.exists():
        try:
            cached = pd.read_csv(candidate, parse_dates=["date"])
            if variable in cached.columns:
                df = cached
                demo_dataset = demo_is_default(city, variable)
        except Exception as exc:
            st.warning(f"Saved climate file could not be read: {exc}")
# First-load fallback (only for the default Lahore/T2M demo): if the cached
# demo file is missing — e.g. it was never committed to the repo — fetch the
# same real NASA POWER range live once per session, so the landing page is
# never blank. The shipped file is preferred; this only runs when it is absent.
if df is None and demo_is_default(city, variable) and not st.session_state.get("_demo_fetch_tried"):
    st.session_state["_demo_fetch_tried"] = True
    try:
        with st.spinner("Loading the Lahore demo dataset (NASA POWER, 2015–2025)…"):
            df_new, metadata = retrieve_climate_data(city, REGIONS[city]["latitude"], REGIONS[city]["longitude"], "20150101", "20251231", variable)
            save_city_data(df_new, metadata, "lahore_t2m")
            st.session_state.frames[(city, variable)] = df_new
            df = df_new
            demo_dataset = True
    except Exception:
        pass  # designed empty state below handles it; never crash first load

# ---------- Live data (real, cached by the src modules) ----------
lat, lon = REGIONS[city]["latitude"], REGIONS[city]["longitude"]
if _geo and _geo.get("city") == city:
    # Live weather/AQI use the exact detected position, not the city centre.
    # Climate history (NASA POWER) still uses the matched catalogue city.
    lat, lon = _geo["latitude"], _geo["longitude"]
with st.spinner("Loading live weather and air quality…"):
    weather = safe(lambda: get_current_conditions(lat, lon, city), "Current conditions")
    forecast = safe(lambda: get_weather_forecast(lat, lon), "7-day forecast")
    aqi = safe(lambda: get_air_quality(lat, lon, city), "Air quality")
if st.session_state.pop("just_refreshed", False):
    st.toast("Live weather / AQI refreshed", icon="🌍")

# ---------- Computed climate context ----------
spec = VARIABLES[variable]
analysis_unit = "mm/month" if variable == "PRECTOTCORR" else spec["unit"]
monthly = trend = anomaly_df = latest_anomaly = risk = proj_df = proj_note = None
meta = None
if df is not None:
    try:
        meta = coverage_summary(df, variable)
        monthly = monthly_aggregate(df, variable)
        trend = analyze_trend(monthly, variable)
        anomaly_df = seasonal_anomalies(monthly, variable)
        if anomaly_df is not None and not anomaly_df.empty:
            latest_anomaly = float(anomaly_df.dropna(subset=["anomaly"]).tail(1)["anomaly"].iloc[0]) if anomaly_df["anomaly"].notna().any() else None
        risk = compute_risk(monthly, variable, trend, latest_anomaly,
                            current_temp=weather.get("temperature_2m") if weather else None,
                            us_aqi=(aqi.get("current") or {}).get("us_aqi") if aqi else None)
        proj_df, proj_note = project_trend(monthly, variable, trend, years_ahead=10)
    except Exception as exc:
        st.error(f"Climate analysis failed for the loaded dataset: {exc}")
# Guard: if analysis failed, meta/monthly are None — treat as no usable
# dataset so no page crashes on meta['first_date'] etc.
if df is not None and meta is None:
    st.error("Climate analysis failed for the loaded dataset — showing the fetch prompt instead of a broken page.")
    df = None

forecast_summary = None
if forecast:
    try:
        d = forecast["daily"]; n = min(7, len(d.get("time", [])))
        parts = []
        for i in range(n):
            day = pd.to_datetime(d["time"][i]).strftime("%a %d %b")
            parts.append(f"{day}: {d['temperature_2m_max'][i]:.0f}°/{d['temperature_2m_min'][i]:.0f}°C, rain chance {d['precipitation_probability_max'][i]:.0f}%")
        forecast_summary = "; ".join(parts)
    except Exception:
        forecast_summary = None

assistant_ctx = {"city": city, "weather": weather, "air_quality": aqi, "trend": trend,
                 "variable_label": spec["label"], "unit": analysis_unit,
                 "latest_anomaly": latest_anomaly, "risk": risk, "forecast_summary": forecast_summary}

# Live ticker context (real values only; shared by Overview + Weather & Maps)
_ticker_ctx = {"city": city,
               "temperature": weather.get("temperature_2m") if weather else None,
               "condition": weather.get("condition_text") if weather else None,
               "us_aqi": aqi["current"].get("us_aqi") if aqi and isinstance(aqi.get("current"), dict) else None,
               "aqi_label": aqi.get("aqi_label") if aqi else None,
               "pm2_5": aqi["current"].get("pm2_5") if aqi and isinstance(aqi.get("current"), dict) else None,
               "provider_time": (weather.get("provider_time") if weather else None) or (aqi.get("provider_time") if aqi else None)}
_ticker_html = ticker_html(build_ticker_items(_ticker_ctx))

def plot_style(fig, height=360):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(7,20,34,.35)",
                      font=dict(family="DM Sans", color="#b7cbd9"), margin=dict(l=5, r=10, t=18, b=5),
                      height=height, hovermode="x unified",
                      xaxis=dict(showgrid=False, title=None), yaxis=dict(gridcolor="rgba(145,180,205,.12)"))
    return fig

# ================= OVERVIEW =================
if page == "Overview":
    _wx_code = weather.get("weather_code") if weather else None
    _wx_class = weather_animation_class(_wx_code)
    _ticker = _ticker_html
    _hero_now = hero_now_html(weather, aqi)
    st.markdown(f"""<section class="ew-hero ew-hero-anim {_wx_class}"><div class="ew-hero-left"><div class="ew-eyebrow">PAKISTAN · WEATHER & EARTH OBSERVATION · {city.upper()}</div>
    <div class="ew-title">Understand the planet.<br>Act on the evidence.</div>
    <div class="ew-sub">One workspace for live weather, real air quality, satellite evidence and long-term climate signals across Pakistan — with transparent sources and scientific context.</div>
    <div><span class="ew-chip">NASA EARTH DATA</span><span class="ew-chip">LIVE AIR QUALITY</span><span class="ew-chip">CLIMATE TRENDS</span><span class="ew-chip">RISK SCREENING</span></div></div>{_hero_now}</section>""", unsafe_allow_html=True)
    if _ticker:
        st.markdown(_ticker, unsafe_allow_html=True)
    else:
        st.info("Live ticker unavailable — live weather and air quality could not be loaded. Press **Refresh live weather / AQI** in the sidebar.")
    _updated = _ticker_ctx["provider_time"]
    st.markdown(f'<p class="ew-updated"><span class="live-dot"></span>LIVE · Updated {_updated if _updated else "—"} · Open-Meteo / CAMS model data, not station observations</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if weather and isinstance(weather.get("temperature_2m"), (int, float)):
            kpi("Air temperature", f"{weather['temperature_2m']:.1f} °C", f"{weather.get('condition_text','')} · Feels like {weather.get('apparent_temperature','—')} °C", delay_ms=0)
        else: kpi("Air temperature", "—", "Live weather unavailable — check connection and retry.", delay_ms=0)
    with c2:
        if aqi:
            cur = aqi["current"]
            kpi("US AQI", f"{cur.get('us_aqi','—'):.0f}" if isinstance(cur.get("us_aqi"), (int, float)) else "—", f"{aqi['aqi_label']} · PM2.5 {cur.get('pm2_5','—')} µg/m³", accent=aqi["aqi_colour"], delay_ms=80)
        else: kpi("US AQI", "—", "Air quality unavailable — check connection and retry.", delay_ms=80)
    with c3:
        if trend and trend.get("status") == "ok":
            _p = trend.get("p_value")
            kpi("Trend / decade", f"{trend['sen_slope_per_decade']:+.3g} {analysis_unit}", f"{spec['label']} · {trend['direction']} · p={_p:.3g}" if _p is not None else f"{spec['label']} · {trend['direction']} · p unavailable", delay_ms=160)
        else: kpi("Trend / decade", "—", "Fetch NASA POWER climate data in the sidebar to unlock the trend.", delay_ms=160)
    with c4:
        if risk and risk.get("composite") is not None:
            kpi("Risk screening", f"{risk['composite']}/100 · {risk['composite_label']}", "Screening only — not an official warning.", delay_ms=240)
        else: kpi("Risk screening", "—", "Needs climate data + live weather / AQI.", delay_ms=240)
    _adv = advisory_summary(weather, aqi, forecast)
    if _adv:
        _adv_bits = []
        if _adv["health_label"]:
            _adv_bits.append(f"<b style=\"color:{_adv['health_colour']}\">Today: {_adv['health_label']}</b>")
        if _adv["rain_label"]:
            _adv_bits.append(f"Rain this week: <b style=\"color:{_adv['rain_colour']}\">{_adv['rain_label']}</b> ({_adv['rain_total_mm']:.0f} mm)")
        st.markdown(f'<div class="card ew-live-card"><div class="ew-card-head"><b>📌 Today’s advisory</b><span>What today’s air, heat and rain mean for you — plain language, from live data</span></div><p style="color:#e8f1f5;font-size:.95rem;margin:12px 0 0">{" · ".join(_adv_bits) if _adv_bits else "Advisory unavailable right now."}</p></div>', unsafe_allow_html=True)
        if st.button("Open Daily Advisory →", key="adv_open", type="primary", use_container_width=True):
            st.session_state["_nav_target"] = "Daily Advisory"
            st.rerun()
    section("Live now", f"{city} · {REGIONS[city]['province']} · Model-based conditions, cached 15 min · Air quality cached 30 min")
    a, b = st.columns(2)
    with a:
        # ONE card: header + stats + source line all inside, no dead header box.
        if weather:
            _wstats = "".join([
                _stat("Humidity", _num(weather.get("relative_humidity_2m"), "{:.0f}%")),
                _stat("Wind", _num(weather.get("wind_speed_10m"), "{:.1f} km/h")),
                _stat("Precipitation", _num(weather.get("precipitation"), "{:.1f} mm")),
                _stat("Cloud cover", f"{weather.get('cloud_cover')}%" if weather.get("cloud_cover") is not None else "—"),
            ])
            _wfoot = html.escape(str(weather.get("condition_text", ""))) + f" · Provider time {html.escape(str(weather.get('provider_time')))} ({html.escape(str(weather.get('timezone')))}) · Source: {html.escape(str(weather.get('source')))}"
            st.markdown(f'<div class="card ew-live-card"><div class="ew-card-head"><b>Current conditions</b><span>Open-Meteo · model estimate, not a station observation</span></div><div class="ew-stats">{_wstats}</div><div class="ew-card-foot">{_wfoot}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card ew-live-card"><div class="ew-card-head"><b>Current conditions</b><span>Open-Meteo · model estimate, not a station observation</span></div><p style="color:#b0c2ce;font-size:.85rem;margin-top:12px">Current conditions could not be loaded. Check your connection and press <b>Refresh live weather / AQI</b> in the sidebar.</p></div>', unsafe_allow_html=True)
    with b:
        if aqi:
            cur = aqi["current"]
            _astats = "".join([
                _stat("PM2.5", f"{cur.get('pm2_5', '—')} µg/m³"),
                _stat("PM10", f"{cur.get('pm10', '—')} µg/m³"),
                _stat("Ozone", f"{cur.get('ozone', '—')} µg/m³"),
            ])
            st.markdown(f'<div class="card ew-live-card"><div class="ew-card-head"><b>Air quality snapshot — US AQI {html.escape(str(cur.get("us_aqi", "—")))} · {html.escape(str(aqi["aqi_label"]))}</b><span>Open-Meteo Air Quality (CAMS) · model estimate · Dominant pollutant: {html.escape(str(aqi["dominant_pollutant"]))}</span></div><p style="color:#e8f1f5;font-size:.85rem;margin:12px 0 0">{html.escape(str(aqi["aqi_advice"]))}</p><div class="ew-stats cols-3">{_astats}</div><div class="ew-card-foot">Provider time {html.escape(str(aqi.get("provider_time")))} ({html.escape(str(aqi.get("timezone")))}) · Source: {html.escape(str(aqi.get("source")))}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card ew-live-card"><div class="ew-card-head"><b>Air quality snapshot</b><span>Open-Meteo Air Quality (CAMS) · model estimate</span></div><p style="color:#b0c2ce;font-size:.85rem;margin-top:12px">Air quality could not be loaded. Check your connection and press <b>Refresh live weather / AQI</b> in the sidebar.</p></div>', unsafe_allow_html=True)
    if df is None:
        section("Your climate workspace", "Three steps to your first trend")
        x1, x2, x3 = st.columns(3)
        with x1: kpi("01 · Select", "Choose a city", "101 mapped urban centres across Pakistan.")
        with x2: kpi("02 · Retrieve", "Connect to NASA", "Fetch daily historical climate estimates.")
        with x3: kpi("03 · Discover", "Read the signal", "Trends, anomalies and risk screening.")
        empty_state("No climate dataset loaded yet",
                    "Pick a city and indicator in the left panel, set the analysis period, and fetch it from NASA POWER — or use the button below to fetch it right now. The Lahore demo dataset (T2M 2015–2025) loads automatically on the default view.",
                    ["1 · Select a city and indicator in the sidebar", "2 · Press the button below — or Retrieve climate data in the sidebar", "3 · The trend, risk score and charts appear on this page"])
        if st.button(f"Fetch {city} climate data now", type="primary", use_container_width=True):
            if fetch_current_dataset():
                st.rerun()
    else:
        section(f"{city} / {spec['label']}", f"Monthly analysis · {analysis_unit} · {meta['first_date']} to {meta['last_date']} · Coverage {meta['coverage_pct']}%")
        if demo_dataset:
            st.caption("Demo dataset: Lahore T2M 2015–2025 · NASA POWER (included file) — press Retrieve climate data in the sidebar to fetch a different city, indicator or period.")
        fig = px.area(monthly, x="date", y=variable, labels={"date": "Month", variable: f"{spec['label']} ({analysis_unit})"})
        fig.update_traces(line=dict(color="#6ce7f4", width=2.5), fillcolor="rgba(74,196,224,.12)", hovertemplate="%{x|%b %Y}<br>%{y:.2f}<extra></extra>")
        st.plotly_chart(plot_style(fig, 380), use_container_width=True, config={"displaylogo": False, "responsive": True})
        st.caption("Monthly precipitation is summed; other indicators are monthly means. Source: NASA POWER.")
    st.markdown('<div class="ew-foot">EARTHWISE AI · PAKISTAN-FIRST EARTH INTELLIGENCE<br><strong>Created by Muhammad Abbubakar</strong> · Founder<br>Historical research and data exploration · Not an emergency monitoring service</div>', unsafe_allow_html=True)

# ================= CLIMATE ANALYTICS =================
elif page == "Climate Analytics":
    section(f"Climate Analytics — {city}", f"{spec['label']} · {analysis_unit} · NASA POWER daily point data, aggregated monthly")
    if df is None:
        empty_state("No climate dataset loaded yet",
                    "This page needs a historical dataset. It loads automatically for the Lahore T2M demo — for any other city or indicator, fetch it live from NASA POWER.",
                    ["1 · Choose the city, indicator and period in the sidebar", f"2 · Press the button below to fetch {city} now", "3 · Coverage, trend, anomalies and the AI Earth Scientist appear here"])
        if st.button(f"Fetch {city} climate data now", type="primary", use_container_width=True):
            if fetch_current_dataset():
                st.rerun()
        st.stop()
    if demo_dataset:
        st.caption("Demo dataset: Lahore T2M 2015–2025 · NASA POWER (included file) — press Retrieve climate data in the sidebar to fetch a different city, indicator or period.")
    m1, m2, m3, m4 = st.columns(4)
    with m1: kpi("Data coverage", f"{meta['coverage_pct']}%", f"{meta['valid_rows']:,} valid daily records")
    with m2: kpi("Monthly observations", f"{len(monthly):,}", f"{meta['first_date']} → {meta['last_date']}")
    with m3:
        if trend and trend.get("status") == "ok": kpi("Sen slope / decade", f"{trend['sen_slope_per_decade']:+.4g} {analysis_unit}", f"Direction: {trend['direction']}")
        else: kpi("Sen slope / decade", "—", "Insufficient data")
    with m4:
        if trend and trend.get("status") == "ok": kpi("Kendall p-value", f"{trend['p_value']:.4g}" if trend.get("p_value") is not None else "Unavailable", "Significant at 0.05" if trend.get("significant_005") else "Not significant at 0.05")
        else: kpi("Kendall p-value", "—", trend.get("message", "") if trend else "")
    t1, t2, t3 = st.tabs(["📈  Time series", "🌡️  Seasonal anomalies", "🧠  AI Earth Scientist"])
    with t1:
        fig = px.area(monthly, x="date", y=variable, labels={"date": "Month", variable: f"{spec['label']} ({analysis_unit})"})
        fig.update_traces(line=dict(color="#6ce7f4", width=2.5), fillcolor="rgba(74,196,224,.12)")
        st.plotly_chart(plot_style(fig, 400), use_container_width=True, config={"displaylogo": False})
        # 12-month rolling mean
        roll = monthly.copy(); roll["rolling_12m"] = roll[variable].rolling(12, min_periods=6).mean()
        fig2 = px.line(roll.dropna(subset=["rolling_12m"]), x="date", y="rolling_12m", labels={"date": "Month", "rolling_12m": f"12-month mean ({analysis_unit})"})
        fig2.update_traces(line=dict(color="#ffd36a", width=2.5))
        st.plotly_chart(plot_style(fig2, 300), use_container_width=True, config={"displaylogo": False})
        st.caption("Top: monthly values. Bottom: 12-month rolling mean — smoother long-term signal. Monthly precipitation is summed; other indicators are monthly means.")
    with t2:
        if anomaly_df is not None and not anomaly_df.empty:
            if latest_anomaly is not None: st.metric("Latest monthly departure from seasonal mean", f"{latest_anomaly:+.2f} {analysis_unit}")
            view = anomaly_df.tail(60)
            afig = px.bar(view, x="date", y="anomaly", color="anomaly", color_continuous_scale="RdBu_r", color_continuous_midpoint=0, labels={"date": "Month", "anomaly": f"Departure ({analysis_unit})"})
            afig.add_hline(y=0, line_dash="dot", line_color="#9bb5c9", opacity=.7)
            st.plotly_chart(plot_style(afig, 340), use_container_width=True, config={"displaylogo": False})
            st.caption("Baseline: each calendar month's mean across this selected dataset. This is a within-period seasonal departure, not a WMO 1991–2020 climate normal.")
            with st.expander("Inspect monthly anomaly values"):
                st.dataframe(anomaly_df.tail(36).round({variable: 3, "anomaly": 3, "climatology": 3, "standardized_anomaly": 3}), use_container_width=True, hide_index=True)
        else: st.info("Not enough monthly observations to calculate a seasonal baseline.")
    with t3:
        st.markdown('<div class="ew-ai"><b style="color:#7ee8d6;font-size:.65rem;letter-spacing:.14em">EARTHWISE INTELLIGENCE · ANALYSIS ENGINE</b><h3>AI Earth Scientist</h3><p style="color:#afc2cd;font-size:.8rem">An evidence-linked interpretation generated from the selected city\'s calculated climate statistics — not a free-form forecast.</p></div>', unsafe_allow_html=True)
        if trend and trend.get("status") == "ok":
            st.markdown(explain_result(city, spec["label"], analysis_unit, trend))
        else: st.warning(trend.get("message", "There is not enough data to calculate a reliable trend.") if trend else "No trend available.")
        with st.expander("Methodology and scientific limitations"):
            st.write("Trend method: Kendall tau significance test and Sen's slope. The simple trend test does not correct for monthly seasonality or serial autocorrelation. The AI explanation summarizes computed fields; it does not independently validate the dataset or establish causation.")
    # Compare cities — on demand, real fetches only
    section("Compare cities", "Same indicator, same period — real NASA POWER fetches, cached 24 h")
    compare = st.multiselect("Add cities to compare (max 3)", [c for c in sorted(REGIONS) if c != city], max_selections=3)
    compare_clicked = st.button("Compare selected cities", type="primary", use_container_width=True)
    if compare_clicked and not compare:
        st.warning("Select at least one city above first, then press **Compare selected cities**.")
    if compare_clicked and compare:
        frames = {}
        with st.spinner("Fetching comparison cities from NASA POWER…"):
            for cname in compare:
                try:
                    d2, _ = retrieve_climate_data(cname, REGIONS[cname]["latitude"], REGIONS[cname]["longitude"], f"{int(start_year)}0101", f"{int(end_year)}1231", variable)
                    frames[cname] = d2
                except Exception as exc: st.warning(f"{cname}: {exc}")
        if frames:
            rows = []
            for cname, d2 in frames.items():
                m2 = monthly_aggregate(d2, variable); r2 = analyze_trend(m2, variable)
                rows.append({"City": cname, "Direction": r2.get("direction", "—"), "Sen slope / decade": r2.get("sen_slope_per_decade"), "p-value": r2.get("p_value"), "Months": r2.get("n")})
            rows.insert(0, {"City": city, "Direction": trend.get("direction", "—") if trend else "—", "Sen slope / decade": trend.get("sen_slope_per_decade") if trend else None, "p-value": trend.get("p_value") if trend else None, "Months": trend.get("n") if trend else None})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.toast(f"Compared {len(frames)} cit{'y' if len(frames) == 1 else 'ies'} with {city}", icon="📊")
            st.caption("Sen's slope per decade, Kendall p-value. Interpret cautiously — no seasonality / autocorrelation correction in this MVP.")
        else:
            st.warning("No comparison data could be fetched — check your connection and try again.")

# ================= AIR QUALITY =================
elif page == "Air Quality":
    section(f"Air Quality — {city}", "Live CAMS model air quality via Open-Meteo Air Quality API · No key required · Not a station measurement")
    if not aqi:
        st.error("Air quality could not be loaded. Check your internet connection and press **Refresh live weather / AQI** in the sidebar.")
        st.stop()
    cur = aqi["current"]
    us_aqi = cur.get("us_aqi")
    g1, g2 = st.columns([1, 1])
    with g1:
        if isinstance(us_aqi, (int, float)):
            gauge = go.Figure(go.Indicator(mode="gauge+number", value=float(us_aqi), title={"text": f"US AQI — {aqi['aqi_label']}", "font": {"color": "#eef6f9", "size": 15}},
                gauge={"axis": {"range": [0, 300], "tickcolor": "#9db2c0"}, "bar": {"color": aqi["aqi_colour"]},
                       "steps": [{"range": [0, 50], "color": "#123527"}, {"range": [50, 100], "color": "#3d3410"}, {"range": [100, 150], "color": "#3d2210"}, {"range": [150, 200], "color": "#3d1215"}, {"range": [200, 300], "color": "#2c0f2e"}],
                       "threshold": {"line": {"color": "#fff", "width": 3}, "value": float(us_aqi)}}))
            gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#b7cbd9"), height=300, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(gauge, use_container_width=True, config={"displayModeBar": False})
        st.write(f"**{aqi['aqi_advice']}**")
        st.caption(f"Dominant pollutant: **{aqi['dominant_pollutant']}** · Provider time {aqi.get('provider_time')} ({aqi.get('timezone')}) · Source: {aqi.get('source')}")
    with g2:
        p1, p2 = st.columns(2)
        with p1: kpi("PM2.5", f"{cur.get('pm2_5','—')} µg/m³", "Fine particles · WHO guideline 5 µg/m³ (annual)")
        with p2: kpi("PM10", f"{cur.get('pm10','—')} µg/m³", "Coarse particles · WHO guideline 15 µg/m³ (annual)")
        p3, p4 = st.columns(2)
        with p3: kpi("Ozone (O₃)", f"{cur.get('ozone','—')} µg/m³", "Photochemical pollutant")
        with p4: kpi("Nitrogen dioxide", f"{cur.get('nitrogen_dioxide','—')} µg/m³", "Traffic / combustion marker")
        p5, p6 = st.columns(2)
        with p5: kpi("European AQI", f"{cur.get('european_aqi','—')}", "EU AQI scale")
        with p6: kpi("Carbon monoxide", f"{cur.get('carbon_monoxide','—')} µg/m³", "Combustion marker")
    # 24h PM2.5 / AQI chart
    hourly = aqi.get("hourly") or {}
    if hourly.get("time"):
        try:
            hdf = pd.DataFrame({"Time": pd.to_datetime(hourly["time"]), "PM2.5 (µg/m³)": hourly.get("pm2_5"), "US AQI": hourly.get("us_aqi")}).dropna(subset=["Time"])
            hdf = hdf[hdf["Time"] <= pd.to_datetime(hdf["Time"].iloc[0]) + pd.Timedelta(hours=24)]
            fig = px.line(hdf, x="Time", y="PM2.5 (µg/m³)", labels={"Time": "Local time"})
            fig.update_traces(line=dict(color="#e5484d", width=2.5))
            st.plotly_chart(plot_style(fig, 300), use_container_width=True, config={"displaylogo": False})
            st.caption("Next 24 hours of modelled PM2.5 (CAMS via Open-Meteo). Values are model estimates and can change with new model runs.")
        except Exception as exc: st.warning(f"Hourly air-quality chart unavailable: {exc}")
    st.markdown("**US AQI bands** — 0–50 Good · 51–100 Moderate · 101–150 Unhealthy for Sensitive Groups · 151–200 Unhealthy · 201–300 Very Unhealthy · 301+ Hazardous")
    st.caption("Health advice is generic US EPA band guidance, not medical advice. For official air-quality warnings, consult local authorities.")

# ================= WEATHER & MAPS =================
elif page == "Weather & Maps":
    section(f"Weather & Maps — {city}", "Model forecast for planning · Not an official PMD warning or emergency alert")
    if _ticker_html:
        st.markdown(_ticker_html, unsafe_allow_html=True)
    if forecast and isinstance(forecast.get("daily"), dict) and forecast["daily"].get("time"):
        daily = forecast["daily"]
        # One clean 7-day strip (7 cols desktop / 4 tablet / 2 mobile) — no
        # fractured 4+3 rows, no content wedged in between.
        _fc = forecast_cards_html(daily)
        if _fc:
            st.markdown("**7-day forecast**")
            st.markdown(_fc, unsafe_allow_html=True)
        else:
            st.info("7-day forecast details are unavailable.")
        hourly = forecast.get("hourly") or {}
        try:
            hdf = pd.DataFrame({"Time": pd.to_datetime(hourly.get("time", [])), "Temperature (°C)": hourly.get("temperature_2m", [])}).dropna()
            if hdf.empty:
                raise ValueError("No hourly temperature values were returned.")
            hfig = px.line(hdf, x="Time", y="Temperature (°C)")
            hfig.update_traces(line=dict(color="#66e3f2", width=2.7), hovertemplate="%{x|%a %H:%M}<br>%{y:.1f} °C<extra></extra>")
            st.markdown("**Next 24 hours · Temperature outlook**")
            st.plotly_chart(plot_style(hfig, 280), use_container_width=True, config={"displayModeBar": False})
        except Exception as exc:
            st.info(f"Hourly temperature outlook is unavailable: {exc}")
        st.caption(f"Forecast provider: {forecast.get('source', 'Open-Meteo')} · Generated at {forecast.get('forecast_generated_at', '—')} ({forecast.get('timezone', '')}) · Forecasts can change as new model runs arrive.")
    else: st.warning("Forecast is temporarily unavailable.")
    section("Earth observation workspace", "National map · 3D globe · NASA satellite evidence")
    wtab, gtab, stab, ctab = st.tabs(["🌡️  National conditions", "🌐  Earth view", "🛰️  Satellite evidence", "📍  City directory"])
    with wtab:
        st.caption("Model-based current weather across the mapped Pakistan city directory · Select a layer to recolour the map")
        map_layer = st.selectbox("Weather layer", ["Temperature", "Apparent temperature", "Precipitation", "Humidity", "Wind speed"], key="national_weather_layer")
        region_records = tuple((n, i["latitude"], i["longitude"]) for n, i in REGIONS.items())
        national_records = safe(lambda: get_national_weather_snapshot(region_records), "Pakistan-wide weather map")
        if national_records:
            ndf = pd.DataFrame(national_records)
            ndf["province"] = ndf["city"].map(lambda nm: REGIONS.get(nm, {}).get("province", "Pakistan"))
            cols_map = {"Temperature": ("temperature", "Temperature (°C)"), "Apparent temperature": ("apparent_temperature", "Apparent temperature (°C)"), "Precipitation": ("precipitation", "Current precipitation (mm)"), "Humidity": ("humidity", "Relative humidity (%)"), "Wind speed": ("wind_speed", "Wind speed (km/h)")}
            lk, ll = cols_map[map_layer]; ndf[ll] = pd.to_numeric(ndf[lk], errors="coerce")
            mfig = px.scatter_geo(ndf.dropna(subset=[ll]), lat="latitude", lon="longitude", color=ll, hover_name="city", hover_data={"condition": True, "province": True, ll: ":.1f", "latitude": False, "longitude": False}, color_continuous_scale="Turbo", labels={ll: ll})
            sel = ndf[ndf["city"] == city]
            if not sel.empty: mfig.add_trace(go.Scattergeo(lat=sel["latitude"], lon=sel["longitude"], mode="markers", name="Selected city", marker=dict(size=13, color="#ffffff", symbol="star", line=dict(width=2, color="#10263b")), hovertemplate=f"<b>{city}</b><br>Selected location<extra></extra>"))
            mfig.update_geos(scope="asia", projection_type="natural earth", center={"lat": 29.5, "lon": 69.5}, lataxis_range=[23, 38], lonaxis_range=[60, 78], showland=True, landcolor="#10283b", showocean=True, oceancolor="#071522", showcountries=True, countrycolor="#31536b", showcoastlines=True, coastlinecolor="#31536b", showframe=False, bgcolor="rgba(0,0,0,0)")
            mfig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#b7cbd9", family="DM Sans"), margin=dict(l=0, r=0, t=8, b=0), height=520, legend=dict(orientation="h", y=1.05, x=0))
            st.plotly_chart(mfig, use_container_width=True, config={"displayModeBar": False})
            heat = ndf.dropna(subset=["apparent_temperature"]).sort_values("apparent_temperature", ascending=False).head(10)
            st.markdown("**Highest modelled apparent temperatures · screening, not an official heat alert**")
            if not heat.empty: st.dataframe(heat[["city", "province", "temperature", "apparent_temperature", "humidity"]].rename(columns={"city": "City", "province": "Region", "temperature": "Air °C", "apparent_temperature": "Apparent °C", "humidity": "Humidity %"}).round(1), use_container_width=True, hide_index=True)
            st.dataframe(ndf[["city", "condition", "temperature", "apparent_temperature", "humidity", "precipitation", "wind_speed"]].rename(columns={"city": "City", "condition": "Conditions", "temperature": "Temperature °C", "apparent_temperature": "Apparent °C", "humidity": "Humidity %", "precipitation": "Precipitation mm", "wind_speed": "Wind km/h"}), use_container_width=True, hide_index=True)
            st.download_button("↓ Download Pakistan city weather snapshot (CSV)", ndf.to_csv(index=False), "earthwise_pakistan_city_weather.csv", "text/csv", use_container_width=True)
        else:
            st.info("Pakistan-wide weather map could not be loaded — check your connection and press **Refresh live weather / AQI** in the sidebar.")
    with gtab:
        st.caption("Interactive textured Earth · City markers · Drag to rotate and scroll to zoom")
        render_earth_globe(city)
        st.caption("Earth texture is a visual basemap. City markers use approximate city-centre coordinates; this is not a live satellite video feed.")
    with stab:
        sat_col, op_col = st.columns([2, 1])
        with sat_col: evidence_layer = st.selectbox("Earth-observation layer", ["VIIRS true-colour imagery", "GPM IMERG precipitation"], key="earth_observation_layer")
        with op_col: raster_opacity = st.slider("Raster opacity", 0.25, 1.0, 0.82, 0.05, key="raster_opacity")
        imagery_date = st.date_input("Observation date", value=date.today() - timedelta(days=2), min_value=date(2012, 1, 1), max_value=date.today() - timedelta(days=1), help="Select a completed UTC day. Recent NASA imagery may not yet have been processed.")
        if evidence_layer == "GPM IMERG precipitation":
            layer_id, layer_name, attribution = "IMERG_Precipitation_Rate_30min", "GPM IMERG precipitation rate", "NASA GPM IMERG · NASA/GSFC"
            st.caption("NASA GPM IMERG satellite-derived precipitation visualisation. A raster evidence layer, not a gauge measurement or flood forecast.")
        else:
            layer_id, layer_name, attribution = "VIIRS_SNPP_CorrectedReflectance_TrueColor", "VIIRS corrected reflectance true colour", "NASA/GSFC/ESDIS VIIRS Suomi-NPP"
            st.caption("NASA VIIRS Suomi-NPP corrected-reflectance true-colour daily composite. Cloud cover and acquisition gaps can obscure the surface.")
        render_nasa_satellite_map(imagery_date, layer_id, layer_name, attribution, raster_opacity)
        st.caption("Map tiles are served by NASA GIBS. The selected date is the imagery date, not necessarily the acquisition time of every pixel.")
    with ctab:
        mdf = pd.DataFrame([{"City": n, "Province": i["province"], "Latitude": i["latitude"], "Longitude": i["longitude"], "Selected": "Selected location" if n == city else "Other city"} for n, i in REGIONS.items()])
        cfig = px.scatter_geo(mdf, lat="Latitude", lon="Longitude", color="Selected", hover_name="City", hover_data={"Province": True, "Latitude": ':.3f', "Longitude": ':.3f', "Selected": False}, color_discrete_map={"Selected location": "#6ce7f4", "Other city": "#4d8dff"})
        cfig.update_geos(scope="asia", projection_type="natural earth", center={"lat": 29.5, "lon": 69.5}, lataxis_range=[23, 38], lonaxis_range=[60, 78], showland=True, landcolor="#10283b", showocean=True, oceancolor="#071522", showcountries=True, countrycolor="#31536b", showcoastlines=True, coastlinecolor="#31536b", showframe=False, bgcolor="rgba(0,0,0,0)")
        cfig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#a9c2d5", family="DM Sans"), margin=dict(l=0, r=0, t=8, b=0), height=390, legend=dict(orientation="h", y=1.05, x=0))
        st.plotly_chart(cfig, use_container_width=True, config={"displayModeBar": False})
        st.caption(f"Directory: {len(REGIONS)} mapped urban centres across Pakistan. Coordinates are approximate city-centre points.")

# ================= AI ASSISTANT =================
elif page == "AI Assistant":
    section("AI Environmental Assistant", f"Answers only from the real data loaded for {city} — live weather, AQI, trend, anomalies and risk. It will say when data is missing instead of guessing.")
    st.markdown('<div class="ew-ai"><b style="color:#7ee8d6;font-size:.65rem;letter-spacing:.14em">EARTHWISE INTELLIGENCE</b><h3>Ask about this city</h3><p style="color:#afc2cd;font-size:.8rem">Try: “What is the air quality?”, “What is the temperature trend?”, “Is there a risk?”, “What is the weather now?”</p></div>', unsafe_allow_html=True)
    if not st.session_state.chat:
        st.session_state.chat.append(("assistant", f"Hi — I'm EarthWise AI, answering only from the real data loaded for {city} right now: live weather, air quality, the climate trend, anomalies and the risk score. Ask me one of the questions below, or type your own. If the data isn't loaded, I'll say so instead of guessing."))
    # Fill the page: what it can answer + one real example answer, so the
    # chat input is never sitting under a large blank void.
    _cap1, _cap2 = st.columns(2)
    with _cap1:
        st.markdown('<div class="ew-assistant-cap"><b>What I can answer</b><ul><li>Current weather and the 7-day forecast</li><li>Live air quality (US AQI, PM2.5, dominant pollutant)</li><li>Temperature trend — direction, Sen slope, p-value</li><li>Seasonal anomalies and the risk screening score</li></ul></div>', unsafe_allow_html=True)
    with _cap2:
        _example = ""
        if aqi:
            try:
                _example = answer_question("What is the air quality?", assistant_ctx)
            except Exception:
                _example = ""
        if _example:
            _short = _example if len(_example) <= 240 else _example[:237].rsplit(" ", 1)[0] + "…"
            st.markdown(f'<div class="ew-assistant-cap"><b>Example — “What is the air quality?”</b><ul><li>{_answer_html(_short)}</li></ul></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="ew-assistant-cap"><b>Example — “What is the air quality?”</b><ul><li>Air quality is loading — press <b>Refresh live weather / AQI</b> in the sidebar and ask again.</li></ul></div>', unsafe_allow_html=True)
    sugg = st.columns(4)
    prompts = ["What is the air quality?", "What is the temperature trend?", "What is the weather now?", "Is there a risk?"]
    for col, p in zip(sugg, prompts):
        if col.button(p, use_container_width=True):
            st.session_state.chat.append(("user", p))
            st.session_state.chat.append(("assistant", answer_question(p, assistant_ctx)))
    q = st.chat_input("Ask about weather, air quality, trend, anomalies or risk…")
    if q:
        st.session_state.chat.append(("user", q))
        with st.spinner("Checking the loaded data…"):
            st.session_state.chat.append(("assistant", answer_question(q, assistant_ctx)))
    for role, text in st.session_state.chat[-12:]:
        cls = "chat-q" if role == "user" else "chat-a"
        who = "You" if role == "user" else "EarthWise AI"
        st.markdown(f'<div class="{cls}"><b>{who}</b><br>{_answer_html(text)}</div>', unsafe_allow_html=True)
    if st.button("Clear conversation"):
        st.session_state.chat = []; st.rerun()
    st.caption("Evidence-bound assistant: no LLM, no invented numbers. Every answer cites the dataset already loaded on this page. For official warnings use PMD / health authorities.")

# ================= RISK & OUTLOOK =================
elif page == "Risk & Outlook":
    section(f"Climate Risk & Outlook — {city}", "Transparent screening from real data · Straight-line Sen-slope projection, NOT a climate-model forecast")
    if df is None or trend is None or trend.get("status") != "ok":
        empty_state("Risk screening needs a climate dataset",
                    "Fetch NASA POWER data first (at least 24 monthly observations). Live weather and AQI already contribute when available — they are shown below as a partial screening.",
                    [f"1 · Press the button below to fetch {city} now", "2 · Or use Retrieve climate data in the sidebar", "3 · The composite score and 10-year outlook appear here"])
        if st.button(f"Fetch {city} climate data now", type="primary", use_container_width=True):
            if fetch_current_dataset():
                st.rerun()
        if risk and risk.get("composite") is not None:
            st.metric("Partial screening (live data only)", f"{risk['composite']}/100 · {risk['composite_label']}")
        st.stop()
    if risk is None:
        st.error("Risk screening could not be computed for this dataset — try fetching the climate data again.")
        st.stop()
    r1, r2, r3, r4 = st.columns(4)
    with r1: kpi("Composite screening", f"{risk['composite']}/100", risk["composite_label"], accent="#ffd36a")
    with r2: kpi("Trend signal", f"{risk['scores'].get('trend', 0):.0f}/100", risk["scores"].get("trend_label", "—"))
    with r3: kpi("Air-quality signal", f"{risk['scores'].get('air_quality', 0):.0f}/100" if risk["scores"].get("air_quality") is not None else "—", risk["scores"].get("air_quality_label", "—"))
    with r4: kpi("Current heat signal", f"{risk['scores'].get('heat_now', 0):.0f}/100" if risk["scores"].get("heat_now") is not None else "—", risk["scores"].get("heat_now_label", "—"))
    for note in risk.get("notes", []): st.caption(note)
    section("10-year outlook — Sen-slope extrapolation", proj_note or "")
    if proj_df is not None and not proj_df.empty:
        pfig = go.Figure()
        hist = monthly.tail(60)
        pfig.add_trace(go.Scatter(x=hist["date"], y=hist[variable], mode="lines", name="Observed (last 60 months)", line=dict(color="#6ce7f4", width=2)))
        pfig.add_trace(go.Scatter(x=proj_df["date"], y=proj_df["projected"], mode="lines+markers", name="Projected (Sen slope)", line=dict(color="#ffd36a", width=2.5, dash="dash")))
        pfig.add_trace(go.Scatter(x=proj_df["date"], y=proj_df["high_95"], mode="lines", line=dict(width=0), showlegend=False))
        pfig.add_trace(go.Scatter(x=proj_df["date"], y=proj_df["low_95"], mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(255,211,106,.15)", name="95% slope CI"))
        st.plotly_chart(plot_style(pfig, 380), use_container_width=True, config={"displaylogo": False})
        st.dataframe(proj_df.round({"projected": 3, "low_95": 3, "high_95": 3}), use_container_width=True, hide_index=True)
        st.download_button("↓ Download 10-year projection (CSV)", proj_df.to_csv(index=False), f"{city.lower().replace(' ','_')}_{variable.lower()}_10y_projection.csv", "text/csv", use_container_width=True)
    st.warning("⚠️ This outlook is a straight-line extrapolation of the historical Sen's slope. It is NOT a climate-model projection, weather forecast or disaster prediction. Do not use it for emergency planning — use PMD and official climate projections.")
    with st.expander("How the risk score is built"):
        st.write("- **Trend signal:** |Sen's slope per decade| scaled (2 °C/decade or 100 mm/decade ≈ high). From NASA POWER monthly data, Kendall p-value shown on the Analytics page.")
        st.write("- **Anomaly signal:** latest same-calendar-month departure.")
        st.write("- **Heat now:** live model temperature bands (30 / 35 / 40 / 45 °C).")
        st.write("- **Air quality:** live US AQI / 3, from CAMS via Open-Meteo.")
        st.write("- **Composite:** mean of the available signals. Screening only.")

# ================= DAILY ADVISORY =================
elif page == "Daily Advisory":
    section(f"Daily Advisory — {city}", "Three plain-language advisories from today's live data · What the numbers mean for your health, your fields and your travel")
    _health = daily_health_verdict(weather, aqi)
    if _health.get("status") == "ok":
        _factors = " · ".join(_health["factors"]) if _health["factors"] else "—"
        _actions = "".join(f"<li>{html.escape(a)}</li>" for a in _health["actions"])
        st.markdown(f'<div class="card ew-live-card"><div class="ew-card-head"><b>🏥 Today’s health verdict — {html.escape(_health["label"])}</b><span>Score {_health["score"]}/10 · From live AQI, heat and humidity</span></div><p style="color:#e8f1f5;font-size:.95rem;margin:12px 0 0">{html.escape(_factors)}</p><ul style="color:#e8f1f5">{_actions}</ul></div>', unsafe_allow_html=True)
        st.caption("General guidance only — not medical advice. If you feel unwell, seek medical help.")
    else:
        st.info("Health verdict unavailable — live weather and air quality could not be loaded. Press **Refresh live weather / AQI** in the sidebar.")
    _farm = farmer_advisory(forecast)
    if _farm.get("status") == "ok":
        _farm_items = "".join(f"<li><b>{html.escape(it['title'])}</b> — {html.escape(it['detail'])}</li>" for it in _farm["items"])
        st.markdown(f'<div class="card ew-live-card"><div class="ew-card-head"><b>🌾 Farmer advisory</b><span>{html.escape(_farm["summary"])}</span></div><ul style="color:#e8f1f5">{_farm_items}</ul></div>', unsafe_allow_html=True)
        st.caption("General planning guidance from the 7-day model forecast — confirm with your local agriculture department for crop-specific decisions.")
    else:
        st.info("Farmer advisory unavailable — the 7-day forecast could not be loaded. Press **Refresh live weather / AQI** in the sidebar.")
    _rain = rain_warning(forecast)
    if _rain.get("status") == "ok":
        _rain_days = "".join(
            "<li>" + d["date"] + ": "
            + (f"{d['rain_mm']:.0f}" if d["rain_mm"] is not None else "—")
            + " mm — " + d["label"] + "</li>"
            for d in _rain["days"])
        st.markdown(f'<div class="card ew-live-card"><div class="ew-card-head"><b>🌧️ Rain warning — {html.escape(_rain["label"])}</b><span>{_rain["total_mm"]:.0f} mm expected this week · Worst day {_rain["worst_day"]} ({_rain["worst_mm"]:.0f} mm)</span></div><p style="color:#e8f1f5;font-size:.95rem;margin:12px 0 0">{html.escape(_rain["advice"])}</p><ul style="color:#e8f1f5">{_rain_days}</ul></div>', unsafe_allow_html=True)
        st.caption("Model forecast screening, not an official warning — Pakistan Meteorological Department (PMD) issues official warnings.")
    else:
        st.info("Rain warning unavailable — the 7-day forecast could not be loaded. Press **Refresh live weather / AQI** in the sidebar.")
    st.markdown('<div class="ew-foot">EARTHWISE AI · PAKISTAN-FIRST EARTH INTELLIGENCE<br><strong>Created by Muhammad Abbubakar</strong> · Founder<br>Advisories are screening guidance from model data, not official warnings</div>', unsafe_allow_html=True)

# ================= DATA & DOWNLOADS =================
elif page == "Data & Downloads":
    section("Data & Downloads", "Every file below comes from a real API response — raw NASA POWER CSV + metadata are saved on fetch")
    if df is None:
        empty_state("No climate dataset loaded yet",
                    "Fetch a dataset and the monthly table, CSV downloads and data provenance appear here. The Lahore T2M demo (2015–2025) loads automatically on the default view.",
                    [f"1 · Press the button below to fetch {city} now", "2 · Or use Retrieve climate data in the sidebar", "3 · Monthly data, anomalies and the projection become downloadable"])
        if st.button(f"Fetch {city} climate data now", type="primary", use_container_width=True):
            if fetch_current_dataset():
                st.rerun()
    else:
        st.markdown(f"**{city} · {spec['label']}** · {meta['first_date']} to {meta['last_date']} · Coverage {meta['coverage_pct']}% · {meta['valid_rows']:,} valid daily records")
        st.dataframe(monthly, use_container_width=True, hide_index=True)
        d1, d2, d3 = st.columns(3)
        with d1: st.download_button("↓ Monthly data (CSV)", monthly.to_csv(index=False), f"{city.lower().replace(' ','_')}_{variable.lower()}_monthly.csv", "text/csv", use_container_width=True)
        with d2:
            if anomaly_df is not None: st.download_button("↓ Seasonal anomalies (CSV)", anomaly_df.to_csv(index=False), f"{city.lower().replace(' ','_')}_{variable.lower()}_seasonal_anomalies.csv", "text/csv", use_container_width=True)
            else: st.caption("Seasonal anomalies unavailable — not enough monthly data.")
        with d3:
            if proj_df is not None and not proj_df.empty: st.download_button("↓ 10-year projection (CSV)", proj_df.to_csv(index=False), f"{city.lower().replace(' ','_')}_{variable.lower()}_10y_projection.csv", "text/csv", use_container_width=True)
            else: st.caption("10-year projection unavailable — needs a valid trend.")
        with st.expander("Data provenance & coordinates"):
            st.write("**Source:** NASA POWER Daily Point API"); st.write("**Coordinates:**", REGIONS[city])
            st.write("**Requested period:**", meta["first_date"], "to", meta["last_date"]); st.write("**NASA POWER parameter:**", variable)
            st.write("**Aggregation:**", "Monthly sum of daily values" if spec["aggregation"] == "sum" else "Monthly mean of daily values")
            st.markdown("[NASA POWER API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)")
    section("APIs & configuration", "What this app calls — and what you need (or don't need) to run it")
    st.markdown("""
| Service | Purpose | Key needed? |
|---|---|---|
| NASA POWER Daily API | Historical climate (T2M, rain, humidity, wind, solar) | No — free, no key |
| Open-Meteo Forecast API | Current weather + 7-day forecast | No for evaluation · `OPEN_METEO_API_KEY` for commercial use |
| Open-Meteo Air Quality API (CAMS) | Live AQI, PM2.5/PM10, O₃, NO₂ | No — free, no key |
| NASA GIBS WMTS | VIIRS true-colour + GPM IMERG satellite tiles | No — free, no key |
| Globe.gl / Leaflet (CDN) | 3D globe + satellite map rendering | No |
""")
    st.caption("No database is used — the original design stores raw NASA POWER CSV + JSON metadata in `data/raw/` (git-ignored). No user accounts, passwords or secrets are stored in this repo. Never commit `.env` or Streamlit secrets.")
    st.markdown('<div class="ew-foot">EARTHWISE AI · PAKISTAN-FIRST EARTH INTELLIGENCE<br><strong>Created by Muhammad Abbubakar</strong> · Founder</div>', unsafe_allow_html=True)

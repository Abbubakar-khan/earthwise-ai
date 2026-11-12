from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.regions import REGIONS, VARIABLES
from src.nasa_power import fetch_daily, save_city_data
from src.cleaning import monthly_aggregate, coverage_summary
from src.statistics import analyze_trend
from src.ai_engine import explain_result

st.set_page_config(
    page_title="EARTHWISE AI | Pakistan Earth Explorer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Lightweight CSS motion: subtle ambient glow, entrance transitions, and responsive controls.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    :root { --ew-bg:#07111f; --ew-panel:#0d1b2b; --ew-line:rgba(148,190,220,.16); --ew-cyan:#57d5ed; --ew-blue:#4d8dff; --ew-muted:#91a8bd; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    .stApp { background: radial-gradient(ellipse at 82% 0%, rgba(25,105,160,.20), transparent 34%), linear-gradient(145deg,#06101d 0%,#091827 48%,#07111f 100%); color:#edf6ff; }
    [data-testid="stHeader"] { background:rgba(5,14,25,.72); backdrop-filter:blur(14px); }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#0a1929,#071321); border-right:1px solid var(--ew-line); }
    [data-testid="stSidebar"] * { color:#e8f2fb; }
    h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.035em; }
    h1 { font-weight:700 !important; }
    .block-container { padding-top:2.1rem; padding-bottom:3rem; max-width:1440px; animation:fadeUp .65s ease both; }
    @keyframes fadeUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
    @keyframes breathe { 0%,100% { box-shadow:0 0 0 0 rgba(87,213,237,.18); } 50% { box-shadow:0 0 0 7px rgba(87,213,237,0); } }
    .ew-hero { position:relative; overflow:hidden; padding:30px 32px; border:1px solid rgba(112,190,224,.24); border-radius:22px; background:linear-gradient(115deg,rgba(16,47,70,.94),rgba(10,27,45,.88) 58%,rgba(12,37,60,.92)); margin-bottom:22px; }
    .ew-hero:after { content:''; position:absolute; width:290px;height:290px;right:-65px;top:-150px;border-radius:50%;background:radial-gradient(circle,rgba(74,185,226,.22),transparent 68%);pointer-events:none; }
    .ew-eyebrow { color:#72d9ef; font-size:.72rem; font-weight:700; letter-spacing:.19em; text-transform:uppercase; }
    .ew-title { font-family:'Space Grotesk',sans-serif; font-size:clamp(2rem,4vw,3.25rem); line-height:1.04; font-weight:700; color:#f5fbff; margin:10px 0 9px; letter-spacing:-.055em; }
    .ew-sub { color:#b3c9dc; font-size:1rem; max-width:720px; line-height:1.65; }
    .ew-status { display:inline-flex; align-items:center; gap:9px; border:1px solid rgba(87,213,237,.25); background:rgba(12,45,63,.72); color:#bceefa; padding:8px 12px; border-radius:99px; font-size:.75rem; font-weight:600; margin-top:19px; }
    .ew-dot { width:7px;height:7px;border-radius:50%;background:#57d5ed;animation:breathe 2s infinite; }
    .ew-section { color:#eaf5ff; font-family:'Space Grotesk',sans-serif; font-size:1.22rem; font-weight:600; margin:1.1rem 0 .65rem; }
    .ew-card { background:linear-gradient(145deg,rgba(17,38,58,.94),rgba(10,25,41,.94)); border:1px solid var(--ew-line); border-radius:16px; padding:17px 18px; min-height:112px; transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease; }
    .ew-card:hover { transform:translateY(-3px); border-color:rgba(87,213,237,.42); box-shadow:0 12px 28px rgba(0,0,0,.16); }
    .ew-kicker { color:#91a8bd; font-size:.72rem; text-transform:uppercase; letter-spacing:.12em; font-weight:700; }
    .ew-value { color:#f1f8ff; font-family:'Space Grotesk',sans-serif; font-size:1.65rem; font-weight:700; margin-top:9px; }
    .ew-note { color:#9db3c7; font-size:.78rem; margin-top:4px; }
    div.stButton > button, div.stDownloadButton > button { border-radius:11px; border:1px solid rgba(87,213,237,.35); background:linear-gradient(100deg,#167da0,#2365b6); color:white; font-weight:700; min-height:2.8rem; transition:all .2s ease; }
    div.stButton > button:hover, div.stDownloadButton > button:hover { transform:translateY(-2px); border-color:#8cecff; box-shadow:0 8px 22px rgba(28,145,190,.22); color:white; }
    div[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(17,38,58,.94),rgba(10,25,41,.94)); border:1px solid var(--ew-line); border-radius:15px; padding:15px 17px; }
    div[data-testid="stMetricLabel"] { color:#9eb5c9; }
    div[data-testid="stMetricValue"] { color:#f1f8ff; font-family:'Space Grotesk',sans-serif; }
    .stAlert { border-radius:13px; }
    [data-testid="stExpander"] { border:1px solid var(--ew-line); border-radius:13px; background:rgba(11,27,44,.62); }
    footer { visibility:hidden; }
    @media (max-width: 700px) { .block-container {padding:1rem .8rem 2rem;} .ew-hero {padding:23px 20px;} .ew-title {font-size:2.1rem;} }
    @media (prefers-reduced-motion: reduce) { *,*::before,*::after { animation-duration:.01ms !important; transition-duration:.01ms !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="ew-hero">
      <div class="ew-eyebrow">FORGE CYBER LAB &nbsp; / &nbsp; EARTH INTELLIGENCE</div>
      <div class="ew-title">Understand our planet.<br>See the patterns.</div>
      <div class="ew-sub">Explore historical climate signals across Pakistan with NASA POWER data, transparent statistics, and clear scientific context.</div>
      <div class="ew-status"><span class="ew-dot"></span> HISTORICAL DATA &nbsp;·&nbsp; ON-DEMAND RETRIEVAL</div>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 🌍 EARTHWISE AI")
    st.caption("PAKISTAN EARTH EXPLORER")
    st.divider()
    st.markdown("### Explore a location")
    city = st.selectbox("City", list(REGIONS))
    variable = st.selectbox(
        "Climate indicator",
        list(VARIABLES),
        format_func=lambda key: f"{VARIABLES[key]['label']} ({VARIABLES[key]['unit']})",
    )
    st.markdown("### Analysis period")
    start_year = st.number_input("Start year", min_value=1981, max_value=2026, value=2001)
    end_year = st.number_input("End year", min_value=int(start_year), max_value=2026, value=2025)
    fetch = st.button("↗  Retrieve NASA POWER data", type="primary", use_container_width=True)
    st.divider()
    st.caption("Source: NASA POWER Daily Point API")
    st.caption("Historical estimates only. Recent records may be incomplete.")

if "frames" not in st.session_state:
    st.session_state.frames = {}

if fetch:
    coords = REGIONS[city]
    with st.spinner("Connecting to NASA POWER and retrieving climate records…"):
        try:
            df, metadata = fetch_daily(
                city,
                coords["latitude"],
                coords["longitude"],
                f"{int(start_year)}0101",
                f"{int(end_year)}1231",
                parameters=(variable,),
            )
            slug = f"{city.lower().replace(' ', '_')}_{variable.lower()}"
            csv_path, meta_path = save_city_data(df, metadata, slug)
            st.session_state.frames[(city, variable)] = df
            st.success(f"Successfully retrieved and saved the dataset for {city}.")
            st.caption(f"Local data file: {csv_path} · Metadata: {meta_path}")
        except Exception as exc:
            st.error(f"NASA POWER request failed: {exc}")

df = st.session_state.frames.get((city, variable))
if df is None:
    candidate = Path("data/raw") / f"{city.lower().replace(' ', '_')}_{variable.lower()}_nasa_power_daily.csv"
    if candidate.exists():
        cached = pd.read_csv(candidate, parse_dates=["date"])
        if variable in cached.columns:
            df = cached

if df is None:
    st.markdown('<div class="ew-section">Your climate workspace</div>', unsafe_allow_html=True)
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown(
            """
            <div class="ew-card">
              <div class="ew-kicker">01 / Select your signal</div>
              <div class="ew-value">Choose a city & indicator</div>
              <div class="ew-note">Use the controls in the left panel to define your research area.</div>
            </div><br>
            <div class="ew-card">
              <div class="ew-kicker">02 / Retrieve trusted data</div>
              <div class="ew-value">Connect to NASA POWER</div>
              <div class="ew-note">Request historical daily estimates for your selected date range.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div class="ew-card">
              <div class="ew-kicker">03 / Explore the evidence</div>
              <div class="ew-value">Turn data into insight</div>
              <div class="ew-note">Review monthly patterns, data coverage, trend statistics, and an evidence-bound AI explanation.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.info("Select a city, choose a climate indicator and date range, then retrieve the dataset to begin.")
    st.caption("Scientific note: NASA POWER provides gridded satellite/model-assisted estimates, not local weather-station observations. This research prototype does not provide forecasts or disaster predictions.")
    st.stop()

meta = coverage_summary(df, variable)
monthly = monthly_aggregate(df, variable)
result = analyze_trend(monthly, variable)
spec = VARIABLES[variable]

st.markdown(f'<div class="ew-section">{city} <span style="color:#7fdcf0">/</span> {spec["label"]}</div>', unsafe_allow_html=True)
st.caption(f"Monthly analysis · {spec['unit']} · {meta['first_date']} to {meta['last_date']}")

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Data coverage", f"{meta['coverage_pct']}%")
with m2:
    st.metric("Valid daily records", f"{meta['valid_rows']:,}")
with m3:
    st.metric("Monthly observations", f"{len(monthly):,}")

st.markdown('<div class="ew-section">Climate signal over time</div>', unsafe_allow_html=True)
fig = px.line(
    monthly,
    x="date",
    y=variable,
    labels={"date": "Month", variable: f"{spec['label']} ({spec['unit']})"},
    template="plotly_dark",
)
fig.update_traces(line=dict(color="#57d5ed", width=2.6), fill="tozeroy", fillcolor="rgba(87,213,237,0.08)")
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(8,22,37,0.45)",
    font=dict(family="DM Sans, sans-serif", color="#b8cadd"),
    margin=dict(l=10, r=15, t=20, b=10),
    hovermode="x unified",
    xaxis=dict(showgrid=False, zeroline=False, title=None),
    yaxis=dict(gridcolor="rgba(145,180,205,.12)", zeroline=False),
    legend=dict(orientation="h"),
)
st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "responsive": True})

st.markdown('<div class="ew-section">Statistical trend assessment</div>', unsafe_allow_html=True)
if result.get("status") == "ok":
    a, b, c, d = st.columns(4)
    a.metric("Long-term direction", result["direction"].title())
    b.metric("Sen slope / decade", f"{result['sen_slope_per_decade']:.4g} {spec['unit']}")
    p_value = result.get("p_value")
    c.metric("Kendall p-value", f"{p_value:.4g}" if p_value is not None else "Unavailable")
    d.metric("Significant at 0.05", "Yes" if result["significant_005"] else "No")
    st.markdown("#### AI Earth Scientist")
    st.markdown(explain_result(city, spec["label"], spec["unit"], result))
else:
    st.warning(result.get("message", "There is not enough data to calculate a reliable trend."))

with st.expander("Data provenance, methodology & limitations"):
    st.write("**Source:** NASA POWER Daily Point API")
    st.write("**Requested period:**", meta["first_date"], "to", meta["last_date"])
    st.write("**NASA POWER parameter:**", variable)
    aggregation = "Monthly sum of daily values" if spec["aggregation"] == "sum" else "Monthly mean of daily values"
    st.write("**Aggregation:**", aggregation)
    st.write("**Trend method:** Kendall tau significance + Sen's slope.")
    st.write("**Scientific caveat:** This simple trend test does not correct for monthly seasonality or serial autocorrelation.")
    st.write("**Coordinates:**", REGIONS[city])
    st.markdown("[NASA POWER API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)")

st.download_button(
    "↓  Download monthly data (CSV)",
    monthly.to_csv(index=False),
    f"{city.lower()}_{variable}_monthly.csv",
    "text/csv",
    use_container_width=True,
)

st.divider()
st.caption("EARTHWISE AI · A Pakistan-first Earth intelligence research prototype · Powered by NASA POWER")

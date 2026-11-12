from pathlib import Path
import sys
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.regions import REGIONS, VARIABLES
from src.nasa_power import fetch_daily, save_city_data
from src.cleaning import monthly_aggregate, coverage_summary
from src.statistics import analyze_trend
from src.ai_engine import explain_result

st.set_page_config(
    page_title="EARTHWISE AI | Pakistan Earth Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium mission-control visual system. Motion is subtle and respects reduced-motion preferences.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root{--bg:#050b14;--panel:#0b1726;--line:rgba(133,181,211,.15);--cyan:#66e3f2;--blue:#5798ff;--muted:#8da7bd;--white:#edf7ff}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:radial-gradient(ellipse at 82% -5%,rgba(24,113,163,.22),transparent 35%),radial-gradient(ellipse at 5% 38%,rgba(22,67,105,.12),transparent 35%),linear-gradient(145deg,#040a12,#081625 58%,#050d18);color:var(--white)}
[data-testid="stHeader"]{background:rgba(4,11,20,.72);backdrop-filter:blur(18px)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1a2a,#07111e);border-right:1px solid var(--line)}
[data-testid="stSidebar"] *{color:#e7f3fc}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.035em}
.block-container{max-width:1500px;padding-top:1.4rem;padding-bottom:3rem;animation:rise .7s cubic-bezier(.2,.7,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
@keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(102,227,242,.35)}50%{opacity:.72;box-shadow:0 0 0 7px rgba(102,227,242,0)}}
@keyframes orbit{from{transform:rotate(0)}to{transform:rotate(360deg)}}
@keyframes scan{0%{transform:translateY(-120%)}100%{transform:translateY(260%)}}
.ew-top{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:15px}
.ew-brand{font:700 .82rem 'Space Grotesk';letter-spacing:.19em;color:#dff8ff}
.ew-brand span{color:var(--cyan)}
.ew-live{display:inline-flex;align-items:center;gap:8px;border:1px solid rgba(102,227,242,.22);background:rgba(16,57,73,.35);border-radius:99px;padding:7px 11px;color:#a9edf5;font-size:.68rem;letter-spacing:.12em;font-weight:700}
.ew-live i{width:7px;height:7px;background:#60e6ba;border-radius:50%;animation:pulse 1.8s infinite}
.ew-hero{position:relative;overflow:hidden;border:1px solid rgba(113,190,222,.22);border-radius:24px;padding:clamp(24px,4vw,42px);background:linear-gradient(112deg,rgba(12,38,59,.97),rgba(8,25,42,.93) 60%,rgba(9,35,55,.9));margin-bottom:20px;box-shadow:0 20px 60px rgba(0,0,0,.17)}
.ew-hero:before{content:'';position:absolute;right:-100px;top:-200px;width:460px;height:460px;border:1px solid rgba(102,227,242,.13);border-radius:50%;box-shadow:0 0 0 28px rgba(102,227,242,.025),0 0 0 58px rgba(102,227,242,.02),0 0 90px rgba(57,170,216,.13);animation:orbit 55s linear infinite;pointer-events:none}
.ew-hero:after{content:'';position:absolute;right:0;top:0;width:42%;height:100%;background:linear-gradient(180deg,transparent,rgba(90,210,235,.06),transparent);animation:scan 8s linear infinite;pointer-events:none}
.ew-eyebrow{position:relative;color:#78dff0;font-size:.68rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase}
.ew-title{position:relative;font:700 clamp(2.1rem,5vw,3.7rem)/1.02 'Space Grotesk';letter-spacing:-.065em;color:#f5fbff;margin:13px 0 12px;max-width:800px}
.ew-sub{position:relative;color:#afc7da;max-width:760px;line-height:1.7;font-size:.97rem}
.ew-hero-foot{position:relative;display:flex;gap:9px;flex-wrap:wrap;margin-top:22px}
.ew-chip{border:1px solid rgba(111,199,225,.2);background:rgba(7,27,43,.68);padding:7px 10px;border-radius:8px;color:#bdebf4;font-size:.68rem;letter-spacing:.08em}
.ew-section{font:600 1.15rem 'Space Grotesk';color:#eaf7ff;margin:1.35rem 0 .7rem}
.ew-muted{color:#91aabd;font-size:.8rem}
.ew-panel{border:1px solid var(--line);border-radius:16px;background:linear-gradient(145deg,rgba(14,34,52,.88),rgba(8,22,37,.9));padding:17px 18px}
.ew-panel-label{color:#91afc5;font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;font-weight:700}
.ew-panel-value{font:700 1.55rem 'Space Grotesk';color:#f1f9ff;margin-top:8px}
.ew-panel-note{color:#90aabe;font-size:.74rem;margin-top:4px}
div[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(14,34,52,.88),rgba(8,22,37,.9));border:1px solid var(--line);border-radius:15px;padding:14px 16px;transition:transform .2s,border-color .2s}
div[data-testid="stMetric"]:hover{transform:translateY(-2px);border-color:rgba(102,227,242,.35)}
div[data-testid="stMetricLabel"]{color:#9bb5c9}
div[data-testid="stMetricValue"]{color:#f3faff;font-family:'Space Grotesk',sans-serif}
div.stButton>button,div.stDownloadButton>button{border-radius:10px;border:1px solid rgba(102,227,242,.34);background:linear-gradient(105deg,#126d89,#245ba8);color:white;font-weight:700;min-height:2.75rem;transition:all .2s ease}
div.stButton>button:hover,div.stDownloadButton>button:hover{transform:translateY(-2px);border-color:#9aeeff;box-shadow:0 9px 24px rgba(31,142,186,.2);color:white}
.stSelectbox>div>div,.stNumberInput>div>div{background:rgba(7,20,34,.9);border-color:var(--line);border-radius:10px}
.stTabs [data-baseweb="tab-list"]{gap:8px;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{border-radius:9px 9px 0 0;color:#9bb5c9;padding:10px 15px}
.stTabs [aria-selected="true"]{color:#8ceafa!important}
[data-testid="stExpander"]{border:1px solid var(--line);border-radius:13px;background:rgba(9,25,41,.55)}
.stAlert{border-radius:12px}
footer{visibility:hidden}
@media(max-width:700px){.block-container{padding:1rem .8rem 2rem}.ew-title{font-size:2.15rem}.ew-hero{padding:23px 19px}.ew-top{align-items:flex-start;flex-direction:column}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important;scroll-behavior:auto!important}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ew-top">
  <div class="ew-brand">EARTHWISE <span>AI</span> &nbsp; / &nbsp; EARTH INTELLIGENCE</div>
  <div class="ew-live"><i></i> SYSTEM ONLINE &nbsp;·&nbsp; DATA ON DEMAND</div>
</div>
<section class="ew-hero">
  <div class="ew-eyebrow">PAKISTAN CLIMATE INTELLIGENCE PLATFORM</div>
  <div class="ew-title">See the signals.<br>Understand our planet.</div>
  <div class="ew-sub">Explore historical climate patterns across Pakistan through NASA POWER data, transparent statistical analysis, and an evidence-led AI Earth Scientist.</div>
  <div class="ew-hero-foot">
    <span class="ew-chip">NASA POWER DATA</span><span class="ew-chip">PROVINCE-WIDE EXPLORATION</span><span class="ew-chip">SCIENTIFIC CONTEXT</span>
  </div>
</section>
""", unsafe_allow_html=True)

if "frames" not in st.session_state:
    st.session_state.frames = {}

provinces = ["All regions"] + sorted({v["province"] for v in REGIONS.values()})
with st.sidebar:
    st.markdown("## 🌍 EARTHWISE AI")
    st.caption("PAKISTAN EARTH INTELLIGENCE")
    st.divider()
    st.markdown("### Location")
    province = st.selectbox("Province / Region", provinces)
    city_options = sorted([c for c, v in REGIONS.items() if province == "All regions" or v["province"] == province])
    city = st.selectbox("City", city_options, index=city_options.index("Lahore") if "Lahore" in city_options else 0)
    st.caption(f"{REGIONS[city]['province']} · {REGIONS[city]['latitude']:.4f}° N, {REGIONS[city]['longitude']:.4f}° E")
    st.divider()
    st.markdown("### Climate signal")
    variable = st.selectbox("Indicator", list(VARIABLES), format_func=lambda k: f"{VARIABLES[k]['label']} · {VARIABLES[k]['unit']}")
    st.markdown("### Time range")
    current_year = date.today().year
    start_year = st.number_input("Start year", min_value=1981, max_value=current_year, value=2001)
    end_year = st.number_input("End year", min_value=int(start_year), max_value=current_year, value=min(current_year - 1, 2025))
    fetch = st.button("↗  Retrieve climate data", type="primary", use_container_width=True)
    st.divider()
    st.caption("SOURCE  /  NASA POWER Daily Point API")
    st.caption("Historical gridded estimates · Not station observations")
    st.caption("Recent records may be incomplete.")

if fetch:
    coords = REGIONS[city]
    with st.status("Connecting to NASA POWER…", expanded=True) as status:
        try:
            st.write("Requesting daily climate records.")
            df_new, metadata = fetch_daily(city, coords["latitude"], coords["longitude"],
                f"{int(start_year)}0101", f"{int(end_year)}1231", parameters=(variable,))
            slug = f"{city.lower().replace(' ', '_').replace('(', '').replace(')', '')}_{variable.lower()}"
            csv_path, meta_path = save_city_data(df_new, metadata, slug)
            st.session_state.frames[(city, variable)] = df_new
            status.update(label="Climate dataset retrieved", state="complete", expanded=False)
            st.toast(f"{city} dataset is ready", icon="🌍")
        except Exception as exc:
            status.update(label="Data retrieval failed", state="error", expanded=True)
            st.error(f"NASA POWER request failed: {exc}")

df = st.session_state.frames.get((city, variable))
if df is None:
    slug = f"{city.lower().replace(' ', '_').replace('(', '').replace(')', '')}_{variable.lower()}"
    candidate = Path("data/raw") / f"{slug}_nasa_power_daily.csv"
    if candidate.exists():
        cached = pd.read_csv(candidate, parse_dates=["date"])
        if variable in cached.columns:
            df = cached

st.markdown('<div class="ew-section">Explore Pakistan</div>', unsafe_allow_html=True)
map_df = pd.DataFrame([{"City": name, "Province": info["province"], "Latitude": info["latitude"], "Longitude": info["longitude"], "Selected": "Selected location" if name == city else "Other city"} for name, info in REGIONS.items()])
map_fig = px.scatter_geo(map_df, lat="Latitude", lon="Longitude", color="Selected", hover_name="City",
    hover_data={"Province": True, "Latitude": ':.3f', "Longitude": ':.3f', "Selected": False},
    color_discrete_map={"Selected location": "#6ce7f4", "Other city": "#4d8dff"})
map_fig.update_geos(scope="asia", projection_type="natural earth", center={"lat": 29.5, "lon": 69.5},
    lataxis_range=[23, 38], lonaxis_range=[60, 78], showland=True, landcolor="#10283b",
    showocean=True, oceancolor="#071522", showcountries=True, countrycolor="#31536b",
    showcoastlines=True, coastlinecolor="#31536b", showframe=False, bgcolor="rgba(0,0,0,0)")
map_fig.update_traces(marker=dict(size=7, opacity=.85, line=dict(width=.7, color="#c9f8ff")))
map_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#a9c2d5", family="DM Sans"), margin=dict(l=0,r=0,t=8,b=0),
    height=390, legend=dict(orientation="h",y=1.05,x=0))
st.plotly_chart(map_fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
st.caption(f"City directory: {len(REGIONS)} major urban centres across all provinces and administrative regions. Points show approximate city-centre coordinates.")

if df is None:
    st.markdown('<div class="ew-section">Your climate workspace</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="ew-panel"><div class="ew-panel-label">01 / Select a location</div><div class="ew-panel-value">Choose a city</div><div class="ew-panel-note">Explore urban centres across Pakistan.</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="ew-panel"><div class="ew-panel-label">02 / Retrieve evidence</div><div class="ew-panel-value">Connect to NASA</div><div class="ew-panel-note">Fetch daily historical climate estimates.</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="ew-panel"><div class="ew-panel-label">03 / Discover patterns</div><div class="ew-panel-value">Read the signal</div><div class="ew-panel-note">Review trends, coverage, and scientific context.</div></div>', unsafe_allow_html=True)
    st.info("Choose a city and climate indicator in the left panel, set the analysis period, then select **Retrieve climate data**.")
    st.caption("Scientific note: NASA POWER provides gridded satellite/model-assisted estimates, not local weather-station observations. This historical research tool does not provide live weather, forecasts, or disaster alerts.")
    st.stop()

meta = coverage_summary(df, variable)
monthly = monthly_aggregate(df, variable)
result = analyze_trend(monthly, variable)
spec = VARIABLES[variable]

st.markdown(f'<div class="ew-section">{city} <span style="color:#6ce7f4">/</span> {spec["label"]}</div>', unsafe_allow_html=True)
st.caption(f"{REGIONS[city]['province']} · Monthly analysis · {spec['unit']} · {meta['first_date']} to {meta['last_date']}")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Data coverage", f"{meta['coverage_pct']}%")
m2.metric("Valid daily records", f"{meta['valid_rows']:,}")
m3.metric("Monthly observations", f"{len(monthly):,}")
m4.metric("Analysis window", f"{start_year if 'start_year' in locals() else monthly['year'].min()}–{end_year if 'end_year' in locals() else monthly['year'].max()}")

tab_overview, tab_trends, tab_data = st.tabs(["◈  Overview", "⌁  Trend analysis", "▤  Data explorer"])
with tab_overview:
    st.markdown('<div class="ew-section">Climate signal over time</div>', unsafe_allow_html=True)
    fig = px.area(monthly, x="date", y=variable, labels={"date":"Month",variable:f"{spec['label']} ({spec['unit']})"})
    fig.update_traces(line=dict(color="#6ce7f4",width=2.5),fillcolor="rgba(74,196,224,.12)",hovertemplate="%{x|%b %Y}<br>%{y:.2f}<extra></extra>")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(7,20,34,.35)",font=dict(family="DM Sans",color="#b7cbd9"),
        margin=dict(l=5,r=10,t=18,b=5),height=390,hovermode="x unified",
        xaxis=dict(showgrid=False,zeroline=False,title=None),yaxis=dict(gridcolor="rgba(145,180,205,.12)",zeroline=False,title=spec["unit"]))
    st.plotly_chart(fig,use_container_width=True,config={"displaylogo":False,"responsive":True})
    st.caption("Monthly precipitation is summed; other indicators are monthly means.")
with tab_trends:
    st.markdown('<div class="ew-section">Statistical trend assessment</div>', unsafe_allow_html=True)
    if result.get("status") == "ok":
        x1,x2,x3,x4=st.columns(4)
        x1.metric("Long-term direction",result["direction"].title())
        x2.metric("Sen slope / decade",f"{result['sen_slope_per_decade']:.4g} {spec['unit']}")
        p_value=result.get("p_value")
        x3.metric("Kendall p-value",f"{p_value:.4g}" if p_value is not None else "Unavailable")
        x4.metric("Significant at 0.05","Yes" if result["significant_005"] else "No")
        st.markdown("#### AI Earth Scientist")
        st.markdown(explain_result(city,spec["label"],spec["unit"],result))
    else:
        st.warning(result.get("message","There is not enough data to calculate a reliable trend."))
    with st.expander("Methodology and scientific limitations"):
        st.write("Trend method: Kendall tau significance test and Sen's slope.")
        st.write("The simple trend test does not correct for monthly seasonality or serial autocorrelation.")
        st.write("The AI explanation summarizes computed fields; it does not independently validate the dataset or establish causation.")
with tab_data:
    st.markdown('<div class="ew-section">Monthly data table</div>', unsafe_allow_html=True)
    st.dataframe(monthly, use_container_width=True, hide_index=True)
    st.download_button("↓  Download monthly data (CSV)",monthly.to_csv(index=False),
        f"{city.lower().replace(' ','_')}_{variable.lower()}_monthly.csv","text/csv",use_container_width=True)

with st.expander("Data provenance & coordinates"):
    st.write("**Source:** NASA POWER Daily Point API")
    st.write("**Coordinates:**",REGIONS[city])
    st.write("**Requested period:**",meta["first_date"],"to",meta["last_date"])
    st.write("**NASA POWER parameter:**",variable)
    st.write("**Aggregation:**","Monthly sum of daily values" if spec["aggregation"]=="sum" else "Monthly mean of daily values")
    st.markdown("[NASA POWER API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)")
st.divider()
st.caption("EARTHWISE AI · Pakistan-first Earth intelligence · Historical data retrieval, not a live monitoring service")

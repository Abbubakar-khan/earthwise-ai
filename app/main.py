from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
import pandas as pd
import plotly.express as px

from src.regions import REGIONS, VARIABLES
from src.nasa_power import fetch_daily, save_city_data
from src.cleaning import monthly_aggregate, coverage_summary
from src.statistics import analyze_trend
from src.ai_engine import explain_result

st.set_page_config(page_title="EARTHWISE AI", page_icon="🌍", layout="wide")
st.title("🌍 EARTHWISE AI")
st.caption("The Intelligent Earth Trend Observatory | FORGE CYBER LAB")
st.warning("Research prototype: NASA POWER provides gridded satellite/model-assisted estimates, not local station measurements. Historical trends are not forecasts or disaster predictions.")

with st.sidebar:
    st.header("Pakistan Earth Explorer")
    city = st.selectbox("Location", list(REGIONS))
    variable = st.selectbox(
        "Earth variable", list(VARIABLES),
        format_func=lambda key: f"{VARIABLES[key]['label']} ({VARIABLES[key]['unit']})"
    )
    start_year = st.number_input("Start year", min_value=1981, max_value=2026, value=2001)
    end_year = st.number_input("End year", min_value=int(start_year), max_value=2026, value=2025)
    fetch = st.button("Fetch NASA POWER data", type="primary", use_container_width=True)
    st.caption("Data access requires an internet connection. Recent/current-year records may be incomplete.")

if "frames" not in st.session_state:
    st.session_state.frames = {}

if fetch:
    coords = REGIONS[city]
    with st.spinner("NASA POWER se data fetch ho raha hai..."):
        try:
            df, metadata = fetch_daily(
                city, coords["latitude"], coords["longitude"],
                f"{int(start_year)}0101", f"{int(end_year)}1231",
                parameters=(variable,)
            )
            slug = city.lower().replace(" ", "_")
            csv_path, meta_path = save_city_data(df, metadata, slug)
            st.session_state.frames[(city, variable)] = df
            st.success(f"Data saved locally: {csv_path}")
            st.caption(f"Retrieval metadata: {meta_path}")
        except Exception as exc:
            st.error(f"NASA API request failed: {exc}")

df = st.session_state.frames.get((city, variable))
if df is None:
    candidate = Path("data/raw") / f"{city.lower().replace(' ', '_')}_nasa_power_daily.csv"
    if candidate.exists():
        cached = pd.read_csv(candidate, parse_dates=["date"])
        if variable in cached.columns:
            df = cached

if df is None:
    st.info("Sidebar se city, variable aur date range select karke **Fetch NASA POWER data** press karein.")
    st.stop()

meta = coverage_summary(df, variable)
monthly = monthly_aggregate(df, variable)
result = analyze_trend(monthly, variable)
spec = VARIABLES[variable]

c1, c2, c3 = st.columns(3)
c1.metric("Valid data coverage", f"{meta['coverage_pct']}%")
c2.metric("Valid daily records", f"{meta['valid_rows']:,}")
c3.metric("Monthly observations", f"{len(monthly):,}")

st.subheader(f"{city}: {spec['label']}")
fig = px.line(
    monthly, x="date", y=variable,
    labels={"date": "Month", variable: f"{spec['label']} ({spec['unit']})"},
    template="plotly_white"
)
fig.update_layout(margin=dict(l=10, r=10, t=25, b=10), hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

if result.get("status") == "ok":
    a, b, c, d = st.columns(4)
    a.metric("Long-term direction", result["direction"].title())
    b.metric("Sen slope / decade", f"{result['sen_slope_per_decade']:.4g} {spec['unit']}")
    p_value = result.get("p_value")
    c.metric("Kendall p-value", f"{p_value:.4g}" if p_value is not None else "Unavailable")
    d.metric("Significant (0.05)", "Yes" if result["significant_005"] else "No")
    st.subheader("AI Earth Scientist")
    st.markdown(explain_result(city, spec["label"], spec["unit"], result))
else:
    st.warning(result.get("message", "Insufficient data."))

with st.expander("Data provenance & limitations"):
    st.write("Source: NASA POWER Daily Point API")
    st.write("Requested range:", meta["first_date"], "to", meta["last_date"])
    st.write("NASA POWER parameter:", variable)
    aggregation = "monthly sum of daily values" if spec["aggregation"] == "sum" else "monthly mean of daily values"
    st.write("Aggregation:", aggregation)
    st.write("Trend method: Kendall tau significance + Sen's slope.")
    st.write("Caveat: the simple trend test does not correct for monthly seasonality or serial autocorrelation.")
    st.write("Coordinates:", REGIONS[city])
    st.write("NASA POWER API documentation: https://power.larc.nasa.gov/docs/services/api/temporal/daily/")

st.download_button(
    "Download monthly CSV", monthly.to_csv(index=False),
    f"{city.lower()}_{variable}_monthly.csv", "text/csv"
)

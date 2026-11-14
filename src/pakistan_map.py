"""Interactive Pakistan map — tap a place, load its live data.

Pure helpers, no Streamlit: the app renders the Plotly figure and reads
the click with st.plotly_chart(on_select="rerun").

Why Plotly and not a Leaflet iframe: a components.html Leaflet map runs
in a sandboxed iframe with NO allow-top-navigation, so a marker click
cannot tell the Streamlit app which city was tapped (verified 2026-11-14
for the geolocation component). A Plotly chart is a native Streamlit
widget, so its point selection comes back to Python on the next run and
the app can switch city, fetch live weather + AQI + climate trend for
that exact place, and rerun. The NASA GIBS Leaflet satellite map stays
as the Earth-observation view on the same page.

The figure colours every place by its live model temperature from the
national snapshot (get_national_weather_snapshot); places the snapshot
could not load for are shown in grey instead of being dropped or
invented.
"""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go

from src.regions import REGIONS

MAP_LAT_RANGE = (23, 38)
MAP_LON_RANGE = (60, 78)


def build_pakistan_map_figure(records, selected_city):
    """Plotly scatter_geo of every REGIONS place.

    records: list of dicts from get_national_weather_snapshot (city,
    latitude, longitude, temperature, condition, province, ...). Places
    missing from records (snapshot failed for them) are still plotted,
    in grey, from REGIONS — the map never hides a place because its live
    fetch failed. Returns a Plotly Figure.
    """
    by_city = {}
    for rec in (records or []):
        if isinstance(rec, dict) and rec.get("city"):
            by_city[rec["city"]] = rec
    rows = []
    for name, info in REGIONS.items():
        rec = by_city.get(name) or {}
        temp = rec.get("temperature")
        try:
            temp = float(temp) if temp is not None else None
        except (TypeError, ValueError):
            temp = None
        rows.append({
            "city": name,
            "province": info["province"],
            "latitude": info["latitude"],
            "longitude": info["longitude"],
            "temperature": temp,
            "condition": rec.get("condition") or "Live data unavailable",
            "live": temp is not None,
        })
    fig = px.scatter_geo(
        rows, lat="latitude", lon="longitude", color="temperature",
        hover_name="city", hover_data={
            "province": True, "temperature": ":.1f",
            "condition": True, "latitude": False, "longitude": False},
        custom_data=["city"],
        color_continuous_scale="Turbo",
        labels={"temperature": "Temperature (°C)"},
    )
    fig.update_traces(
        marker=dict(size=8, line=dict(width=0.6, color="#0b1d2d")),
        selector=dict(type="scattergeo"),
    )
    sel = [r for r in rows if r["city"] == selected_city]
    if sel:
        fig.add_trace(go.Scattergeo(
            lat=[sel[0]["latitude"]], lon=[sel[0]["longitude"]],
            mode="markers", name="Selected place",
            marker=dict(size=15, color="#ffffff", symbol="star",
                        line=dict(width=2, color="#10263b")),
            hovertemplate=f"<b>{selected_city}</b><br>Selected place<extra></extra>",
            customdata=[[selected_city]],
        ))
    fig.update_geos(
        scope="asia", projection_type="natural earth",
        center={"lat": 29.5, "lon": 69.5},
        lataxis_range=list(MAP_LAT_RANGE), lonaxis_range=list(MAP_LON_RANGE),
        showland=True, landcolor="#10283b",
        showocean=True, oceancolor="#071522",
        showcountries=True, countrycolor="#31536b",
        showcoastlines=True, coastlinecolor="#31536b",
        showframe=False, bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b7cbd9", family="DM Sans"),
        margin=dict(l=0, r=0, t=8, b=0), height=560,
        legend=dict(orientation="h", y=1.05, x=0),
        coloraxis_colorbar=dict(title="°C"),
    )
    return fig


def city_from_selection(selection, current_city=None):
    """City name tapped on the map, or None.

    selection: the PlotlyState.selection dict from st.plotly_chart
    ({"points": [{"customdata": ["Lahore"], ...}]}). The star marker for
    the already-selected place also carries its name — that is not a new
    selection, so it returns None when it matches current_city. Unknown
    names and malformed selections return None, never a crash.
    """
    if not isinstance(selection, dict):
        return None
    points = selection.get("points")
    if not isinstance(points, list) or not points:
        return None
    for point in points:
        if not isinstance(point, dict):
            continue
        custom = point.get("customdata")
        name = None
        if isinstance(custom, (list, tuple)) and custom:
            name = custom[0]
        elif isinstance(custom, str):
            name = custom
        if isinstance(name, str) and name in REGIONS and name != current_city:
            return name
    return None

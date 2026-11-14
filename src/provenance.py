"""NASA Data Provenance — trace every live number to its source.

Pure logic + HTML builder, no Streamlit, no network: it takes the dicts
the app already fetched (live weather, AQI, forecast, NASA POWER coverage
summary) and returns one row per source, each with what it provides, when
it was last updated, and whether it is live right now.

Honesty: every row says what the source really is — model estimates and
satellite products, not station observations. A source that failed to
load is shown as unavailable, never silently dropped and never invented.
"""
from __future__ import annotations

import html

DOCS = {
    "power": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
    "openmeteo": "https://open-meteo.com/en/docs",
    "cams": "https://open-meteo.com/en/docs/air-quality-api",
    "gibs": "https://earthdata.nasa.gov/earth-observation-data/near-real-time",
}


def _txt(value, fallback="—"):
    if value is None or (isinstance(value, str) and not value.strip()):
        return fallback
    return str(value)


def provenance_rows(weather, aqi, forecast, meta):
    """One provenance row per source, from already-fetched data.

    weather/aqi/forecast/meta: the dicts the app already has (any may be
    None). Returns a list of dicts: {source, provides, detail, status,
    updated, docs} where status is "live", "unavailable" or "on demand".
    """
    rows = []
    # 1. NASA POWER — 10-year climate history.
    if isinstance(meta, dict) and meta.get("first_date"):
        first = _txt(meta.get("first_date"))[:4]
        last = _txt(meta.get("last_date"))[:4]
        rows.append({
            "source": "NASA POWER",
            "provides": "10-year climate history (daily gridded estimates)",
            "detail": (f"{first}–{last} · {meta.get('coverage_pct', '—')}% coverage · "
                       f"{meta.get('valid_rows', '—'):,} valid daily records"
                       if isinstance(meta.get("valid_rows"), int) else
                       f"{first}–{last} · {meta.get('coverage_pct', '—')}% coverage"),
            "status": "live",
            "updated": f"{meta.get('first_date', '')} to {meta.get('last_date', '')}",
            "docs": DOCS["power"],
        })
    else:
        rows.append({
            "source": "NASA POWER",
            "provides": "10-year climate history (daily gridded estimates)",
            "detail": "Not loaded yet — fetch a climate dataset in the sidebar.",
            "status": "unavailable",
            "updated": None,
            "docs": DOCS["power"],
        })
    # 2. Open-Meteo — live weather + forecast.
    if isinstance(weather, dict) and weather.get("temperature_2m") is not None:
        rows.append({
            "source": "Open-Meteo",
            "provides": "Live weather + 7-day forecast (model data)",
            "detail": (f"{_txt(weather.get('condition_text'))} · "
                       f"{weather.get('temperature_2m'):.1f} °C · "
                       f"feels like {weather.get('apparent_temperature', '—')} °C"),
            "status": "live",
            "updated": f"{_txt(weather.get('provider_time'))} ({_txt(weather.get('timezone'))})",
            "docs": DOCS["openmeteo"],
        })
    else:
        rows.append({
            "source": "Open-Meteo",
            "provides": "Live weather + 7-day forecast (model data)",
            "detail": "Unavailable — check your connection and press Refresh live weather / AQI.",
            "status": "unavailable",
            "updated": None,
            "docs": DOCS["openmeteo"],
        })
    # 3. CAMS via Open-Meteo Air Quality — live AQI.
    if isinstance(aqi, dict) and isinstance(aqi.get("current"), dict):
        cur = aqi["current"]
        rows.append({
            "source": "CAMS · Open-Meteo Air Quality",
            "provides": "Live AQI + pollutants (PM2.5, PM10, O₃, NO₂)",
            "detail": (f"US AQI {cur.get('us_aqi', '—')} · {aqi.get('aqi_label', '')} · "
                       f"PM2.5 {cur.get('pm2_5', '—')} µg/m³ · "
                       f"dominant pollutant {aqi.get('dominant_pollutant', '—')}"),
            "status": "live",
            "updated": f"{_txt(aqi.get('provider_time'))} ({_txt(aqi.get('timezone'))})",
            "docs": DOCS["cams"],
        })
    else:
        rows.append({
            "source": "CAMS · Open-Meteo Air Quality",
            "provides": "Live AQI + pollutants (PM2.5, PM10, O₃, NO₂)",
            "detail": "Unavailable — check your connection and press Refresh live weather / AQI.",
            "status": "unavailable",
            "updated": None,
            "docs": DOCS["cams"],
        })
    # 4. NASA GIBS — satellite imagery (tiles on demand).
    _fc = forecast if isinstance(forecast, dict) else {}
    rows.append({
        "source": "NASA GIBS",
        "provides": "Satellite imagery — VIIRS true colour + GPM IMERG rain",
        "detail": ("Tiles load on the Weather & Maps page — pick an imagery "
                   "date there." +
                   (f" Forecast generated {_txt(_fc.get('forecast_generated_at'))}."
                    if _fc.get("forecast_generated_at") else "")),
        "status": "on demand",
        "updated": None,
        "docs": DOCS["gibs"],
    })
    return rows


_STATUS_STYLE = {
    "live": ("● LIVE", "#2fd08c"),
    "unavailable": ("● UNAVAILABLE", "#f08a2e"),
    "on demand": ("● ON DEMAND", "#9db2c0"),
}


def provenance_html(rows, city):
    """Render the provenance panel as one card. Rows come from
    provenance_rows(); every dynamic string is escaped."""
    items = []
    for row in rows or []:
        label, colour = _STATUS_STYLE.get(row.get("status", ""), ("●", "#9db2c0"))
        updated = (f"<br><span style=\"color:#8299a8\">Updated: "
                   f"{html.escape(str(row['updated']))}</span>"
                   if row.get("updated") else "")
        items.append(
            f'<div class="ew-prov-row">'
            f'<div class="ew-prov-src"><b>{html.escape(str(row.get("source", "")))}</b>'
            f'<span style="color:{colour};font-size:.68rem;font-weight:700">'
            f"{label}</span></div>"
            f'<div class="ew-prov-what">{html.escape(str(row.get("provides", "")))}</div>'
            f'<div class="ew-prov-detail">{html.escape(str(row.get("detail", "")))}{updated}</div>'
            f'<div class="ew-prov-docs"><a href="{html.escape(str(row.get("docs", "")))}" '
            f'target="_blank" rel="noopener">Source docs ↗</a></div>'
            f"</div>"
        )
    return (
        '<div class="card ew-prov">'
        '<div class="ew-card-head"><b>🛰️ NASA data provenance — where every number comes from</b>'
        f'<span>Live for {html.escape(str(city))} · Tap a source to read its docs</span></div>'
        + "".join(items) +
        '<p class="ew-card-foot">All four sources are model estimates / satellite products — '
        'not station observations. NASA POWER is a gridded reanalysis estimate; '
        'Open-Meteo and CAMS are model forecasts; GIBS tiles are satellite imagery. '
        'For official warnings, use the Pakistan Meteorological Department.</p>'
        "</div>"
    )

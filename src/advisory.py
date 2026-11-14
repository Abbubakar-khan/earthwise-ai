"""Daily advisories — plain-language decisions from live data.

Three features no weather app bundles for a Pakistani city:

1. **Health verdict ("Aaj ka din")** — one score from live AQI + heat +
   humidity, with concrete actions (mask, children indoors, water, when to
   exercise). Weather apps show numbers; none tells you what to *do*.
2. **Farmer advisory** — irrigation / sowing / spraying guidance from the
   7-day model forecast (rain in the next 48 h, dry spells, heat, frost,
   wind). No weather app gives Pakistan-farmer advice.
3. **Rain warning** — heavy-rain screening for the next 7 days (worst day,
   7-day total, travel/drainage advice).

Pure logic, no Streamlit, no network: every function takes the dicts the
app already fetched (Open-Meteo current + 7-day forecast, CAMS AQI) and
returns plain data. Every function is defensive — missing or partial data
returns an "unavailable" result instead of raising, so a page never
crashes on a bad fetch.

Honesty notes (shown in the app next to each advisory):
- Thresholds are this app's own screening rules, documented below — not
  medical advice, not agronomy advice, not an official PMD warning.
- AQI bands follow the US EPA bands already used in src/air_quality.py.
- Heat bands are chosen for Pakistan summers (apparent temperature):
  35 C feels hot, 40 C is dangerous work outdoors, 43 C+ is extreme.
- Rain bands follow common forecast practice: 20 mm/day is heavy,
  50 mm/day is very heavy for one day in most Pakistani cities.
"""
from __future__ import annotations

from datetime import datetime

# ---------- shared helpers ----------

def _num(value):
    """Float or None — never raises on junk."""
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _day_label(iso_date: str) -> str:
    """'2026-11-14' -> 'Sat 14 Nov'; falls back to the raw string."""
    try:
        return datetime.strptime(str(iso_date)[:10], "%Y-%m-%d").strftime("%a %d %b")
    except (TypeError, ValueError):
        return str(iso_date)


def _daily_days(daily):
    """Normalise the Open-Meteo daily dict into a list of day dicts.

    Arrays can be short or ragged if the provider changes shape; use the
    shortest length and skip days with no date. Returns [] for anything
    unusable (caller reports 'unavailable').
    """
    if not isinstance(daily, dict):
        return []
    times = daily.get("time") or []
    if not isinstance(times, (list, tuple)) or not times:
        return []
    keys = ("temperature_2m_max", "temperature_2m_min", "precipitation_sum",
            "precipitation_probability_max", "wind_speed_10m_max", "weather_code")
    n = len(times)
    for key in keys:
        vals = daily.get(key)
        if isinstance(vals, (list, tuple)):
            n = min(n, len(vals))
    days = []
    for i in range(n):
        def _at(key):
            vals = daily.get(key)
            if isinstance(vals, (list, tuple)) and i < len(vals):
                return _num(vals[i])
            return None
        days.append({
            "date": _day_label(times[i]),
            "tmax": _at("temperature_2m_max"),
            "tmin": _at("temperature_2m_min"),
            "rain_mm": _at("precipitation_sum"),
            "rain_prob": _at("precipitation_probability_max"),
            "wind_max": _at("wind_speed_10m_max"),
            "code": _at("weather_code"),
        })
    return days


# ---------- 1. Health verdict ----------

def _aqi_points(us_aqi):
    """US EPA bands (same as src/air_quality.py) -> 0..5 points."""
    v = _num(us_aqi)
    if v is None:
        return 0
    if v <= 50:
        return 0
    if v <= 100:
        return 1
    if v <= 150:
        return 2
    if v <= 200:
        return 3
    if v <= 300:
        return 4
    return 5


def _heat_points(apparent_c, temp_c):
    """Apparent temperature (feels-like) -> 0..4 points."""
    v = _num(apparent_c)
    if v is None:
        v = _num(temp_c)
    if v is None:
        return 0
    if v < 30:
        return 0
    if v < 35:
        return 1
    if v < 40:
        return 2
    if v < 43:
        return 3
    return 4


def daily_health_verdict(weather, aqi):
    """One health verdict for today from live weather + live AQI.

    weather: get_current_conditions dict (may be None). aqi: get_air_quality
    dict (may be None). Returns {"status": "ok"|"unavailable", ...}.
    """
    if not weather and not aqi:
        return {"status": "unavailable"}
    current = (aqi or {}).get("current") or {}
    us_aqi = _num(current.get("us_aqi"))
    pm25 = _num(current.get("pm2_5"))
    temp = _num((weather or {}).get("temperature_2m"))
    apparent = _num((weather or {}).get("apparent_temperature"))
    humidity = _num((weather or {}).get("relative_humidity_2m"))
    if us_aqi is None and temp is None:
        return {"status": "unavailable"}

    aqi_pts = _aqi_points(us_aqi)
    heat_pts = _heat_points(apparent, temp)
    humid_pts = 1 if (humidity is not None and humidity >= 75
                      and temp is not None and temp >= 30) else 0
    score = min(10, aqi_pts * 2 + heat_pts + humid_pts)

    if score <= 2:
        label, colour = "Good day", "#2fd08c"
    elif score <= 5:
        label, colour = "Fair — take basic care", "#f5c542"
    elif score <= 8:
        label, colour = "Be careful today", "#f08a2e"
    else:
        label, colour = "Stay indoors if you can", "#e5484d"

    factors = []
    if us_aqi is not None:
        factors.append(f"Air quality: US AQI {us_aqi:.0f} "
                       f"({(aqi or {}).get('aqi_label', '—')})")
    if apparent is not None:
        factors.append(f"Feels like {apparent:.0f}°C")
    elif temp is not None:
        factors.append(f"Temperature {temp:.0f}°C")
    if humidity is not None:
        factors.append(f"Humidity {humidity:.0f}%")
    if pm25 is not None:
        factors.append(f"PM2.5 {pm25:.1f} µg/m³ "
                       f"(dominant pollutant: {(aqi or {}).get('dominant_pollutant', '—')})")

    actions = []
    if us_aqi is not None and us_aqi >= 151:
        actions.append("Wear a mask outdoors (N95/KN95 if you have one).")
    if us_aqi is not None and us_aqi >= 101:
        actions.append("Children, elderly people and anyone with asthma "
                       "should stay indoors as much as possible.")
        actions.append("Avoid outdoor exercise in the morning and evening "
                       "smog hours; keep windows closed then.")
    if apparent is not None and apparent >= 40:
        actions.append("Drink water often; rest in the shade; "
                       "avoid the midday sun (11am–4pm).")
    elif apparent is not None and apparent >= 35:
        actions.append("Stay hydrated and take breaks in the shade.")
    if humid_pts:
        actions.append("Humid air makes heat feel worse — wear light "
                       "clothes and drink extra water.")
    if not actions:
        actions.append("Good day for outdoor activity — enjoy it.")
    return {"status": "ok", "score": score, "label": label, "colour": colour,
            "us_aqi": us_aqi, "pm2_5": pm25, "apparent": apparent,
            "temperature": temp, "humidity": humidity,
            "factors": factors, "actions": actions}


# ---------- 2. Farmer advisory ----------

def farmer_advisory(forecast):
    """Irrigation / sowing / spraying guidance from the 7-day forecast.

    forecast: get_weather_forecast dict (may be None). Returns
    {"status": "ok"|"unavailable", "items": [...], "summary": str,
    "week_rain_mm": float|None}.
    """
    days = _daily_days((forecast or {}).get("daily"))
    if not days:
        return {"status": "unavailable", "items": [], "summary": "",
                "week_rain_mm": None}
    items = []
    rain_48 = sum((d["rain_mm"] or 0) for d in days[:2])
    prob_48 = max((d["rain_prob"] or 0) for d in days[:2])
    if rain_48 >= 5 or prob_48 >= 70:
        items.append({"level": "info", "title": "Hold off irrigation",
                      "detail": f"Rain is expected in the next 2 days "
                                f"({rain_48:.0f} mm, up to {prob_48:.0f}% chance) "
                                f"— watering now would waste water."})
    week_rain = sum((d["rain_mm"] or 0) for d in days)
    hot_days = [d for d in days if d["tmax"] is not None and d["tmax"] >= 35]
    if week_rain < 2:
        detail = "No rain is expected this week — plan irrigation."
        if hot_days:
            detail += (" Hot days ahead (up to "
                       f"{max(d['tmax'] for d in hot_days):.0f}°C) — water early "
                       "in the morning or in the evening to cut evaporation.")
        items.append({"level": "info", "title": "Dry week ahead",
                      "detail": detail})
    for d in days:
        if d["rain_mm"] is not None and d["rain_mm"] >= 20:
            items.append({"level": "warning", "title": f"Heavy rain on {d['date']}",
                          "detail": f"{d['rain_mm']:.0f} mm expected — avoid sowing "
                                    "and spraying that day; check field drainage."})
    for d in days:
        if d["tmin"] is not None and d["tmin"] <= 2:
            items.append({"level": "warning", "title": f"Frost risk on {d['date']}",
                          "detail": f"Night low {d['tmin']:.0f}°C — protect "
                                    "sensitive crops overnight."})
    for d in days:
        if d["wind_max"] is not None and d["wind_max"] >= 40:
            items.append({"level": "warning", "title": f"Strong wind on {d['date']}",
                          "detail": f"Gusts up to {d['wind_max']:.0f} km/h — "
                                    "delay spraying that day."})
    for d in days:
        if d["tmax"] is not None and d["tmax"] >= 40:
            items.append({"level": "warning", "title": f"Heat stress on {d['date']}",
                          "detail": f"Day high {d['tmax']:.0f}°C — irrigate in "
                                    "the evening and watch for wilting."})
    # Good window: first run of 2+ dry days with workable temperatures.
    run = []
    for d in days:
        dry = (d["rain_mm"] or 0) < 1
        mild = (d["tmax"] is not None and 20 <= d["tmax"] <= 33)
        if dry and mild:
            run.append(d)
            if len(run) >= 2:
                break
        else:
            run = []
    if len(run) >= 2:
        items.append({"level": "good",
                      "title": f"Good window for field work: {run[0]['date']} – {run[-1]['date']}",
                      "detail": "Dry days with mild temperatures — a good "
                                "time for sowing or spraying."})
    if not items:
        items.append({"level": "good", "title": "No strong signals this week",
                      "detail": "Conditions look normal for field work — "
                                "no rain, frost, heat or wind warnings."})
    warnings = sum(1 for it in items if it["level"] == "warning")
    summary = (f"{week_rain:.0f} mm of rain expected this week"
               + (f" · {warnings} warning{'s' if warnings != 1 else ''}" if warnings else " · no warnings"))
    return {"status": "ok", "items": items, "summary": summary,
            "week_rain_mm": week_rain}


# ---------- 3. Rain warning ----------

RAIN_LEVELS = [
    (50, "very heavy", "Very heavy rain", "#e5484d"),
    (20, "heavy", "Heavy rain", "#f08a2e"),
    (5, "moderate", "Moderate rain", "#f5c542"),
    (0, "none", "No heavy rain", "#2fd08c"),
]


def _rain_level(mm):
    v = _num(mm) or 0
    for threshold, key, label, colour in RAIN_LEVELS:
        if v >= threshold:
            return key, label, colour
    return "none", "No heavy rain", "#2fd08c"


def rain_warning(forecast):
    """Heavy-rain screening for the next 7 days.

    forecast: get_weather_forecast dict (may be None). Returns
    {"status": "ok"|"unavailable", "level", "label", "colour",
    "total_mm", "worst_day", "worst_mm", "heavy_days", "days": [...],
    "advice": str}.
    """
    days = _daily_days((forecast or {}).get("daily"))
    if not days:
        return {"status": "unavailable", "level": "none",
                "label": "No heavy rain", "colour": "#2fd08c",
                "total_mm": None, "worst_day": None, "worst_mm": None,
                "heavy_days": 0, "days": [], "advice": ""}
    enriched = []
    for d in days:
        key, label, colour = _rain_level(d["rain_mm"])
        enriched.append({**d, "level": key, "label": label, "colour": colour})
    total = sum((d["rain_mm"] or 0) for d in days)
    worst = max(days, key=lambda d: d["rain_mm"] or 0)
    worst_mm = worst["rain_mm"] or 0
    heavy_days = sum(1 for d in enriched if d["level"] in ("heavy", "very heavy"))
    level, label, colour = _rain_level(worst_mm)
    if level == "none":
        advice = ("No heavy rain is expected this week — normal travel "
                  "and outdoor plans are fine.")
    elif level == "moderate":
        advice = ("Some rain is expected — carry rain cover and allow "
                  "extra time on wet roads.")
    elif level == "heavy":
        advice = (f"Heavy rain is expected on {worst['date']} ({worst_mm:.0f} mm) — "
                  "avoid unnecessary travel during the heaviest hours and "
                  "clear drains around your home.")
    else:
        advice = (f"Very heavy rain is expected on {worst['date']} ({worst_mm:.0f} mm) — "
                  "stay updated with PMD warnings, avoid riverbanks and "
                  "low-lying roads, and do not drive through flooded streets.")
    return {"status": "ok", "level": level, "label": label, "colour": colour,
            "total_mm": total, "worst_day": worst["date"], "worst_mm": worst_mm,
            "heavy_days": heavy_days, "days": enriched, "advice": advice}


# ---------- Overview teaser ----------

def advisory_summary(weather, aqi, forecast):
    """One-line teaser for the Overview page: health label + rain level.

    Never raises; returns None when nothing is available.
    """
    health = daily_health_verdict(weather, aqi)
    rain = rain_warning(forecast)
    if health.get("status") != "ok" and rain.get("status") != "ok":
        return None
    return {
        "health_label": health.get("label") if health.get("status") == "ok" else None,
        "health_score": health.get("score") if health.get("status") == "ok" else None,
        "health_colour": health.get("colour") if health.get("status") == "ok" else None,
        "rain_label": rain.get("label") if rain.get("status") == "ok" else None,
        "rain_colour": rain.get("colour") if rain.get("status") == "ok" else None,
        "rain_total_mm": rain.get("total_mm") if rain.get("status") == "ok" else None,
    }

"""Body & weather — how today's weather works on your heart and body.

Two features no weather app gives:

1. **Heart / body strain graph** — a 24-hour curve of the estimated
   strain on the heart and body, from the hourly forecast (temperature)
   plus today's humidity and AQI. Hot, humid, smoggy hours push the
   curve up; cool, clean hours keep it low. It also names the hardest
   hour of the day and what to do about it.
2. **Best hours today** — the best 2–3 hours to be outdoors (exercise,
   travel, field work) and the hours to avoid, from the same hourly
   forecast. One glance instead of reading 24 numbers.

Pure logic, no Streamlit, no network: every function takes the dicts the
app already fetched (Open-Meteo current + hourly forecast, CAMS AQI) and
returns plain data. Defensive — missing data returns "unavailable"
instead of raising.

HONESTY — read this before showing the graph to anyone:
- This is an **estimate of strain from weather data** (temperature,
  humidity, AQI). It is **NOT a heartbeat measurement**: no smartwatch
  or heart sensor is connected, and no real heart-rate data exists in
  this app. A real heartbeat graph needs a wearable; the app says this
  next to the graph.
- Strain bands are this app's own screening rules (heat strain rises
  steeply above 32 °C apparent; cold strain below 5 °C; smog adds load
  on the heart and lungs). They are general guidance, not medical
  advice — anyone with a heart condition should follow their doctor,
  not this graph.
"""
from __future__ import annotations

from datetime import datetime


def _num(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _hour_label(iso_time: str) -> str:
    """'2026-11-14T14:00' -> '14:00'; falls back to the raw string."""
    try:
        return datetime.strptime(str(iso_time)[:16], "%Y-%m-%dT%H:%M").strftime("%H:%M")
    except (TypeError, ValueError):
        return str(iso_time)


def _temp_strain(temp_c):
    """Temperature -> 0..9 strain points (heat and cold both load the body)."""
    v = _num(temp_c)
    if v is None:
        return 0
    if v < 5:
        return 4
    if v < 10:
        return 2
    if v < 27:
        return 0
    if v < 30:
        return 1
    if v < 33:
        return 3
    if v < 36:
        return 4
    if v < 39:
        return 6
    if v < 42:
        return 7
    if v < 45:
        return 8
    return 9


def _aqi_strain(us_aqi):
    """AQI -> 0..3 extra strain points (smog loads heart and lungs)."""
    v = _num(us_aqi)
    if v is None:
        return 0
    if v <= 100:
        return 0
    if v <= 150:
        return 1
    if v <= 200:
        return 2
    return 3


def _strain_label(score):
    if score <= 2:
        return "Easy on the body", "#2fd08c"
    if score <= 5:
        return "Moderate strain", "#f5c542"
    if score <= 7:
        return "Hard on the body", "#f08a2e"
    return "Very hard — take care", "#e5484d"


def hourly_strain(hourly, humidity=None, us_aqi=None):
    """24-hour body-strain curve from the hourly forecast.

    hourly: forecast["hourly"] dict with time / temperature_2m /
    precipitation / precipitation_probability (may be None or partial).
    humidity: current relative humidity (%). us_aqi: current US AQI.
    Returns {"status": "ok"|"unavailable", "hours": [...], "peak": {...}|None}.
    Each hour: {"time", "temp", "strain", "label"}.
    """
    if not isinstance(hourly, dict):
        return {"status": "unavailable", "hours": [], "peak": None}
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    precips = hourly.get("precipitation") or []
    probs = hourly.get("precipitation_probability") or []
    if not isinstance(times, (list, tuple)) or not times:
        return {"status": "unavailable", "hours": [], "peak": None}
    n = len(times)
    for vals in (temps, precips, probs):
        if isinstance(vals, (list, tuple)):
            n = min(n, len(vals))
    hum = _num(humidity)
    aqi_mod = _aqi_strain(us_aqi)
    hours = []
    for i in range(n):
        temp = _num(temps[i]) if i < len(temps) else None
        precip = _num(precips[i]) if i < len(precips) else None
        score = _temp_strain(temp) + aqi_mod
        if hum is not None and hum >= 75 and temp is not None and temp >= 28:
            score += 1
        if precip is not None and precip > 0.5 and temp is not None and temp < 20:
            score += 1  # wet + cold
        score = max(0, min(10, score))
        label, _ = _strain_label(score)
        hours.append({"time": _hour_label(times[i]), "temp": temp,
                      "strain": score, "label": label})
    peak = max(hours, key=lambda h: h["strain"]) if hours else None
    return {"status": "ok", "hours": hours, "peak": peak}


def current_strain(weather, aqi):
    """Strain on the body right now, from live weather + live AQI.

    weather: get_current_conditions dict (may be None). aqi:
    get_air_quality dict (may be None). Returns
    {"status": "ok"|"unavailable", "score", "label", "colour", "advice"}.
    """
    if not weather and not aqi:
        return {"status": "unavailable"}
    temp = _num((weather or {}).get("temperature_2m"))
    apparent = _num((weather or {}).get("apparent_temperature"))
    humidity = _num((weather or {}).get("relative_humidity_2m"))
    us_aqi = _num(((aqi or {}).get("current") or {}).get("us_aqi"))
    if temp is None and apparent is None and us_aqi is None:
        return {"status": "unavailable"}
    feel = apparent if apparent is not None else temp
    score = _temp_strain(feel) + _aqi_strain(us_aqi)
    if humidity is not None and humidity >= 75 and feel is not None and feel >= 28:
        score += 1
    score = max(0, min(10, score))
    label, colour = _strain_label(score)
    advice = []
    if score >= 8:
        advice.append("Rest as much as you can, stay cool and drink water "
                      "often; avoid heavy work outdoors.")
    elif score >= 6:
        advice.append("Take it slow outdoors — rest in the shade and drink "
                      "water regularly.")
    if us_aqi is not None and us_aqi >= 151:
        advice.append("Smog is adding load on your heart and lungs — wear a "
                      "mask outdoors and keep exertion light.")
    if feel is not None and feel >= 40:
        advice.append("Extreme heat: the heart works much harder — stay out "
                      "of the midday sun.")
    if feel is not None and feel < 5:
        advice.append("Bitter cold strains the heart too — dress warmly and "
                      "avoid sudden heavy exertion.")
    if not advice:
        advice.append("Easy conditions for your body right now.")
    return {"status": "ok", "score": score, "label": label, "colour": colour,
            "advice": advice, "temperature": temp, "apparent": apparent,
            "humidity": humidity, "us_aqi": us_aqi}


def best_hours(hourly, us_aqi=None):
    """Best and worst hours to be outdoors today (06:00–20:00).

    hourly: forecast["hourly"] dict (may be None). us_aqi: current US AQI.
    Returns {"status": "ok"|"unavailable", "best": [...], "avoid": [...],
    "summary": str}. Each entry: {"time", "temp", "rain_prob", "score",
    "reason"}. "avoid" only lists hours scoring 5 or below.
    """
    if not isinstance(hourly, dict):
        return {"status": "unavailable", "best": [], "avoid": [], "summary": ""}
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    precips = hourly.get("precipitation") or []
    probs = hourly.get("precipitation_probability") or []
    if not isinstance(times, (list, tuple)) or not times:
        return {"status": "unavailable", "best": [], "avoid": [], "summary": ""}
    n = len(times)
    for vals in (temps, precips, probs):
        if isinstance(vals, (list, tuple)):
            n = min(n, len(vals))
    aqi_mod = _aqi_strain(us_aqi)
    scored = []
    for i in range(n):
        label = _hour_label(times[i])
        try:
            hour = int(label.split(":")[0])
        except (ValueError, IndexError):
            continue
        if hour < 6 or hour > 20:
            continue
        temp = _num(temps[i]) if i < len(temps) else None
        precip = _num(precips[i]) if i < len(precips) else None
        prob = _num(probs[i]) if i < len(probs) else None
        score = 10 - _temp_strain(temp) - aqi_mod
        if prob is not None:
            score -= prob / 25.0
        if precip is not None and precip > 0.5:
            score -= 2
        score = max(0, min(10, round(score, 1)))
        bits = []
        if temp is not None:
            bits.append(f"{temp:.0f}°C")
        bits.append("dry" if (precip or 0) <= 0.5 else "wet")
        if prob is not None:
            bits.append(f"rain chance {prob:.0f}%")
        scored.append({"time": label, "temp": temp,
                       "rain_prob": prob, "score": score,
                       "reason": ", ".join(bits)})
    if not scored:
        return {"status": "unavailable", "best": [], "avoid": [], "summary": ""}
    ranked = sorted(scored, key=lambda h: (-h["score"], h["time"]))
    best = ranked[:3]
    avoid = [h for h in sorted(scored, key=lambda h: (h["score"], h["time"]))
             if h["score"] <= 5][:2]
    summary = ("Best time outdoors: " + ", ".join(b["time"] for b in best)
               + (f" · Avoid {avoid[0]['time']}" if avoid else " · No bad hours today"))
    return {"status": "ok", "best": best, "avoid": avoid, "summary": summary}

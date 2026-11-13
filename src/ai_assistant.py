"""Evidence-bound AI assistant — rule-based, no LLM, no hallucination.

It answers ONLY from the context the app passes in (real live weather,
real air quality, real computed trend / anomaly / risk). If the data is
not in the context it says so instead of inventing an answer.
"""
from __future__ import annotations


def _fmt(v, unit="", nd=1):
    if v is None:
        return "not available"
    try:
        return f"{float(v):.{nd}f} {unit}".strip()
    except (TypeError, ValueError):
        return str(v)


def answer_question(question: str, ctx: dict) -> str:
    q = (question or "").lower().strip()
    city = ctx.get("city", "the selected city")
    if not q:
        return "Ask me about the weather, air quality, climate trend, anomalies or risk for the selected city — I answer from the live data loaded on this page."

    # --- weather / now ---
    if any(w in q for w in ("weather", "temperature now", "how hot", "how cold", "right now", "today")):
        w = ctx.get("weather") or {}
        return (f"**{city} — right now (model-based, Open-Meteo):** "
                f"{_fmt(w.get('temperature_2m'), '°C')} air temperature, "
                f"feels like {_fmt(w.get('apparent_temperature'), '°C')}, "
                f"humidity {_fmt(w.get('relative_humidity_2m'), '%', 0)}, "
                f"wind {_fmt(w.get('wind_speed_10m'), 'km/h')}, "
                f"precipitation {_fmt(w.get('precipitation'), 'mm')}. "
                f"Condition: {w.get('condition_text', 'not available')}. "
                f"This is a model estimate, not a station observation — check PMD for official warnings.")

    # --- air quality ---
    if any(w in q for w in ("air", "aqi", "pollution", "pm2", "smog", "breathe")):
        a = ctx.get("air_quality") or {}
        cur = a.get("current") or {}
        if not cur:
            return f"I don't have air-quality data loaded for {city} yet — open the Air Quality page to fetch it from the Open-Meteo / CAMS API."
        return (f"**{city} — air quality (CAMS, Open-Meteo):** US AQI **{_fmt(cur.get('us_aqi'), '', 0)} — {a.get('aqi_label', '')}**. "
                f"PM2.5 {_fmt(cur.get('pm2_5'), 'µg/m³')}, PM10 {_fmt(cur.get('pm10'), 'µg/m³')}, "
                f"ozone {_fmt(cur.get('ozone'), 'µg/m³')}, NO₂ {_fmt(cur.get('nitrogen_dioxide'), 'µg/m³')}. "
                f"Dominant pollutant: {a.get('dominant_pollutant', '—')}. {a.get('aqi_advice', '')}")

    # --- trend ---
    if any(w in q for w in ("trend", "warming", "cooling", "changing", "increase", "decrease", "climate")):
        t = ctx.get("trend") or {}
        if t.get("status") != "ok":
            return (f"I can't give a trend for {city} yet — fetch NASA POWER climate data first "
                    f"(Climate Analytics page). At least 24 monthly observations are needed.")
        return (f"**{city} — {ctx.get('variable_label', 'climate')} trend:** {t.get('direction')}, "
                f"Sen's slope **{t.get('sen_slope_per_decade'):+.3g} {ctx.get('unit', '')} per decade**, "
                f"Kendall p-value {t.get('p_value')}, "
                f"{'significant' if t.get('significant_005') else 'not significant'} at 0.05, "
                f"over {t.get('first_month')} to {t.get('last_month')} ({t.get('n')} months). "
                f"This is a historical statistical trend, not a forecast, and seasonality/autocorrelation are not corrected in this MVP.")

    # --- anomaly ---
    if any(w in q for w in ("anomal", "unusual", "normal", "departure")):
        an = ctx.get("latest_anomaly")
        if an is None:
            return f"No seasonal anomaly is loaded for {city} yet — fetch climate data first."
        return (f"The latest monthly departure from the same-calendar-month mean in {city} is "
                f"**{float(an):+.2f} {ctx.get('unit', '')}**. "
                f"The baseline is the mean for that calendar month inside the selected dataset — not a 1991–2020 climate normal.")

    # --- risk ---
    if any(w in q for w in ("risk", "danger", "flood", "heatwave", "safe")):
        r = ctx.get("risk") or {}
        if r.get("composite") is None:
            return f"No risk screening is available for {city} yet — fetch climate data and live weather/AQI first. Risk here is a screening signal, never an official alert."
        return (f"**{city} — screening risk: {r.get('composite_label')} (composite {r.get('composite')}/100).** "
                f"Trend: {r.get('scores', {}).get('trend_label', '—')}, "
                f"air quality: {r.get('scores', {}).get('air_quality_label', '—')}, "
                f"current heat: {r.get('scores', {}).get('heat_now_label', '—')}. "
                f"This is a screening signal only — for warnings use PMD and health authorities.")

    # --- forecast ---
    if any(w in q for w in ("forecast", "tomorrow", "next week", "rain")):
        f = ctx.get("forecast_summary")
        if not f:
            return f"I don't have a forecast loaded for {city} — open the Weather page. Forecasts are model products and can change."
        return f"**{city} — 7-day model forecast:** {f}"

    # --- data / sources ---
    if any(w in q for w in ("source", "data", "where", "nasa", "open-meteo")):
        return ("Data sources on this page: **NASA POWER** (historical daily climate, no key), "
                "**Open-Meteo** (current weather + 7-day forecast, free evaluation endpoint; commercial use needs OPEN_METEO_API_KEY), "
                "**Open-Meteo Air Quality / CAMS** (live AQI, no key), and **NASA GIBS** (VIIRS / GPM IMERG satellite tiles, no key). "
                "All values are labelled with their provider and timestamp.")

    if any(w in q for w in ("hello", "hi", "hey", "salam")):
        return (f"Hello! I'm the EarthWise assistant for **{city}**. I can explain the live weather, "
                f"air quality, climate trend, anomalies and risk screening — all from the real data on this page. Try: "
                f"“What is the trend?” or “How is the air quality?”")

    return ("I can only answer from the data loaded for this city — weather, air quality, climate trend, "
            "anomalies, forecast or risk. Try one of those, e.g. “What is the air quality in "
            f"{city}?” or “What is the temperature trend?”")

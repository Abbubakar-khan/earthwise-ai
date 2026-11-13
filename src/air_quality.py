"""Real air-quality data from the Open-Meteo Air Quality API (CAMS).

Free, no API key required. https://open-meteo.com/en/docs/air-quality-api
Values are model / CAMS reanalysis estimates, not a local monitoring station.
US AQI is computed by Open-Meteo from the pollutant concentrations.
"""
from __future__ import annotations

import requests
import streamlit as st

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# US EPA AQI breakpoints: (label, colour, advice)
AQI_BANDS = [
    (0, 50, "Good", "#2fd08c", "Air quality is satisfactory."),
    (51, 100, "Moderate", "#f5c542", "Acceptable; unusually sensitive people should watch symptoms."),
    (101, 150, "Unhealthy for Sensitive Groups", "#f08a2e", "Sensitive groups should reduce prolonged outdoor exertion."),
    (151, 200, "Unhealthy", "#e5484d", "Everyone may feel effects; reduce prolonged outdoor exertion."),
    (201, 300, "Very Unhealthy", "#9b5de5", "Health alert: avoid prolonged outdoor exertion."),
    (301, 500, "Hazardous", "#7a1f2b", "Emergency conditions: avoid outdoor activity."),
]


def aqi_category(us_aqi):
    """Return (label, colour, advice) for a US AQI value, or Unknown."""
    if us_aqi is None:
        return ("Unknown", "#8a9aa8", "No AQI value was returned.")
    try:
        v = float(us_aqi)
    except (TypeError, ValueError):
        return ("Unknown", "#8a9aa8", "No AQI value was returned.")
    for lo, hi, label, colour, advice in AQI_BANDS:
        if lo <= v <= hi:
            return (label, colour, advice)
    return ("Hazardous", "#7a1f2b", "Emergency conditions: avoid outdoor activity.")


def dominant_pollutant(current: dict) -> str:
    """Best-effort dominant pollutant from PM2.5 / PM10 / O3 / NO2, by WHO guideline ratio."""
    # WHO 2021 annual guideline values (ug/m3): PM2.5 5, PM10 15, O3 60 (peak-season 8h), NO2 10
    guides = {"pm2_5": (5, "PM2.5"), "pm10": (15, "PM10"),
              "ozone": (60, "Ozone"), "nitrogen_dioxide": (10, "NO2")}
    best, best_ratio = "—", 0.0
    for key, (guide, label) in guides.items():
        try:
            v = float(current.get(key))
        except (TypeError, ValueError):
            continue
        if v / guide > best_ratio:
            best, best_ratio = label, v / guide
    return best


@st.cache_data(ttl=30 * 60, show_spinner=False)
def get_air_quality(latitude: float, longitude: float, city: str = "") -> dict:
    """Fetch current + next-24h hourly air quality. Raises on failure."""
    params = {
        "latitude": latitude, "longitude": longitude,
        "current": "pm2_5,pm10,us_aqi,european_aqi,ozone,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide,dust",
        "hourly": "pm2_5,pm10,us_aqi",
        "forecast_days": 2, "timezone": "auto",
    }
    resp = requests.get(API_URL, params=params, timeout=25)
    resp.raise_for_status()
    payload = resp.json()
    current = payload.get("current")
    if not isinstance(current, dict) or current.get("us_aqi") is None and current.get("pm2_5") is None:
        raise ValueError("The air-quality provider returned an incomplete payload.")
    label, colour, advice = aqi_category(current.get("us_aqi"))
    return {
        "city": city, "current": current, "hourly": payload.get("hourly", {}),
        "timezone": payload.get("timezone", "Local time"),
        "provider_time": current.get("time", "Time unavailable"),
        "source": "Open-Meteo Air Quality API (CAMS)",
        "aqi_label": label, "aqi_colour": colour, "aqi_advice": advice,
        "dominant_pollutant": dominant_pollutant(current),
    }

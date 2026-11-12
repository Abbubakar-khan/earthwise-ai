"""Latest model-based weather conditions from Open-Meteo.

These are model-derived current conditions, not guaranteed ground-station observations.
"""
from __future__ import annotations

import requests
import streamlit as st

API_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


@st.cache_data(ttl=15 * 60, show_spinner=False)
def get_current_conditions(latitude: float, longitude: float, city: str) -> dict:
    """Fetch current model conditions; cached briefly to avoid excessive API requests."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "precipitation", "weather_code", "wind_speed_10m",
            "wind_direction_10m", "cloud_cover",
        ]),
        "timezone": "auto",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }
    response = requests.get(API_URL, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    current = payload.get("current")
    if not isinstance(current, dict) or "temperature_2m" not in current:
        raise ValueError("The weather provider returned an incomplete current-conditions payload.")
    code = current.get("weather_code")
    current["condition_text"] = WEATHER_CODES.get(code, "Conditions unavailable")
    current["city"] = city
    current["timezone"] = payload.get("timezone", "Local time")
    current["provider_time"] = current.get("time", "Time unavailable")
    current["source"] = "Open-Meteo forecast models"
    return current

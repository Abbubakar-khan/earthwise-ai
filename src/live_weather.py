"""Latest model-based weather conditions from Open-Meteo.

These are model-derived current conditions, not guaranteed ground-station observations.
"""
from __future__ import annotations

import os

import requests
import streamlit as st

FREE_API_URL = "https://api.open-meteo.com/v1/forecast"
COMMERCIAL_API_URL = "https://customer-api.open-meteo.com/v1/forecast"


def _get_api_key() -> str | None:
    key = os.getenv("OPEN_METEO_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("OPEN_METEO_API_KEY")
    except Exception:
        return None


def commercial_api_configured() -> bool:
    return bool(_get_api_key())

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
    api_key = _get_api_key()
    api_url = COMMERCIAL_API_URL if api_key else FREE_API_URL
    if api_key:
        params["apikey"] = api_key
    response = requests.get(api_url, params=params, timeout=20)
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
    current["source"] = "Open-Meteo commercial API" if api_key else "Open-Meteo free evaluation API"
    return current



@st.cache_data(ttl=30 * 60, show_spinner=False)
def get_weather_forecast(latitude: float, longitude: float) -> dict:
    """Fetch a seven-day model forecast and 24-hour hourly outlook."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,cloud_cover",
        "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max,sunrise,sunset,uv_index_max",
        "forecast_days": 7,
        "forecast_hours": 24,
        "timezone": "auto",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }
    api_key = _get_api_key()
    api_url = COMMERCIAL_API_URL if api_key else FREE_API_URL
    if api_key:
        params["apikey"] = api_key
    response = requests.get(api_url, params=params, timeout=25)
    response.raise_for_status()
    payload = response.json()
    daily = payload.get("daily")
    hourly = payload.get("hourly")
    if not isinstance(daily, dict) or not daily.get("time"):
        raise ValueError("The weather provider returned no daily forecast.")
    if not isinstance(hourly, dict) or not hourly.get("time"):
        raise ValueError("The weather provider returned no hourly forecast.")
    return {
        "daily": daily,
        "hourly": hourly,
        "timezone": payload.get("timezone", "Local time"),
        "source": "Open-Meteo commercial API" if api_key else "Open-Meteo free evaluation API",
        "forecast_generated_at": payload.get("current", {}).get("time", "Unavailable"),
    }



@st.cache_data(ttl=20 * 60, show_spinner=False)
def get_national_weather_snapshot(region_records: tuple[tuple[str, float, float], ...]) -> list[dict]:
    """Fetch one cached multi-location snapshot for the mapped Pakistan city directory."""
    api_key = _get_api_key()
    api_url = COMMERCIAL_API_URL if api_key else FREE_API_URL
    records = []
    for start in range(0, len(region_records), 40):
        chunk = region_records[start:start + 40]
        params = {
            "latitude": ",".join(str(item[1]) for item in chunk),
            "longitude": ",".join(str(item[2]) for item in chunk),
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        }
        if api_key:
            params["apikey"] = api_key
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list) or len(payload) != len(chunk):
            raise ValueError("The weather provider returned an incomplete multi-city snapshot.")
        for (city, latitude, longitude), item in zip(chunk, payload):
            current = item.get("current", {}) if isinstance(item, dict) else {}
            if not current:
                continue
            records.append({
                "city": city,
                "latitude": latitude,
                "longitude": longitude,
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation"),
                "wind_speed": current.get("wind_speed_10m"),
                "weather_code": current.get("weather_code"),
                "condition": WEATHER_CODES.get(current.get("weather_code"), "Conditions unavailable"),
                "provider_time": current.get("time"),
                "timezone": item.get("timezone", "Local time"),
            })
    if not records:
        raise ValueError("No city weather records were returned.")
    return records

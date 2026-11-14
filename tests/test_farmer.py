"""Farmer crop-planting guide (2026-11-14): pure logic, no network.

Verdicts come from real numbers only — the calendar month, the 7-day
forecast (min/max, rain, frost/heat) and, when loaded, the NASA POWER
monthly history. Windows are the conservative core of the season.
"""
from datetime import date

import pandas as pd

from src.farmer import CROPS, crop_planting_guide


def _forecast(days, start_day=14):
    """days: list of (tmax, tmin, rain_mm). Dates run from 2026-11-14."""
    return {"daily": {
        "time": [f"2026-11-{start_day + i:02d}" for i in range(len(days))],
        "temperature_2m_max": [d[0] for d in days],
        "temperature_2m_min": [d[1] for d in days],
        "precipitation_sum": [d[2] for d in days],
        "weather_code": [0 for _ in days],
    }}


def _mild_week():
    return _forecast([(28, 14, 0), (29, 15, 0), (27, 13, 0), (28, 14, 0),
                      (26, 12, 0), (27, 13, 0), (28, 14, 0)])


def _by_key(guide):
    return {c["key"]: c for c in guide["crops"]}


def test_eight_crops_covered():
    keys = {c["key"] for c in CROPS}
    assert keys == {"wheat", "rice", "cotton", "maize", "sugarcane",
                    "onion", "tomato", "potato"}
    for crop in CROPS:
        assert crop["window"] and crop["window_text"] and crop["note"]


def test_november_wheat_and_potato_in_season():
    guide = crop_planting_guide(_mild_week(), today=date(2026, 11, 14))
    assert guide["status"] == "ok"
    crops = _by_key(guide)
    assert crops["wheat"]["status"] == "sow_now"
    assert crops["potato"]["status"] == "sow_now"
    assert crops["onion"]["status"] == "sow_now"
    assert "window is open" in crops["wheat"]["reason"]
    assert guide["summary"]["sow_now"] >= 3


def test_november_rice_and_cotton_not_in_season():
    guide = crop_planting_guide(_mild_week(), today=date(2026, 11, 14))
    crops = _by_key(guide)
    # Windows closed months ago — the guide says wait, not "sow now".
    assert crops["rice"]["status"] in ("too_late", "wait")
    assert crops["cotton"]["status"] in ("too_late", "wait")


def test_september_rice_just_missed_is_too_late():
    guide = crop_planting_guide(_mild_week(), today=date(2026, 9, 14))
    crops = _by_key(guide)
    assert crops["rice"]["status"] == "too_late"
    assert "has closed" in crops["rice"]["reason"]


def test_june_rice_and_sugarcane_in_season():
    june = _forecast([(36, 26, 0), (37, 27, 2), (35, 26, 0), (36, 27, 0),
                      (38, 28, 0), (37, 27, 0), (36, 26, 0)], start_day=10)
    # Dates are June-shaped for the test via today=June; forecast shape only.
    guide = crop_planting_guide(june, today=date(2026, 6, 14))
    crops = _by_key(guide)
    assert crops["rice"]["status"] == "sow_now"
    assert crops["wheat"]["status"] == "wait"


def test_september_wheat_coming_soon():
    guide = crop_planting_guide(_mild_week(), today=date(2026, 9, 1))
    crops = _by_key(guide)
    assert crops["wheat"]["status"] == "coming_soon"
    assert "next month" in crops["wheat"]["reason"]


def test_frost_warning_attached_to_sowing_crop():
    frosty = _forecast([(12, 1, 0), (13, 0, 0), (14, 2, 0), (15, 5, 0),
                        (16, 6, 0), (15, 4, 0), (14, 3, 0)])
    guide = crop_planting_guide(frosty, today=date(2026, 11, 14))
    wheat = _by_key(guide)["wheat"]
    assert wheat["status"] == "sow_now"
    assert any("Frost" in w for w in wheat["watch"])
    assert guide["frost_days"] == 3


def test_heat_warning_attached():
    hot = _forecast([(41, 24, 0), (42, 25, 0), (40, 24, 0), (39, 23, 0),
                     (38, 23, 0), (37, 22, 0), (36, 22, 0)])
    guide = crop_planting_guide(hot, today=date(2026, 11, 14))
    wheat = _by_key(guide)["wheat"]
    assert any("Heat" in w for w in wheat["watch"])


def test_heavy_rain_warning_attached():
    wet = _forecast([(26, 15, 25), (27, 16, 0), (26, 15, 0), (27, 16, 0),
                     (28, 16, 0), (27, 15, 0), (26, 15, 0)])
    guide = crop_planting_guide(wet, today=date(2026, 11, 14))
    assert guide["heavy_rain_days"] == 1
    assert any("Heavy rain" in w for w in _by_key(guide)["wheat"]["watch"])


def test_typical_month_temp_from_history():
    monthly = pd.DataFrame({
        "date": pd.to_datetime(["2023-11-01", "2024-11-01", "2025-11-01",
                                "2024-06-01"]),
        "T2M": [22.0, 24.0, 23.0, 32.0],
        "month": [11, 11, 11, 6],
    })
    guide = crop_planting_guide(_mild_week(), monthly=monthly,
                                variable="T2M", today=date(2026, 11, 14))
    assert guide["typical_month_temp_c"] == 23.0


def test_missing_forecast_is_unavailable():
    assert crop_planting_guide(None)["status"] == "unavailable"
    assert crop_planting_guide({})["status"] == "unavailable"
    assert crop_planting_guide({"daily": {}})["status"] == "unavailable"


def test_disclaimer_present():
    guide = crop_planting_guide(_mild_week(), today=date(2026, 11, 14))
    assert "not agronomy advice" in guide["disclaimer"]
    assert "agriculture department" in guide["disclaimer"]

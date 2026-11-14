"""Daily advisories (2026-11-14): pure-logic tests, no network, no Streamlit.

Covers the three new features — health verdict, farmer advisory and rain
warning — including missing-data handling (never raises, reports
'unavailable') and the exact thresholds the app documents.
"""
from src.advisory import (
    advisory_summary,
    daily_health_verdict,
    farmer_advisory,
    rain_warning,
)


def _weather(temp=26.0, apparent=27.0, humidity=50.0):
    return {"temperature_2m": temp, "apparent_temperature": apparent,
            "relative_humidity_2m": humidity}


def _aqi(us_aqi=40, pm25=12.0):
    return {"current": {"us_aqi": us_aqi, "pm2_5": pm25},
            "aqi_label": "Good", "dominant_pollutant": "PM2.5"}


def _forecast(days):
    """days: list of (tmax, tmin, rain_mm, rain_prob, wind_max)."""
    return {"daily": {
        "time": [f"2026-11-{14 + i:02d}" for i in range(len(days))],
        "temperature_2m_max": [d[0] for d in days],
        "temperature_2m_min": [d[1] for d in days],
        "precipitation_sum": [d[2] for d in days],
        "precipitation_probability_max": [d[3] for d in days],
        "wind_speed_10m_max": [d[4] for d in days],
        "weather_code": [0 for _ in days],
    }}


# ---------- health verdict ----------

def test_health_good_day():
    v = daily_health_verdict(_weather(), _aqi())
    assert v["status"] == "ok"
    assert v["score"] <= 2
    assert v["label"] == "Good day"
    assert any("outdoor activity" in a for a in v["actions"])


def test_health_smog_day_is_be_careful():
    # Lahore smog morning: AQI 158 Unhealthy, mild heat.
    v = daily_health_verdict(_weather(26.0, 27.6, 52.0), _aqi(158, 47.3))
    assert v["status"] == "ok"
    assert v["label"] == "Be careful today"
    assert any("mask" in a.lower() for a in v["actions"])
    assert any("Children" in a for a in v["actions"])
    assert "US AQI 158" in v["factors"][0]


def test_health_extreme_heat_and_smog_is_worst():
    v = daily_health_verdict(_weather(44.0, 46.0, 60.0), _aqi(320, 180.0))
    assert v["label"] == "Stay indoors if you can"
    assert v["score"] == 10
    assert any("midday sun" in a for a in v["actions"])


def test_health_humid_heat_adds_a_point():
    dry = daily_health_verdict(_weather(32.0, 33.0, 40.0), _aqi(40))
    humid = daily_health_verdict(_weather(32.0, 33.0, 80.0), _aqi(40))
    assert humid["score"] == dry["score"] + 1


def test_health_missing_everything_is_unavailable():
    assert daily_health_verdict(None, None)["status"] == "unavailable"
    assert daily_health_verdict({}, {})["status"] == "unavailable"


def test_health_works_with_aqi_only():
    v = daily_health_verdict(None, _aqi(158, 47.3))
    assert v["status"] == "ok"
    assert v["label"] == "Be careful today"


# ---------- farmer advisory ----------

def test_farmer_rain_in_48h_holds_irrigation():
    fc = _forecast([(28, 18, 8.0, 80, 10), (27, 17, 0.0, 20, 10),
                    (26, 16, 0.0, 10, 10), (26, 16, 0.0, 10, 10),
                    (27, 17, 0.0, 10, 10), (28, 18, 0.0, 10, 10),
                    (28, 18, 0.0, 10, 10)])
    adv = farmer_advisory(fc)
    assert adv["status"] == "ok"
    assert any("Hold off irrigation" in it["title"] for it in adv["items"])
    assert adv["week_rain_mm"] == 8.0


def test_farmer_dry_hot_week_says_irrigate():
    fc = _forecast([(38, 24, 0.0, 5, 10)] * 7)
    adv = farmer_advisory(fc)
    assert any("Dry week" in it["title"] for it in adv["items"])
    assert any("morning or in the evening" in it["detail"] for it in adv["items"])


def test_farmer_heavy_rain_frost_wind_heat_flagged():
    fc = _forecast([(30, 18, 25.0, 90, 10), (28, 1, 0.0, 10, 45),
                    (41, 25, 0.0, 10, 10), (27, 17, 0.0, 10, 10),
                    (27, 17, 0.0, 10, 10), (27, 17, 0.0, 10, 10),
                    (27, 17, 0.0, 10, 10)])
    adv = farmer_advisory(fc)
    titles = [it["title"] for it in adv["items"]]
    assert any("Heavy rain" in t for t in titles)
    assert any("Frost risk" in t for t in titles)
    assert any("Strong wind" in t for t in titles)
    assert any("Heat stress" in t for t in titles)
    assert all(it["level"] == "warning" for it in adv["items"]
               if "Heavy rain" in it["title"] or "Frost" in it["title"])


def test_farmer_good_window_found():
    fc = _forecast([(28, 18, 6.0, 80, 10), (26, 16, 0.0, 10, 10),
                    (27, 17, 0.0, 10, 10), (27, 17, 0.0, 10, 10),
                    (27, 17, 0.0, 10, 10), (27, 17, 0.0, 10, 10),
                    (27, 17, 0.0, 10, 10)])
    adv = farmer_advisory(fc)
    assert any("Good window" in it["title"] for it in adv["items"])


def test_farmer_missing_forecast_is_unavailable():
    assert farmer_advisory(None)["status"] == "unavailable"
    assert farmer_advisory({})["status"] == "unavailable"
    assert farmer_advisory({"daily": {}})["status"] == "unavailable"


# ---------- rain warning ----------

def test_rain_no_rain():
    fc = _forecast([(28, 18, 0.0, 5, 10)] * 7)
    w = rain_warning(fc)
    assert w["status"] == "ok"
    assert w["level"] == "none"
    assert w["total_mm"] == 0.0
    assert w["heavy_days"] == 0
    assert "No heavy rain" in w["advice"]


def test_rain_heavy_day_found():
    fc = _forecast([(28, 18, 0.0, 5, 10), (27, 17, 32.0, 90, 10),
                    (27, 17, 2.0, 20, 10), (27, 17, 0.0, 10, 10),
                    (27, 17, 0.0, 10, 10), (27, 17, 0.0, 10, 10),
                    (27, 17, 0.0, 10, 10)])
    w = rain_warning(fc)
    assert w["level"] == "heavy"
    assert w["worst_mm"] == 32.0
    assert w["heavy_days"] == 1
    assert w["total_mm"] == 34.0
    assert "clear drains" in w["advice"]


def test_rain_very_heavy_day():
    fc = _forecast([(28, 18, 65.0, 95, 10)] + [(27, 17, 0.0, 10, 10)] * 6)
    w = rain_warning(fc)
    assert w["level"] == "very heavy"
    assert "PMD" in w["advice"]


def test_rain_missing_forecast_is_unavailable():
    assert rain_warning(None)["status"] == "unavailable"
    assert rain_warning({"daily": {"time": []}})["status"] == "unavailable"


# ---------- overview teaser ----------

def test_advisory_summary_combines_both():
    fc = _forecast([(28, 18, 0.0, 5, 10)] * 7)
    s = advisory_summary(_weather(26.0, 27.6, 52.0), _aqi(158, 47.3), fc)
    assert s is not None
    assert s["health_label"] == "Be careful today"
    assert s["rain_label"] == "No heavy rain"
    assert s["rain_total_mm"] == 0.0


def test_advisory_summary_none_when_nothing_available():
    assert advisory_summary(None, None, None) is None

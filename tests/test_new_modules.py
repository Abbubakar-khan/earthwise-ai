import pandas as pd
from src.air_quality import aqi_category, dominant_pollutant
from src.risk import compute_risk, project_trend, risk_level
from src.ai_assistant import answer_question
from src.statistics import analyze_trend


def test_aqi_bands():
    assert aqi_category(25)[0] == "Good"
    assert aqi_category(175)[0] == "Unhealthy"
    assert aqi_category(None)[0] == "Unknown"


def test_dominant_pollutant():
    assert dominant_pollutant({"pm2_5": 67.8, "pm10": 10.0, "ozone": 20.0, "nitrogen_dioxide": 5.0}) == "PM2.5"


def test_risk_from_real_trend():
    dates = pd.date_range("2000-01-01", periods=60, freq="MS")
    monthly = pd.DataFrame({"date": dates, "x": range(60)})
    trend = analyze_trend(monthly, "x")
    risk = compute_risk(monthly, "T2M", trend, latest_anomaly=1.5, current_temp=38.0, us_aqi=175)
    assert risk["composite"] is not None and 0 <= risk["composite"] <= 100
    assert risk["composite_label"] in ("Low", "Moderate", "High", "Very high")
    assert risk_level(10) == "Low" and risk_level(90) == "Very high"


def test_projection_is_linear_extrapolation():
    dates = pd.date_range("2000-01-01", periods=60, freq="MS")
    monthly = pd.DataFrame({"date": dates, "x": [float(i) for i in range(60)]})
    trend = analyze_trend(monthly, "x")
    proj, note = project_trend(monthly, "x", trend, years_ahead=5)
    assert len(proj) == 5
    assert "extrapolation" in note.lower()
    assert proj["projected"].iloc[-1] > proj["projected"].iloc[0]


def test_assistant_answers_only_from_context():
    ctx = {"city": "Lahore", "weather": {"temperature_2m": 19.4, "apparent_temperature": 20.0,
           "relative_humidity_2m": 69, "wind_speed_10m": 5.0, "precipitation": 0.0,
           "condition_text": "Clear sky"},
           "air_quality": {"current": {"us_aqi": 175, "pm2_5": 67.8, "pm10": 77.8, "ozone": 20.0,
                            "nitrogen_dioxide": 56.4}, "aqi_label": "Unhealthy",
                            "aqi_advice": "Reduce exertion.", "dominant_pollutant": "PM2.5"},
           "trend": {"status": "ok", "direction": "increasing", "sen_slope_per_decade": 0.3,
                     "p_value": 0.01, "significant_005": True, "first_month": "2001-01-01",
                     "last_month": "2025-12-01", "n": 300},
           "variable_label": "Mean Air Temperature", "unit": "°C",
           "latest_anomaly": 1.2, "risk": {"composite": 62.0, "composite_label": "High", "scores": {}},
           "forecast_summary": None}
    assert "175" in answer_question("What is the air quality?", ctx)
    assert "increasing" in answer_question("What is the trend?", ctx)
    assert "19.4" in answer_question("What is the weather now?", ctx)
    # Missing data -> says so, does not invent
    assert "don't have" in answer_question("What is the air quality?", {"city": "Lahore", "air_quality": {}})

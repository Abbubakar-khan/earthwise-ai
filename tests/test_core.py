import pandas as pd
from src.cleaning import monthly_aggregate
from src.statistics import analyze_trend

def test_monthly_temperature_mean():
    df = pd.DataFrame({"date": pd.to_datetime(["2020-01-01","2020-01-02"]),
                       "T2M": [10.0, 20.0]})
    out = monthly_aggregate(df, "T2M")
    assert out.loc[0, "T2M"] == 15.0

def test_monthly_precipitation_sum():
    df = pd.DataFrame({"date": pd.to_datetime(["2020-01-01","2020-01-02"]),
                       "PRECTOTCORR": [2.0, 3.0]})
    out = monthly_aggregate(df, "PRECTOTCORR")
    assert out.loc[0, "PRECTOTCORR"] == 5.0

def test_upward_trend_detected():
    dates = pd.date_range("2000-01-01", periods=60, freq="MS")
    df = pd.DataFrame({"date": dates, "x": range(60)})
    result = analyze_trend(df, "x")
    assert result["status"] == "ok"
    assert result["direction"] == "increasing"
    assert result["sen_slope_per_decade"] > 0



def test_constant_series_has_unavailable_significance_not_crash():
    from src.ai_engine import explain_result

    dates = pd.date_range("2000-01-01", periods=60, freq="MS")
    df = pd.DataFrame({"date": dates, "x": [5.0] * 60})
    result = analyze_trend(df, "x")
    assert result["status"] == "ok"
    assert result["p_value"] is None
    explanation = explain_result("Lahore", "Temperature", "°C", result)
    assert "unavailable" in explanation
    assert "not statistically testable" in explanation

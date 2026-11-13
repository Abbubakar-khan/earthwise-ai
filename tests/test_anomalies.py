import pandas as pd
from src.anomalies import seasonal_anomalies

def test_seasonal_anomaly_compares_same_calendar_months():
    monthly = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-01", "2021-01-01", "2020-02-01", "2021-02-01"]),
        "T2M": [10.0, 14.0, 20.0, 24.0],
    })
    result = seasonal_anomalies(monthly, "T2M")
    january = result[result["month"] == 1].sort_values("year")
    february = result[result["month"] == 2].sort_values("year")
    assert january["climatology"].tolist() == [12.0, 12.0]
    assert january["anomaly"].tolist() == [-2.0, 2.0]
    assert february["anomaly"].tolist() == [-2.0, 2.0]

def test_seasonal_anomaly_handles_single_year_without_z_score():
    monthly = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-01", "2020-02-01"]),
        "PRECTOTCORR": [5.0, 9.0],
    })
    result = seasonal_anomalies(monthly, "PRECTOTCORR")
    assert result["anomaly"].tolist() == [0.0, 0.0]
    assert result["standardized_anomaly"].isna().all()

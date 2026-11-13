import pandas as pd

from src.climate_fingerprint import build_climate_fingerprint


def test_fingerprint_compares_same_calendar_months():
    dates = pd.date_range("2020-01-01", periods=36, freq="MS")
    values = []
    for date in dates:
        seasonal_base = 10 + date.month
        year_effect = date.year - 2020
        values.append(seasonal_base + year_effect)
    frame = pd.DataFrame({"date": dates, "T2M": values})

    result = build_climate_fingerprint(frame, "T2M")

    assert list(result.index) == [2020, 2021, 2022]
    assert list(result.columns) == [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    assert result.loc[2020, "Jan"] < result.loc[2021, "Jan"] < result.loc[2022, "Jan"]


def test_fingerprint_requires_three_years():
    dates = pd.date_range("2021-01-01", periods=24, freq="MS")
    frame = pd.DataFrame({"date": dates, "T2M": range(24)})

    assert build_climate_fingerprint(frame, "T2M").empty


def test_fingerprint_leaves_constant_months_blank():
    dates = pd.date_range("2020-01-01", periods=36, freq="MS")
    frame = pd.DataFrame({"date": dates, "T2M": [5.0] * len(dates)})

    result = build_climate_fingerprint(frame, "T2M")

    assert result.isna().all().all()

"""Climate story (2026-11-14): pure logic, no Streamlit, no network.

The honest-words rule is tested hardest: a non-significant trend must
never be called warming or cooling.
"""
import pandas as pd
import pytest

from src.story import climate_story


def _trend(slope=-1.34, p=0.52, n=132, direction="decreasing",
           first="2015-01-01", last="2025-12-01"):
    return {"status": "ok", "n": n, "direction": direction,
            "sen_slope_per_decade": slope, "p_value": p,
            "significant_005": bool(p < 0.05),
            "first_month": first, "last_month": last}


def _monthly():
    # 11 years of monthly T2M: June hottest (~35), January coldest (~12).
    rows = []
    for year in range(2015, 2026):
        for month in range(1, 13):
            base = {1: 12.0, 2: 15.0, 3: 21.0, 4: 27.0, 5: 32.0, 6: 35.0,
                    7: 33.0, 8: 32.0, 9: 30.0, 10: 26.0, 11: 19.0, 12: 14.0}[month]
            rows.append({"date": pd.Timestamp(year, month, 1),
                         "T2M": base + (year - 2015) * -0.01, "month": month})
    return pd.DataFrame(rows)


def test_lahore_case_never_claims_warming_or_cooling():
    s = climate_story("Lahore", "T2M", "Mean Air Temperature", "°C",
                      _trend(), _monthly())
    assert s["status"] == "ok"
    assert s["significant"] is False
    assert "not statistically significant" in s["line"]
    assert "do not show a clear" in s["line"]
    assert "1.3" in s["line"]  # |−1.34| °C/decade
    assert "2015–2025" in s["line"]
    # Must not call it warming or cooling.
    assert "warming" not in s["line"].lower()
    assert "cooling" not in s["line"].lower()
    assert "June" in s["detail"] and "January" in s["detail"]
    assert "132 monthly observations" in s["detail"]


def test_significant_warming_says_so_plainly():
    s = climate_story("Karachi", "T2M", "Mean Air Temperature", "°C",
                      _trend(slope=2.1, p=0.01, direction="increasing"), _monthly())
    assert s["status"] == "ok"
    assert s["significant"] is True
    assert "statistically significant warming trend" in s["line"]
    assert "2.1" in s["line"]


def test_significant_cooling_says_so_plainly():
    s = climate_story("Murree", "T2M", "Mean Air Temperature", "°C",
                      _trend(slope=-3.1, p=0.004, direction="decreasing"), _monthly())
    assert s["significant"] is True
    assert "statistically significant cooling trend" in s["line"]


def test_unavailable_when_trend_is_not_ok():
    assert climate_story("Lahore", "T2M", "Mean Air Temperature", "°C",
                         {"status": "insufficient", "n": 5}, _monthly())["status"] == "unavailable"
    assert climate_story("Lahore", "T2M", "Mean Air Temperature", "°C",
                         None, _monthly())["status"] == "unavailable"
    assert climate_story("Lahore", "T2M", "Mean Air Temperature", "°C",
                         _trend(slope=None), _monthly())["status"] == "unavailable"


def test_story_works_without_monthly_table():
    s = climate_story("Lahore", "T2M", "Mean Air Temperature", "°C",
                      _trend(), monthly=None)
    assert s["status"] == "ok"
    assert "132 monthly observations" in s["detail"]
    assert "hottest" not in s["detail"]


def test_precipitation_uses_wettest_driest_words():
    rows = []
    for year in range(2015, 2026):
        for month in range(1, 13):
            val = {1: 20.0, 2: 25.0, 3: 30.0, 4: 20.0, 5: 15.0, 6: 25.0,
                   7: 120.0, 8: 100.0, 9: 60.0, 10: 10.0, 11: 5.0, 12: 12.0}[month]
            rows.append({"date": pd.Timestamp(year, month, 1),
                         "PRECTOTCORR": val, "month": month})
    monthly = pd.DataFrame(rows)
    s = climate_story("Lahore", "PRECTOTCORR", "Precipitation", "mm/month",
                      _trend(slope=42.0, p=0.3, direction="increasing"), monthly)
    assert s["status"] == "ok"
    assert "wettest" in s["detail"] and "driest" in s["detail"]
    assert "July" in s["detail"] and "November" in s["detail"]
    assert "hottest" not in s["detail"]


def test_tiny_slope_is_called_no_clear_trend():
    s = climate_story("Lahore", "T2M", "Mean Air Temperature", "°C",
                      _trend(slope=-0.001, p=0.9, direction="approximately stable"), _monthly())
    assert s["status"] == "ok"
    assert "changed very little" in s["line"]

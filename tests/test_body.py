"""Body & weather (2026-11-14): pure-logic tests, no network, no Streamlit.

Covers the heart/body strain curve, the current-strain verdict and the
best-hours planner, including missing-data handling (never raises).
"""
from src.body import best_hours, current_strain, hourly_strain


def _hourly(temps, precips=None, probs=None):
    n = len(temps)
    return {
        "time": [f"2026-11-14T{h:02d}:00" for h in range(n)],
        "temperature_2m": temps,
        "precipitation": precips if precips is not None else [0.0] * n,
        "precipitation_probability": probs if probs is not None else [0] * n,
    }


def _weather(temp=26.0, apparent=27.0, humidity=50.0):
    return {"temperature_2m": temp, "apparent_temperature": apparent,
            "relative_humidity_2m": humidity}


def _aqi(us_aqi=40):
    return {"current": {"us_aqi": us_aqi}, "aqi_label": "Good"}


# ---------- hourly strain curve ----------

def test_strain_cool_morning_low_hot_afternoon_high():
    temps = [22, 24, 28, 33, 38, 41, 39, 34, 29, 25] + [24] * 14
    r = hourly_strain(_hourly(temps))
    assert r["status"] == "ok"
    assert len(r["hours"]) == 24
    assert r["hours"][0]["strain"] <= 2
    assert r["hours"][5]["strain"] >= 7
    assert r["peak"]["time"] == "05:00"  # 41 C is the hottest hour
    assert r["peak"]["strain"] >= 7


def test_strain_smog_adds_load():
    temps = [26] * 24
    clean = hourly_strain(_hourly(temps), us_aqi=40)
    smoggy = hourly_strain(_hourly(temps), us_aqi=180)
    assert smoggy["hours"][0]["strain"] == clean["hours"][0]["strain"] + 2


def test_strain_capped_at_ten():
    temps = [46] * 24
    r = hourly_strain(_hourly(temps), humidity=90, us_aqi=320)
    assert all(h["strain"] <= 10 for h in r["hours"])


def test_strain_missing_hourly_is_unavailable():
    assert hourly_strain(None)["status"] == "unavailable"
    assert hourly_strain({})["status"] == "unavailable"
    assert hourly_strain({"time": []})["status"] == "unavailable"


# ---------- current strain ----------

def test_current_strain_easy_day():
    s = current_strain(_weather(24.0, 25.0, 45.0), _aqi(35))
    assert s["status"] == "ok"
    assert s["score"] <= 2
    assert s["label"] == "Easy on the body"


def test_current_strain_smog_and_heat_is_very_hard():
    s = current_strain(_weather(38.0, 44.0, 60.0), _aqi(220))
    assert s["status"] == "ok"
    assert s["label"] == "Very hard — take care"
    assert any("mask" in a.lower() for a in s["advice"])


def test_current_strain_missing_everything_is_unavailable():
    assert current_strain(None, None)["status"] == "unavailable"
    assert current_strain({}, {})["status"] == "unavailable"


def test_current_strain_works_with_aqi_only():
    s = current_strain(None, _aqi(180))
    assert s["status"] == "ok"
    assert s["score"] >= 2


# ---------- best hours ----------

def test_best_hours_picks_cool_dry_morning():
    # Hot midday, cool dry morning, rainy evening.
    temps = [26, 25, 24, 24, 25, 26, 27, 29, 33, 36, 38, 40, 39, 37, 34, 31, 28, 26, 25, 24, 23, 22, 21, 21]
    precips = [0.0] * 16 + [3.0] * 8
    probs = [5] * 16 + [80] * 8
    r = best_hours(_hourly(temps, precips, probs), us_aqi=40)
    assert r["status"] == "ok"
    assert r["best"][0]["time"] in ("06:00", "07:00")
    assert all(b["score"] >= 6 for b in r["best"])
    assert r["avoid"], "the rainy evening should be listed to avoid"


def test_best_hours_only_daytime():
    temps = [18] * 24
    r = best_hours(_hourly(temps), us_aqi=40)
    assert all(6 <= int(b["time"].split(":")[0]) <= 20 for b in r["best"])
    assert all(6 <= int(a["time"].split(":")[0]) <= 20 for a in r["avoid"])


def test_best_hours_missing_hourly_is_unavailable():
    assert best_hours(None)["status"] == "unavailable"
    assert best_hours({})["status"] == "unavailable"

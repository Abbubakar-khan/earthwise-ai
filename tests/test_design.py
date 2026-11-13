"""Professional design fix (2026-11-14): hero live panel, forecast strip,
demo-dataset default. Pure helpers from src/animations.py only — no
Streamlit import, no network.
"""
from src.animations import DESIGN_CSS, demo_is_default, forecast_cards_html, hero_now_html


def _weather():
    return {"temperature_2m": 19.2, "apparent_temperature": 19.5,
            "relative_humidity_2m": 70, "wind_speed_10m": 6.1,
            "weather_code": 0, "condition_text": "Clear sky",
            "provider_time": "2026-11-14T01:30"}


def _aqi():
    return {"current": {"us_aqi": 173, "pm2_5": 62.4},
            "aqi_label": "Unhealthy"}


def _daily(n=7):
    return {
        "time": [f"2026-11-{14 + i:02d}" for i in range(n)],
        "weather_code": [0] * n,
        "temperature_2m_max": [24.0] * n,
        "temperature_2m_min": [12.0] * n,
        "precipitation_probability_max": [16] * n,
        "precipitation_sum": [0.0] * n,
        "wind_speed_10m_max": [11.0] * n,
        "uv_index_max": [3.2] * n,
    }


def test_hero_now_shows_real_values():
    html_out = hero_now_html(_weather(), _aqi())
    assert "19.2°" in html_out
    assert "Clear sky" in html_out
    assert "19.5" in html_out  # feels-like
    assert "70%" in html_out
    assert "6.1 km/h" in html_out
    assert "173" in html_out
    assert "Unhealthy" in html_out


def test_hero_now_empty_without_live_weather():
    assert hero_now_html(None, _aqi()) == ""
    assert hero_now_html({}, _aqi()) == ""
    assert hero_now_html({"temperature_2m": None}, _aqi()) == ""


def test_hero_now_escapes_html():
    w = _weather()
    w["condition_text"] = "<script>alert(1)</script>"
    out = hero_now_html(w, None)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_forecast_grid_has_seven_cards_one_row():
    out = forecast_cards_html(_daily(7))
    assert out.count("ew-fc\"") == 7 or out.count('class="ew-fc"') == 7
    assert "ew-forecast-grid" in out
    assert "24°" in out and "12°" in out
    assert "Rain 16%" in out


def test_forecast_grid_handles_missing_data():
    assert forecast_cards_html(None) == ""
    assert forecast_cards_html({}) == ""
    assert forecast_cards_html({"time": []}) == ""
    out = forecast_cards_html(_daily(3))
    assert out.count('class="ew-fc"') == 3


def test_demo_is_default_only_lahore_t2m():
    assert demo_is_default("Lahore", "T2M") is True
    assert demo_is_default("Karachi", "T2M") is False
    assert demo_is_default("Lahore", "RH2M") is False
    assert demo_is_default("Lahore", "PRECTOTCORR") is False


def test_design_css_has_grid_header_and_mobile_rules():
    assert "ew-forecast-grid" in DESIGN_CSS
    assert "repeat(7,1fr)" in DESIGN_CSS
    assert "repeat(2,1fr)" in DESIGN_CSS
    assert "padding-top:3.4rem" in DESIGN_CSS
    assert "ew-hero-right" in DESIGN_CSS
    assert "ew-empty" in DESIGN_CSS
    assert "ew-stat-value" in DESIGN_CSS

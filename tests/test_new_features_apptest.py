"""Live visuals + Pakistan map + farmer guide (2026-11-14): AppTest, real
app runs. One module-scoped fixture; the first run does live Open-Meteo /
CAMS fetches, so the timeout is generous.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "main.py")


@pytest.fixture(scope="module")
def app():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    assert not at.exception, f"app raised on first load: {at.exception}"
    return at


def test_overview_live_weather_scene_renders(app):
    scenes = [m for m in app.markdown if "wx-scene" in m.value]
    assert scenes, "live weather scene missing on Overview"
    # The scene shows the real live condition + temperature.
    assert "wx-scene-temp" in scenes[0].value
    assert "wx-scene-cond" in scenes[0].value


def test_weather_page_map_tab_and_picker_load_a_place(app):
    app.button(key="nav_Weather & Maps").click().run()
    assert not app.exception
    assert app.session_state["page"] == "Weather & Maps"
    # The tap-to-load map is rendered (Plotly chart with the map key).
    # (Streamlit 1.63 AppTest has no .plotly_chart accessor — use .get.)
    _charts = app.get("plotly_chart")
    assert any(getattr(c, "key", None) == "pakistan_map" for c in _charts), \
        "Pakistan map chart missing on Weather & Maps"
    # Fallback picker: choose Multan, load it, whole app switches city.
    app.selectbox(key="map_city_pick").set_value("Multan").run()
    app.button(key="map_load").click().run()
    assert not app.exception, f"loading Multan raised: {app.exception}"
    assert app.session_state["City"] == "Multan"
    assert app.session_state["city_main"] == "Multan"
    # Overview for the new place still renders its live scene.
    app.button(key="nav_Overview").click().run()
    assert not app.exception
    assert any("wx-scene" in m.value for m in app.markdown)
    # Back to Lahore for the other tests in this module.
    app.selectbox(key="City").set_value("Lahore").run()
    assert app.session_state["City"] == "Lahore"


def test_daily_advisory_crop_guide_renders(app):
    app.button(key="nav_Daily Advisory").click().run()
    assert not app.exception
    assert app.session_state["page"] == "Daily Advisory"
    text = " ".join(m.value for m in app.markdown)
    assert "Crop planting guide" in text
    assert "Wheat" in text
    assert "Rice" in text
    # The disclaimer is an st.caption, not markdown, in AppTest.
    _captions = " ".join(c.value for c in app.caption)
    assert "not agronomy advice" in _captions
    # November in Lahore: wheat is in season.
    assert "Sow now" in text

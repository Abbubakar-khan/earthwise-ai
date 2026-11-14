"""UI polish + wow features (2026-11-14): AppTest, real app runs. One
module-scoped fixture; the first run does live Open-Meteo / CAMS fetches,
so the timeout is generous.

Test order matters: the intro splash only paints on the FIRST run of the
session, so the splash test is first. The provenance and story assertions
are written to hold even when a live fetch fails (rows show "unavailable",
the story comes from the local demo dataset), so a rate-limited Open-Meteo
does not fake-fail them.
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


def _all_markdown(app):
    return " ".join(m.value for m in app.markdown)


def test_intro_splash_paints_on_first_load_with_real_stages(app):
    # First run only: the splash is rendered in the same first run.
    assert any("ew-intro" in m.value for m in app.markdown), \
        "intro splash missing on first load"
    text = _all_markdown(app)
    assert "Connecting to NASA POWER" in text
    assert "Fetching live weather" in text
    assert "Loading 10-year climate history" in text
    assert "ew-intro-ring" in text
    assert "ew-intro-letter" in text


def test_overview_provenance_panel_traces_every_source(app):
    text = _all_markdown(app)
    assert "NASA data provenance" in text
    for name in ("NASA POWER", "Open-Meteo", "CAMS", "NASA GIBS"):
        assert name in text, f"provenance panel missing {name}"
    assert "model estimates" in text
    assert "not station observations" in text
    assert "Source docs" in text


def test_overview_story_in_one_line_is_honest(app):
    text = _all_markdown(app)
    assert "The story in one line" in text
    # Demo dataset is Lahore T2M 2015–2025: decreasing, p = 0.52, NOT
    # significant — the story must say so, never claim warming.
    assert "not statistically significant" in text
    assert "do not show a clear" in text


def test_climate_analytics_story_renders(app):
    app.button(key="nav_Climate Analytics").click().run()
    assert not app.exception
    assert app.session_state["page"] == "Climate Analytics"
    text = _all_markdown(app)
    assert "The story in one line" in text
    assert "not statistically significant" in text
    assert "June" in text and "January" in text  # hottest / coldest month


def test_data_downloads_links_to_provenance_on_overview(app):
    app.button(key="nav_Data & Downloads").click().run()
    assert not app.exception
    assert app.session_state["page"] == "Data & Downloads"
    app.button(key="prov_open").click().run()
    assert not app.exception
    assert app.session_state["page"] == "Overview"
    assert "NASA data provenance" in _all_markdown(app)

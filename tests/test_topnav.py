"""Intro splash + top navigation (2026-11-14): AppTest, real app runs.

Runs the full app once (module-scoped fixture) and then drives it:
- intro splash is present on first load (not only after a rerun),
- a top-nav button exists for every page,
- clicking each top-nav button switches the page AND the sidebar radio
  follows it,
- the sidebar radio still switches pages the other way.

Order matters: the intro assertions run on the fresh fixture, before any
navigation reruns remove the splash from the DOM.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["Overview", "Climate Analytics", "Air Quality", "Weather & Maps",
         "Daily Advisory", "AI Assistant", "Risk & Outlook", "Data & Downloads"]
APP = str(Path(__file__).resolve().parents[1] / "app" / "main.py")


@pytest.fixture(scope="module")
def app():
    # First run does live Open-Meteo / CAMS fetches, so the 3s default
    # AppTest timeout is far too short.
    at = AppTest.from_file(APP, default_timeout=90)
    at.run()
    assert not at.exception, f"app raised on first load: {at.exception}"
    return at


def test_intro_splash_renders_on_first_load(app):
    intro = [m for m in app.markdown if "ew-intro" in m.value]
    assert intro, "intro splash HTML missing on first load"
    assert "ew-intro-letter" in intro[0].value
    assert "ew-intro-title" in intro[0].value
    # The splash is rendered in the same first run as the app (no sleep +
    # rerun), so the header is already there behind it.
    assert any("EARTHWISE" in m.value for m in app.markdown)


def test_top_nav_buttons_exist_for_all_pages(app):
    keys = {b.key for b in app.button if b.key is not None}
    for p in PAGES:
        assert f"nav_{p}" in keys, f"missing top-nav button for {p}"
    assert len([k for k in keys if k.startswith("nav_")]) == 8


def test_top_nav_buttons_switch_pages_and_radio_follows(app):
    for p in PAGES[1:]:
        app.button(key=f"nav_{p}").click().run()
        assert not app.exception, f"navigating to {p} raised: {app.exception}"
        assert app.session_state["page"] == p
        assert app.radio(key="page").value == p


def test_sidebar_radio_still_switches_pages(app):
    app.radio(key="page").set_value("Risk & Outlook").run()
    assert not app.exception
    assert app.session_state["page"] == "Risk & Outlook"
    app.radio(key="page").set_value("Overview").run()
    assert not app.exception
    assert app.session_state["page"] == "Overview"

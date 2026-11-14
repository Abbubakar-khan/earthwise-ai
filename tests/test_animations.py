"""Tests for src/animations.py — pure helpers only, no Streamlit, no network."""
from src.animations import (
    ANIMATION_CSS,
    INTRO_CSS,
    build_ticker_items,
    hero_symbol_html,
    intro_html,
    ticker_html,
    weather_animation_class,
)


def test_weather_animation_class_mapping():
    assert weather_animation_class(0) == "wx-clear"
    assert weather_animation_class(1) == "wx-partly"
    assert weather_animation_class(2) == "wx-partly"
    assert weather_animation_class(3) == "wx-cloud"
    assert weather_animation_class(51) == "wx-rain"
    assert weather_animation_class(71) == "wx-snow"
    assert weather_animation_class(95) == "wx-storm"
    assert weather_animation_class(999) == "wx-partly"
    assert weather_animation_class(None) == "wx-partly"
    assert weather_animation_class("61") == "wx-rain"


def test_ticker_items_use_only_real_values():
    items = build_ticker_items({
        "city": "Lahore", "temperature": 19.4, "condition": "Clear sky",
        "us_aqi": 173, "aqi_label": "Unhealthy", "pm2_5": 67.8,
        "provider_time": "2026-11-14T01:00",
    })
    joined = " | ".join(items)
    assert "Lahore" in joined and "19.4" in joined
    assert "173" in joined and "Unhealthy" in joined
    assert "67.8" in joined and "2026-11-14T01:00" in joined


def test_ticker_items_omit_missing_values_never_invent():
    assert build_ticker_items({})[-1].startswith("Live data")
    assert build_ticker_items(None) == []
    items = build_ticker_items({"city": "Lahore"})
    assert not any("°C" in i for i in items)
    assert not any("AQI" in i for i in items)


def test_ticker_html_duplicates_for_seamless_loop_and_escapes():
    out = ticker_html(["Lahore — 19.4 °C", "US AQI 173"])
    assert out.count("Lahore") == 2  # duplicated set
    assert "ew-ticker-track" in out
    assert ticker_html([]) == ""
    assert "<script>" not in ticker_html(["<script>alert(1)</script>"])


def test_hero_symbol_uses_animation_class():
    out = hero_symbol_html(0, "☀️")
    assert "wx-clear" in out and "☀️" in out
    assert "wx-storm" in hero_symbol_html(95, "⛈️")


def test_intro_splash_is_branded_and_names_real_sources():
    out = intro_html()
    # Title is per-letter spans now (fly-in), so check the letters, not the
    # contiguous word.
    assert all(f">{ch}</span>" in out for ch in "EARTHWISEAI")
    assert "Pakistan Earth Intelligence" in out
    assert "NASA POWER" in out and "OPEN-METEO" in out and "CAMS" in out
    assert "ew-intro" in out and "ew-intro-bar" in out
    assert "<script>" not in out
    assert "@keyframes introBar" in INTRO_CSS
    assert "@keyframes introFadeOut" in INTRO_CSS
    assert "prefers-reduced-motion" in INTRO_CSS


def test_intro_title_flies_in_letter_by_letter():
    """Intro fly-in (2026-11-14): the title is per-letter spans with
    staggered delays, driven by the introFlyIn keyframe; the 'AI' letters
    keep the accent colour; reduced-motion users get no delay either."""
    out = intro_html()
    assert out.count("ew-intro-letter") == 11  # EARTHWISE (9) + AI (2)
    assert out.count("ew-intro-ai") == 2
    assert "animation-delay:50ms" in out
    assert "animation-delay:700ms" in out
    assert ">E</span>" in out and ">I</span>" in out
    # Letters are separate spans now, so the plain contiguous word is gone
    # from the markup (the visible text still reads EARTHWISE AI).
    assert "EARTHWISE <span>AI</span>" not in out
    assert "@keyframes introFlyIn" in INTRO_CSS
    assert "translateY(-56px)" in INTRO_CSS
    assert ".ew-intro-letter" in INTRO_CSS
    assert "introFadeOut .5s ease 2.5s" in INTRO_CSS  # splash stays ~2.5s, fades after
    assert "animation-delay:0ms!important" in INTRO_CSS  # reduced-motion: no stagger


def test_intro_splash_has_real_loading_stages_and_globe_pulse():
    """Intro upgrade (2026-11-14): staged loading text reflecting real
    stages, a pulsing ring around the globe, and a title glow — all CSS,
    all inside the ~2.5s splash."""
    out = intro_html()
    assert "Connecting to NASA POWER" in out
    assert "Fetching live weather" in out
    assert "Loading 10-year climate history" in out
    assert "ew-intro-stages" in out and "ew-intro-stage" in out
    assert out.count("ew-intro-stage") == 4  # container + 3 stage spans
    assert "ew-intro-ring" in out
    assert "@keyframes introStage" in INTRO_CSS
    assert "@keyframes introStageLast" in INTRO_CSS
    assert "@keyframes introTitleGlow" in INTRO_CSS
    assert "@keyframes introRing" in INTRO_CSS
    assert "introBar 2.3s" in INTRO_CSS


def test_animation_css_respects_reduced_motion_and_mobile():
    # Reduced-motion is enforced by the app's existing media query in main.py;
    # the animation CSS itself must not set animation-duration:0 / remove it.
    assert "@keyframes tickerScroll" in ANIMATION_CSS
    assert "@keyframes heroShimmer" in ANIMATION_CSS
    assert "@keyframes kpiIn" in ANIMATION_CSS
    assert "@media(prefers-reduced-motion" not in ANIMATION_CSS  # handled in main.py
    assert "max-width:700px" in ANIMATION_CSS

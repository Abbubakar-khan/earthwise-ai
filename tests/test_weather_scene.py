"""Live weather scene (2026-11-14): the animated sky must match the LIVE
weather code — sun for clear, clouds, rain, snow, storm, fog — and must
never show a scene for weather it does not have (no fake data)."""
from src.animations import live_weather_scene_html, weather_scene_class


def _wx(code, temp=26.0, condition="Clear sky"):
    return {"weather_code": code, "temperature_2m": temp,
            "condition_text": condition}


def test_scene_class_mapping():
    assert weather_scene_class(0) == "wx-clear"
    assert weather_scene_class(2) == "wx-partly"
    assert weather_scene_class(3) == "wx-cloud"
    assert weather_scene_class(61) == "wx-rain"
    assert weather_scene_class(71) == "wx-snow"
    assert weather_scene_class(95) == "wx-storm"
    assert weather_scene_class(45) == "wx-fog"
    assert weather_scene_class(None) == "wx-partly"


def test_clear_scene_has_sun_and_temp():
    html = live_weather_scene_html(_wx(0))
    assert 'wx-scene wx-clear' in html
    assert 'wx-scene-sun' in html
    assert "26.0°" in html
    assert "Clear sky" in html


def test_cloudy_scene_has_clouds_not_sun():
    html = live_weather_scene_html(_wx(3, 22.0, "Overcast"))
    assert 'wx-scene wx-cloud' in html
    assert 'wx-cloud-shape' in html
    assert 'wx-scene-sun' not in html


def test_rain_scene_has_falling_drops():
    html = live_weather_scene_html(_wx(63, 19.0, "Moderate rain"))
    assert 'wx-scene wx-rain' in html
    assert html.count('wx-drop') >= 5


def test_snow_scene_has_flakes():
    html = live_weather_scene_html(_wx(73, -2.0, "Moderate snow"))
    assert 'wx-scene wx-snow' in html
    assert html.count('wx-flake') >= 5
    assert "-2.0°" in html


def test_storm_scene_has_lightning():
    html = live_weather_scene_html(_wx(95, 28.0, "Thunderstorm"))
    assert 'wx-scene wx-storm' in html
    assert 'wx-bolt' in html


def test_fog_scene_has_fog_bands():
    html = live_weather_scene_html(_wx(45, 12.0, "Fog"))
    assert 'wx-scene wx-fog' in html
    assert html.count('wx-fog-band') == 3


def test_no_scene_without_live_weather():
    assert live_weather_scene_html(None) == ""
    assert live_weather_scene_html({}) == ""
    assert live_weather_scene_html({"weather_code": 0}) == ""  # no temp


def test_condition_text_is_escaped():
    html = live_weather_scene_html(_wx(0, 26.0, "<script>alert(1)</script>"))
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

"""Auto location detect (2026-11-14): pure logic + AppTest handoff.

Covers:
- haversine distance and nearest-city matching against REGIONS,
- BigDataCloud reverse-geocode response parsing (with requests mocked),
- locality-name matching (exact / word / fuzzy / ambiguous / foreign),
- resolve_detected_location (reverse-geocode vs nearest fallback),
- the query-params handoff into the real app: a detected location switches
  the city and the live sections use the EXACT coordinates, denial falls
  back silently to the manual picker, and the main-area picker stays in
  sync with the sidebar picker (both directions).

The live weather/AQI functions and reverse_geocode are faked (no network)
in the AppTest tests; the climate history for the matched city comes from
the shipped demo CSV (Lahore) or the designed empty state (other cities),
so no NASA POWER fetch happens here.
"""
from pathlib import Path
from unittest import mock

import pytest
from streamlit.testing.v1 import AppTest

from src.geolocation import (
    LOCALITY_MAX_DISTANCE_KM,
    haversine_km,
    match_locality_to_city,
    nearest_region_city,
    parse_geo_query_params,
    parse_reverse_geocode,
    resolve_detected_location,
    reverse_geocode,
)

APP = str(Path(__file__).resolve().parents[1] / "app" / "main.py")
COMPONENT_DIR = Path(__file__).resolve().parents[1] / "components" / "geolocation"

LAHORE_LAT, LAHORE_LON = 31.5204, 74.3587
KARACHI_LAT, KARACHI_LON = 24.8607, 67.0011


# ---------- haversine / nearest city ----------

def test_haversine_same_point_is_zero():
    assert haversine_km(LAHORE_LAT, LAHORE_LON, LAHORE_LAT, LAHORE_LON) == 0.0


def test_haversine_lahore_karachi():
    # Lahore–Karachi is ~1,030 km by road-line; great-circle is ~1,033 km.
    assert 1000 <= haversine_km(LAHORE_LAT, LAHORE_LON, KARACHI_LAT, KARACHI_LON) <= 1060


def test_haversine_invalid_coordinates_raise():
    with pytest.raises(ValueError):
        haversine_km(100.0, 0.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        haversine_km(0.0, 200.0, 0.0, 0.0)


def test_nearest_region_city():
    city, dist = nearest_region_city(LAHORE_LAT, LAHORE_LON)
    assert city == "Lahore" and dist < 1.0
    city, dist = nearest_region_city(KARACHI_LAT, KARACHI_LON)
    assert city == "Karachi" and dist < 1.0
    # Mid-Atlantic: nearest catalogue city is the westernmost, Jiwani
    # (61.74°E — further west than Gwadar since the 2026-11-14 expansion).
    city, dist = nearest_region_city(0.0, -30.0)
    assert city == "Jiwani" and dist > 9000


# ---------- reverse-geocode parsing ----------

def test_parse_reverse_geocode_prefers_locality():
    assert parse_reverse_geocode({"locality": "Lahore", "city": "Lahore District"}) == "Lahore"


def test_parse_reverse_geocode_falls_back_to_city():
    assert parse_reverse_geocode({"locality": "", "city": "Karachi"}) == "Karachi"


def test_parse_reverse_geocode_empty_or_none():
    assert parse_reverse_geocode({}) is None
    assert parse_reverse_geocode(None) is None
    assert parse_reverse_geocode({"locality": "  ", "city": ""}) is None


def test_reverse_geocode_success_with_mock():
    fake = mock.Mock()
    fake.json.return_value = {"locality": "Lahore", "city": "Lahore", "countryName": "Pakistan"}
    fake.raise_for_status.return_value = None
    with mock.patch("src.geolocation.requests.get", return_value=fake) as get:
        assert reverse_geocode(LAHORE_LAT, LAHORE_LON) == "Lahore"
        url = get.call_args.args[0]
        assert "bigdatacloud.net" in url


def test_reverse_geocode_failure_returns_none():
    with mock.patch("src.geolocation.requests.get", side_effect=Exception("offline")):
        assert reverse_geocode(LAHORE_LAT, LAHORE_LON) is None


# ---------- locality matching ----------

@pytest.mark.parametrize("locality,expected", [
    ("Lahore", "Lahore"),
    ("lahore", "Lahore"),
    ("  Multan  ", "Multan"),
    ("Karimabad", "Hunza (Karimabad)"),
    ("Hunza", "Hunza (Karimabad)"),
    ("Faislabad", "Faisalabad"),      # typo -> fuzzy match
    ("Rawalpindi", "Rawalpindi"),
    ("Dera", None),                    # ambiguous (Dera Ghazi Khan / Dera Ismail Khan / ...)
    ("London", None),
    ("New York", None),
    ("", None),
    (None, None),
])
def test_match_locality_to_city(locality, expected):
    assert match_locality_to_city(locality) == expected


# ---------- resolve_detected_location ----------

def test_resolve_detected_location_reverse_geocode():
    r = resolve_detected_location(LAHORE_LAT, LAHORE_LON, "Lahore")
    assert r["city"] == "Lahore" and r["method"] == "reverse-geocode"
    assert r["locality"] == "Lahore" and r["distance_km"] < 1.0
    assert r["latitude"] == LAHORE_LAT and r["longitude"] == LAHORE_LON


def test_resolve_detected_location_nearest_when_no_locality():
    r = resolve_detected_location(KARACHI_LAT, KARACHI_LON, None)
    assert r["city"] == "Karachi" and r["method"] == "nearest"
    assert r["locality"] is None


def test_resolve_detected_location_nearest_when_far_outside():
    r = resolve_detected_location(0.0, -30.0, "Atlantic Ocean")
    assert r["city"] == "Jiwani" and r["method"] == "nearest"
    assert r["locality"] == "Atlantic Ocean"
    assert r["distance_km"] > LOCALITY_MAX_DISTANCE_KM


def test_resolve_detected_location_invalid_coordinates_raise():
    with pytest.raises(ValueError):
        resolve_detected_location(91.0, 0.0, "Nowhere")


# ---------- query-params handoff ----------

def test_parse_geo_query_params_ok():
    assert parse_geo_query_params({"geo_lat": "31.5", "geo_lon": "74.3", "geo_status": "ok"}) == {
        "status": "ok", "latitude": 31.5, "longitude": 74.3}


def test_parse_geo_query_params_denied_without_coords():
    assert parse_geo_query_params({"geo_status": "denied"}) == {
        "status": "denied", "latitude": None, "longitude": None}


def test_parse_geo_query_params_rejects_bad_values():
    assert parse_geo_query_params({"geo_lat": "abc", "geo_lon": "74.3", "geo_status": "ok"}) is None
    assert parse_geo_query_params({"geo_lat": "100", "geo_lon": "74.3", "geo_status": "ok"}) is None
    assert parse_geo_query_params({"geo_lat": "31.5", "geo_lon": "74.3"}) is None  # no status
    assert parse_geo_query_params({}) is None


# ---------- component files ----------

def test_component_files_present_and_wired():
    html = (COMPONENT_DIR / "index.html").read_text()
    assert "navigator.geolocation" in html
    assert "setComponentValue" in html
    assert "setComponentReady" in html
    assert "request_id" in html
    assert (COMPONENT_DIR / "streamlit.js").exists()
    assert (COMPONENT_DIR / "ArrowTable.js").exists()


# ---------- AppTest: detected location actually switches the city ----------

class _FakeCached:
    """Stand-in for a @st.cache_data function: callable, records calls,
    and has .clear() (the app's refresh button calls .clear() on the
    real cached functions)."""
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if callable(self.payload):
            return self.payload(*args, **kwargs)
        return self.payload

    def clear(self):
        self.calls.clear()


def _fake_current(lat, lon, city):
    return {
        "temperature_2m": 18.6, "relative_humidity_2m": 55,
        "apparent_temperature": 18.9, "precipitation": 0.0,
        "weather_code": 0, "wind_speed_10m": 6.1, "wind_direction_10m": 90,
        "cloud_cover": 5, "condition_text": "Clear sky", "city": city,
        "timezone": "Asia/Karachi", "provider_time": "2026-11-14T03:00",
        "source": "Open-Meteo free evaluation API",
    }


def _fake_forecast(lat, lon):
    days = ["2026-11-14", "2026-11-15", "2026-11-16", "2026-11-17",
            "2026-11-18", "2026-11-19", "2026-11-20"]
    return {
        "daily": {
            "time": days, "weather_code": [0] * 7,
            "temperature_2m_max": [24.0] * 7, "temperature_2m_min": [12.0] * 7,
            "precipitation_probability_max": [0] * 7, "precipitation_sum": [0.0] * 7,
            "wind_speed_10m_max": [10.0] * 7,
            "sunrise": ["2026-11-14T06:30"] * 7, "sunset": ["2026-11-14T17:30"] * 7,
            "uv_index_max": [5.0] * 7,
        },
        "hourly": {
            "time": ["2026-11-14T00:00"] * 24, "temperature_2m": [18.0] * 24,
            "precipitation_probability": [0] * 24, "precipitation": [0.0] * 24,
            "weather_code": [0] * 24, "wind_speed_10m": [5.0] * 24,
        },
        "timezone": "Asia/Karachi", "source": "Open-Meteo free evaluation API",
        "forecast_generated_at": "2026-11-14T03:00",
    }


def _fake_aqi(lat, lon, city=""):
    return {
        "city": city,
        "current": {"us_aqi": 42, "pm2_5": 12.0, "pm10": 20.0, "time": "2026-11-14T03:00"},
        "hourly": {"time": ["2026-11-14T00:00"], "pm2_5": [12.0], "us_aqi": [42]},
        "timezone": "Asia/Karachi", "provider_time": "2026-11-14T03:00",
        "source": "Open-Meteo Air Quality API (CAMS)",
        "aqi_label": "Good", "aqi_colour": "#4ade80",
        "aqi_advice": "Air quality is good.",
        "dominant_pollutant": "PM2.5",
    }


@pytest.fixture
def geo_app(monkeypatch):
    """Run the real app with live weather/AQI + reverse-geocode faked.

    Yields run(query_params, locality): starts a fresh AppTest with those
    query params and that reverse-geocode answer.
    """
    def run(query_params=None, locality="Lahore"):
        monkeypatch.setattr("src.live_weather.get_current_conditions", _FakeCached(_fake_current))
        monkeypatch.setattr("src.live_weather.get_weather_forecast", _FakeCached(_fake_forecast))
        monkeypatch.setattr("src.air_quality.get_air_quality", _FakeCached(_fake_aqi))
        monkeypatch.setattr("src.geolocation.reverse_geocode", lambda lat, lon: locality)
        at = AppTest.from_file(APP, default_timeout=90)
        if query_params:
            at.query_params = dict(query_params)
        at.run()
        assert not at.exception, f"app raised: {at.exception}"
        return at

    yield run


def _all_text(at):
    return "\n".join(
        [m.value for m in at.markdown] +
        [c.value for c in at.caption] +
        [t.value for t in at.text] +
        [w.value for w in at.warning] +
        [i.value for i in at.info]
    )


def test_geo_query_params_switch_city_and_use_exact_coords(geo_app):
    # A point a few km off Lahore's centre: matched city is Lahore, but
    # live weather must use the EXACT detected coordinates, not the centre.
    at = geo_app({"geo_lat": "31.55", "geo_lon": "74.40", "geo_status": "ok"})
    assert at.session_state["City"] == "Lahore"
    geo = at.session_state["geo"]
    assert geo["city"] == "Lahore" and geo["method"] == "reverse-geocode"
    assert geo["latitude"] == 31.55 and geo["longitude"] == 74.40
    assert "Detected near: Lahore" in _all_text(at)
    assert at.query_params == {}, "detected coords must not stay in the URL"


def test_geo_exact_coords_passed_to_live_calls(geo_app, monkeypatch):
    # Same scenario as above, but asserting on the fake's recorded calls.
    current = _FakeCached(_fake_current)
    forecast = _FakeCached(_fake_forecast)
    aqi = _FakeCached(_fake_aqi)
    monkeypatch.setattr("src.live_weather.get_current_conditions", current)
    monkeypatch.setattr("src.live_weather.get_weather_forecast", forecast)
    monkeypatch.setattr("src.air_quality.get_air_quality", aqi)
    monkeypatch.setattr("src.geolocation.reverse_geocode", lambda lat, lon: "Lahore")
    at = AppTest.from_file(APP, default_timeout=90)
    at.query_params = {"geo_lat": "31.55", "geo_lon": "74.40", "geo_status": "ok"}
    at.run()
    assert not at.exception
    assert current.calls and current.calls[0][0][:2] == (31.55, 74.40), \
        f"live weather must use exact coords, got {current.calls}"
    assert aqi.calls and aqi.calls[0][0][:2] == (31.55, 74.40)


def test_geo_denied_falls_back_silently(geo_app):
    at = geo_app({"geo_status": "denied"})
    # "geo" is never set on denial — the app just falls back to the picker.
    # (AppTest's session_state has no .get(), so check membership instead.)
    assert "geo" not in at.session_state
    assert at.session_state["City"] == "Lahore"  # default, unchanged
    assert "declined" in _all_text(at)
    assert any("Use my location" in b.label for b in at.button)


def test_geo_outside_pakistan_uses_nearest_city(geo_app):
    at = geo_app({"geo_lat": "0.0", "geo_lon": "-30.0", "geo_status": "ok"},
                 locality="Atlantic Ocean")
    assert at.session_state["City"] == "Jiwani"
    geo = at.session_state["geo"]
    assert geo["method"] == "nearest"
    assert "Nearest city in our catalogue: Jiwani" in _all_text(at)


def test_main_picker_syncs_sidebar(geo_app):
    at = geo_app()
    assert at.selectbox(key="city_main").value == "Lahore"
    at.selectbox(key="city_main").set_value("Karachi").run()
    assert not at.exception
    assert at.session_state["City"] == "Karachi"
    assert at.selectbox(key="City").value == "Karachi"


def test_sidebar_picker_syncs_main(geo_app):
    at = geo_app()
    at.selectbox(key="City").set_value("Islamabad").run()
    assert not at.exception
    assert at.selectbox(key="city_main").value == "Islamabad"
    assert at.session_state["City"] == "Islamabad"


def test_use_my_location_button_arms_request(geo_app):
    at = geo_app()
    assert "geo_request" not in at.session_state
    at.button(key="geo_use").click().run()
    assert not at.exception
    assert at.session_state["geo_request"] is True
    assert at.session_state["geo_request_id"] == 1


def test_change_button_clears_detection(geo_app):
    at = geo_app({"geo_lat": "31.55", "geo_lon": "74.40", "geo_status": "ok"})
    assert at.session_state["geo"] is not None
    assert at.button(key="geo_change") is not None
    at.button(key="geo_change").click().run()
    assert not at.exception
    assert at.session_state["geo"] is None
    assert at.session_state["City"] == "Lahore"  # city stays; only exact coords drop
    assert at.button(key="geo_use") is not None  # button is back


# ---------- component bundle regression (2026-11-14) ----------

def test_component_js_relative_imports_have_extensions():
    """Native ES modules need the file extension: "./ArrowTable" (no .js)
    fails to resolve in the browser, so the whole component never loads —
    the "Use my location" button then silently does nothing live (the
    "trouble loading the main.earthwise_geolocation component" banner).
    Every relative import in the vendored component must end in .js.
    """
    import re

    for name in ("streamlit.js", "index.html", "ArrowTable.js"):
        text = (COMPONENT_DIR / name).read_text(encoding="utf-8")
        # Skip //-comment lines: docstrings may quote an import path.
        code = "\n".join(
            line for line in text.splitlines()
            if not line.strip().startswith("//")
        )
        for imp in re.findall(r"""from\s+["'](\.[^"']+)["']""", code):
            assert imp.endswith(".js"), f"{name} has extensionless import: {imp}"
    assert './ArrowTable.js"' in (COMPONENT_DIR / "streamlit.js").read_text(encoding="utf-8")


def test_locating_caption_shows_after_tap(geo_app):
    """Tapping "Use my location" must give visible feedback while the
    detection is in flight, instead of the button looking dead."""
    at = geo_app()
    at.button(key="geo_use").click().run()
    assert not at.exception
    assert "Locating" in _all_text(at)


def test_assistant_example_has_no_literal_markdown_markers(geo_app):
    """Assistant answers are written in Markdown (**bold**), but the app
    renders them inside raw-HTML bubbles where Streamlit does not parse
    Markdown — the ** markers showed literally on the AI Assistant page
    (seen live 2026-11-14). Bold must render as <b>, with no ** left."""
    at = geo_app()
    at.radio(key="page").set_value("AI Assistant").run()
    assert not at.exception
    # Scope to the assistant's own HTML bubbles only: the sidebar's
    # "Climate signal" list legitimately uses ** in a real st.markdown
    # call, where Markdown IS parsed and bold renders fine.
    bubbles = [m.value for m in at.markdown
               if "ew-assistant-cap" in m.value
               or 'class="chat-a"' in m.value or 'class="chat-q"' in m.value]
    assert bubbles, "assistant example/chat bubbles missing"
    assert all("**" not in b for b in bubbles)
    assert any("<b>" in b for b in bubbles)  # the example answer's bold survived as HTML


def test_daily_advisory_page_renders_all_three(geo_app):
    """The Daily Advisory page (2026-11-14) shows the health verdict, the
    farmer advisory and the rain warning from the faked live data, and the
    Overview teaser button opens the page."""
    at = geo_app()
    assert at.button(key="adv_open") is not None
    at.button(key="adv_open").click().run()
    assert not at.exception
    assert at.session_state["page"] == "Daily Advisory"
    text = _all_text(at)
    assert "health verdict" in text.lower()
    assert "Farmer advisory" in text
    assert "Rain warning" in text
    assert "not medical advice" in text
    assert "not an official warning" in text

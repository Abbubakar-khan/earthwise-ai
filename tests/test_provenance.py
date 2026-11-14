"""NASA Data Provenance (2026-11-14): pure logic + HTML, no Streamlit,
no network. Tests that every live number traces to its source, that a
failed source shows as unavailable (never invented), and that HTML is
escaped.
"""
from src.provenance import provenance_html, provenance_rows


def _weather():
    return {"temperature_2m": 27.2, "apparent_temperature": 28.6,
            "condition_text": "Clear sky", "provider_time": "2026-11-14T13:00",
            "timezone": "Asia/Karachi", "source": "Open-Meteo free evaluation API"}


def _aqi():
    return {"current": {"us_aqi": 157, "pm2_5": 48.7},
            "aqi_label": "Unhealthy", "dominant_pollutant": "PM2.5",
            "provider_time": "2026-11-14T13:00", "timezone": "Asia/Karachi",
            "source": "Open-Meteo Air Quality API (CAMS)"}


def _meta():
    return {"rows": 4018, "valid_rows": 4018, "coverage_pct": 100.0,
            "first_date": "2015-01-01", "last_date": "2025-12-31"}


def _forecast():
    return {"forecast_generated_at": "2026-11-14T13:00", "timezone": "Asia/Karachi"}


def test_four_rows_always_present():
    rows = provenance_rows(_weather(), _aqi(), _forecast(), _meta())
    assert len(rows) == 4
    assert [r["source"] for r in rows] == [
        "NASA POWER", "Open-Meteo", "CAMS · Open-Meteo Air Quality", "NASA GIBS"]


def test_rows_carry_real_values():
    rows = provenance_rows(_weather(), _aqi(), _forecast(), _meta())
    power, om, cams, gibs = rows
    assert power["status"] == "live"
    assert "2015–2025" in power["detail"]
    assert "100.0% coverage" in power["detail"]
    assert "4,018" in power["detail"]
    assert om["status"] == "live"
    assert "27.2" in om["detail"] and "Clear sky" in om["detail"]
    assert "13:00" in om["updated"] and "Asia/Karachi" in om["updated"]
    assert cams["status"] == "live"
    assert "157" in cams["detail"] and "PM2.5" in cams["detail"]
    assert gibs["status"] == "on demand"
    assert "Weather & Maps" in gibs["detail"]


def test_failed_sources_show_unavailable_never_invented():
    rows = provenance_rows(None, None, None, None)
    assert [r["status"] for r in rows] == [
        "unavailable", "unavailable", "unavailable", "on demand"]
    joined = " ".join(r["detail"] for r in rows)
    assert "Unavailable" in joined
    assert "Not loaded yet" in joined
    # GIBS is on demand, never "live" from nothing.
    assert rows[3]["status"] == "on demand"


def test_partial_failure_only_marks_what_failed():
    rows = provenance_rows(_weather(), None, None, _meta())
    assert rows[0]["status"] == "live"
    assert rows[1]["status"] == "live"
    assert rows[2]["status"] == "unavailable"
    assert rows[3]["status"] == "on demand"


def test_provenance_html_names_all_sources_and_honesty_note():
    out = provenance_html(provenance_rows(_weather(), _aqi(), _forecast(), _meta()), "Lahore")
    for name in ("NASA POWER", "Open-Meteo", "CAMS", "NASA GIBS"):
        assert name in out
    assert "model estimates" in out
    assert "not station observations" in out
    assert "Lahore" in out
    assert "ew-prov" in out and "ew-prov-row" in out
    assert "Source docs" in out


def test_provenance_html_escapes_dynamic_strings():
    w = _weather()
    w["condition_text"] = "<script>alert(1)</script>"
    out = provenance_html(provenance_rows(w, _aqi(), _forecast(), _meta()), "<b>Lahore</b>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "&lt;b&gt;Lahore&lt;/b&gt;" in out


def test_provenance_html_empty_rows_still_renders_note():
    out = provenance_html([], "Lahore")
    assert "model estimates" in out
    assert "not station observations" in out

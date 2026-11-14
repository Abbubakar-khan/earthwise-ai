"""Retry behaviour for live Open-Meteo fetches.

Regression test for the 2026-11-14 morning outage: the deployed app showed
"temporarily unavailable" (read timeout) on every live page even though
api.open-meteo.com answered fine — a single attempt with no retry made one
slow fetch look like the whole app was broken.
"""
import requests

from src.live_weather import _get_with_retry


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_retry_succeeds_after_transient_timeouts(monkeypatch):
    calls = {"n": 0}

    def flaky_get(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise requests.ReadTimeout("read timed out")
        return _FakeResponse({"ok": True})

    monkeypatch.setattr("src.live_weather.requests.get", flaky_get)
    monkeypatch.setattr("src.live_weather.time.sleep", lambda s: None)
    resp = _get_with_retry("https://example.invalid", params={}, timeout=5)
    assert resp.json() == {"ok": True}
    assert calls["n"] == 3


def test_retry_raises_after_all_attempts_fail(monkeypatch):
    calls = {"n": 0}

    def always_timeout(*args, **kwargs):
        calls["n"] += 1
        raise requests.ReadTimeout("read timed out")

    monkeypatch.setattr("src.live_weather.requests.get", always_timeout)
    monkeypatch.setattr("src.live_weather.time.sleep", lambda s: None)
    try:
        _get_with_retry("https://example.invalid", params={}, timeout=5)
    except requests.ReadTimeout:
        pass
    else:
        raise AssertionError("expected ReadTimeout after retries exhausted")
    assert calls["n"] == 3

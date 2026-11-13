from types import SimpleNamespace

import src.ai_assistant as assistant


def test_gateway_configuration_enables_assistant(monkeypatch):
    values = {
        "NEON_AI_GATEWAY_BASE_URL": "https://branch-api.ai.example.neon.tech",
        "NEON_AI_GATEWAY_TOKEN": "scoped-token",
    }
    monkeypatch.setattr(assistant, "_secret", lambda name, default="": values.get(name, default))
    assert assistant.assistant_configured() is True


def test_gateway_is_preferred_and_uses_responses_route(monkeypatch):
    values = {
        "NEON_AI_GATEWAY_BASE_URL": "https://branch-api.ai.example.neon.tech/",
        "NEON_AI_GATEWAY_TOKEN": "scoped-token",
        "NEON_AI_MODEL": "gpt-5-mini",
        "OPENAI_API_KEY": "fallback-key",
    }
    monkeypatch.setattr(assistant, "_secret", lambda name, default="": values.get(name, default))
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return SimpleNamespace(status_code=200, json=lambda: {"output_text": "Gateway answer"})

    monkeypatch.setattr(assistant.requests, "post", fake_post)
    answer = assistant.ask_earthwise("Explain rainfall", {"city": "Lahore"}, [])

    assert answer == "Gateway answer"
    assert captured["url"] == "https://branch-api.ai.example.neon.tech/openai/v1/responses"
    assert captured["headers"]["Authorization"] == "Bearer scoped-token"
    assert captured["json"]["model"] == "gpt-5-mini"
    assert captured["json"]["store"] is False


def test_openai_fallback_is_used_without_gateway(monkeypatch):
    values = {"OPENAI_API_KEY": "openai-key", "OPENAI_MODEL": "gpt-4.1-mini"}
    monkeypatch.setattr(assistant, "_secret", lambda name, default="": values.get(name, default))
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return SimpleNamespace(status_code=200, json=lambda: {"output_text": "OpenAI answer"})

    monkeypatch.setattr(assistant.requests, "post", fake_post)
    answer = assistant.ask_earthwise("Explain temperature", {}, [])

    assert answer == "OpenAI answer"
    assert captured["url"] == assistant.OPENAI_API_URL
    assert captured["headers"]["Authorization"] == "Bearer openai-key"
    assert captured["json"]["model"] == "gpt-4.1-mini"


def test_assistant_requires_provider_credentials(monkeypatch):
    monkeypatch.setattr(assistant, "_secret", lambda name, default="": default)
    assert assistant.assistant_configured() is False

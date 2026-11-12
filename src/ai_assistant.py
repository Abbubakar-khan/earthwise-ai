"""EARTHWISE AI conversational climate assistant.

Uses Neon's branch-scoped AI Gateway when configured, with an optional direct
OpenAI Responses API fallback. Credentials are read server-side only.
"""
from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

OPENAI_API_URL = "https://api.openai.com/v1/responses"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_NEON_MODEL = "gpt-5-mini"


def _secret(name: str, default: str = "") -> str:
    value = os.getenv(name, "")
    if value:
        return value
    try:
        return str(st.secrets.get(name, default) or default)
    except Exception:
        return default


def _gateway_config() -> tuple[str, str]:
    """Return the Neon Gateway base URL and token when both are configured."""
    base_url = _secret("NEON_AI_GATEWAY_BASE_URL").strip().rstrip("/")
    token = _secret("NEON_AI_GATEWAY_TOKEN").strip()
    return (base_url, token) if base_url and token else ("", "")


def assistant_configured() -> bool:
    gateway_url, gateway_token = _gateway_config()
    return bool((gateway_url and gateway_token) or _secret("OPENAI_API_KEY").strip())


def ask_earthwise(question: str, context: dict[str, Any], history: list[dict[str, str]]) -> str:
    """Ask the configured model with evidence and safety boundaries."""
    gateway_url, gateway_token = _gateway_config()
    if gateway_url and gateway_token:
        api_url = f"{gateway_url}/openai/v1/responses"
        api_key = gateway_token
        model = _secret("NEON_AI_MODEL", DEFAULT_NEON_MODEL).strip() or DEFAULT_NEON_MODEL
    else:
        api_key = _secret("OPENAI_API_KEY").strip()
        if not api_key:
            raise RuntimeError(
                "EARTHWISE AI chat is not configured. Add NEON_AI_GATEWAY_BASE_URL "
                "and NEON_AI_GATEWAY_TOKEN, or an OPENAI_API_KEY, in Streamlit app Secrets."
            )
        api_url = OPENAI_API_URL
        model = _secret("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL

    instructions = (
        "You are EARTHWISE AI, a careful Earth and climate intelligence assistant. "
        "Help users understand Pakistan's climate, weather, geography, satellite imagery, "
        "and the dataset context supplied with the conversation. Be clear, concise, and useful. "
        "Never invent measurements, sources, citations, live alerts, or forecasts. "
        "Distinguish observed, modelled, historical, and forecast information. "
        "NASA POWER values are gridded satellite/model-assisted estimates, not local station observations. "
        "A historical trend is not a forecast and does not prove causation. "
        "If the supplied context does not contain the requested fact, say what is missing and suggest a reliable source. "
        "Do not present this product as an emergency warning system. For immediate danger, direct users to official authorities. "
        "Use Markdown, explain units, and state uncertainty plainly."
    )
    transcript = []
    for item in history[-8:]:
        role = item.get("role", "")
        text = item.get("content", "")
        if role in {"user", "assistant"} and text:
            transcript.append(f"{role.upper()}: {text}")
    transcript.append(f"CURRENT DATA CONTEXT: {context}")
    transcript.append(f"USER: {question}")
    payload = {
        "model": model,
        "instructions": instructions,
        "input": "\n\n".join(transcript),
        "max_output_tokens": 700,
        "store": False,
    }
    try:
        response = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        if response.status_code >= 400:
            # Never echo provider response bodies because they may contain sensitive details.
            raise RuntimeError(
                f"The AI provider returned HTTP {response.status_code}. "
                "Check the Neon Gateway credential/model access or the configured provider key."
            )
        data = response.json()
    except requests.Timeout as exc:
        raise RuntimeError("The AI request timed out. Please try again.") from exc
    except requests.RequestException as exc:
        raise RuntimeError("EARTHWISE AI could not reach its model provider. Please try again shortly.") from exc

    output_text = data.get("output_text")
    if output_text:
        return str(output_text).strip()
    chunks = []
    for item in data.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text" and part.get("text"):
                    chunks.append(part["text"])
    answer = "\n".join(chunks).strip()
    if not answer:
        raise RuntimeError("The AI provider returned an empty answer. Please try a different question.")
    return answer

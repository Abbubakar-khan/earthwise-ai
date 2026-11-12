"""EARTHWISE AI conversational climate assistant.

Uses the OpenAI Responses API only when the owner supplies an API key in
Streamlit secrets. The key is never shown in the interface or sent to the browser.
"""
from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1-mini"


def _secret(name: str, default: str = "") -> str:
    value = os.getenv(name, "")
    if value:
        return value
    try:
        return str(st.secrets.get(name, default) or default)
    except Exception:
        return default


def assistant_configured() -> bool:
    return bool(_secret("OPENAI_API_KEY").strip())


def ask_earthwise(question: str, context: dict[str, Any], history: list[dict[str, str]]) -> str:
    """Ask the configured language model, with strict evidence and safety boundaries."""
    api_key = _secret("OPENAI_API_KEY").strip()
    if not api_key:
        raise RuntimeError("EARTHWISE AI chat is not configured yet. Add OPENAI_API_KEY in Streamlit app Secrets.")
    model = _secret("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
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
            API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        if response.status_code >= 400:
            # Never echo provider response bodies because they may contain sensitive details.
            raise RuntimeError(f"The AI provider returned HTTP {response.status_code}. Check the API key, billing, model access, and usage limits.")
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

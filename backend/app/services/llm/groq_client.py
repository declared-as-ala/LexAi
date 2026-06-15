"""Minimal Groq (OpenAI-compatible) chat client — no secrets in code."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT


def groq_chat_completion_content(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.25,
    max_tokens: int = 8192,
    response_format_json: bool = True,
) -> str | None:
    """
    POST /chat/completions; returns assistant message content or None on failure.

    Never logs the API key or full request body containing secrets.
    """
    if not LLM_API_KEY:
        return None
    base = LLM_BASE_URL.rstrip("/")
    url = f"{base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format_json:
        body["response_format"] = {"type": "json_object"}

    try:
        with httpx.Client(timeout=float(LLM_TIMEOUT)) as client:
            r = client.post(url, headers=headers, json=body)
    except httpx.HTTPError:
        return None

    if r.status_code >= 400:
        # Groq may reject response_format for some models — retry without it once
        if response_format_json and r.status_code == 400:
            body.pop("response_format", None)
            try:
                with httpx.Client(timeout=float(LLM_TIMEOUT)) as client:
                    r = client.post(url, headers=headers, json=body)
            except httpx.HTTPError:
                return None
        if r.status_code >= 400:
            return None

    try:
        data = r.json()
        return str(data["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None

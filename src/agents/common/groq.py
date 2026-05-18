from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from urllib.parse import urljoin

from .gemini import load_env_file


GROQ_API_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_TIMEOUT_SECONDS = 60.0


@dataclass(slots=True)
class GroqResponse:
    text: str
    raw: dict[str, Any]
    model: str


def call_groq(
    *,
    model: str,
    prompt: str,
    api_key: str | None = None,
    context: str | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    top_p: float | None = None,
    system_instruction: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> GroqResponse:
    resolved_key = _resolve_api_key(api_key)
    payload: dict[str, Any] = {
        "model": model,
        "messages": _build_messages(context, prompt, system_instruction),
    }

    if temperature is not None:
        payload["temperature"] = temperature
    if max_output_tokens is not None:
        payload["max_tokens"] = max_output_tokens
    if top_p is not None:
        payload["top_p"] = top_p

    url = urljoin(GROQ_API_BASE_URL.rstrip("/") + "/", "chat/completions")
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {resolved_key}",
            # Cloudflare's Browser Integrity Check can block requests with
            # missing or generic User-Agent header. Allow configuring the
            # header via the GROQ_USER_AGENT env var; default to a modern
            # browser-like User-Agent which is normally accepted by Cloudflare.
            "User-Agent": os.getenv(
                "GROQ_USER_AGENT",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            ),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Groq request failed with HTTP {error.code}: {details}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Groq request failed: {error.reason}") from error

    return GroqResponse(text=_extract_text(raw), raw=raw, model=model)


def _resolve_api_key(api_key: str | None) -> str:
    load_env_file()
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("Groq API key not provided. Set GROQ_API_KEY or pass api_key explicitly.")
    return key


def _build_messages(context: str | None, prompt: str, system_instruction: str | None) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    user_parts: list[str] = []
    if context:
        user_parts.append(context)
    user_parts.append(prompt)
    messages.append({"role": "user", "content": "\n\n".join(user_parts)})
    return messages


def _extract_text(raw: dict[str, Any]) -> str:
    choices = raw.get("choices", [])
    for choice in choices:
        message = choice.get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                text = part.get("text") if isinstance(part, dict) else None
                if isinstance(text, str):
                    parts.append(text)
            if parts:
                return "".join(parts)
    return ""
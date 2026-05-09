from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_TIMEOUT_SECONDS = 60.0


@dataclass(slots=True)
class GeminiRequest:
    """Parameters for a single Gemini generateContent call."""

    model: str
    prompt: str
    context: str | None = None
    api_key: str | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None
    top_p: float | None = None
    top_k: int | None = None
    system_instruction: str | None = None
    safety_settings: list[dict[str, Any]] = field(default_factory=list)
    stream: bool = False
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    extra_generation_config: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GeminiResponse:
    """Normalized Gemini response payload."""

    text: str
    raw: dict[str, Any]
    model: str


def load_env_file(path: str | os.PathLike[str] | None = None) -> None:
    """Load simple KEY=VALUE lines from a local .env file into process env."""
    env_path = Path(path) if path is not None else Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def call_gemini(
    *,
    model: str,
    prompt: str,
    api_key: str | None = None,
    context: str | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    system_instruction: str | None = None,
    safety_settings: list[dict[str, Any]] | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    stream: bool = False,
    extra_generation_config: dict[str, Any] | None = None,
) -> GeminiResponse:
    """Call Gemini using the REST generateContent endpoint.

    The helper keeps agent code simple and avoids a hard dependency on the SDK.
    It accepts both explicit API keys and environment-based keys.
    """
    resolved_key = _resolve_api_key(api_key)
    contents = _build_contents(context, prompt)
    payload: dict[str, Any] = {
        "contents": contents,
    }

    generation_config: dict[str, Any] = dict(extra_generation_config or {})
    if temperature is not None:
        generation_config["temperature"] = temperature
    if max_output_tokens is not None:
        generation_config["maxOutputTokens"] = max_output_tokens
    if top_p is not None:
        generation_config["topP"] = top_p
    if top_k is not None:
        generation_config["topK"] = top_k
    if generation_config:
        payload["generationConfig"] = generation_config
    if system_instruction is not None:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
    if safety_settings:
        payload["safetySettings"] = safety_settings
    if stream:
        payload["stream"] = True

    url = f"{GEMINI_API_BASE_URL}/models/{model}:generateContent?{urlencode({'key': resolved_key})}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini request failed with HTTP {error.code}: {details}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Gemini request failed: {error.reason}") from error

    return GeminiResponse(text=_extract_text(raw), raw=raw, model=model)


def _resolve_api_key(api_key: str | None) -> str:
    load_env_file()
    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY or pass api_key explicitly.")
    return key


def _build_contents(context: str | None, prompt: str) -> list[dict[str, Any]]:
    parts: list[dict[str, str]] = []
    if context:
        parts.append({"text": context})
    parts.append({"text": prompt})
    return [{"role": "user", "parts": parts}]


def _extract_text(raw: dict[str, Any]) -> str:
    candidates = raw.get("candidates", [])
    for candidate in candidates:
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if isinstance(text, str):
                return text
    return ""

from __future__ import annotations

import os
from dataclasses import dataclass

from .gemini import call_gemini
from .groq import call_groq


DEFAULT_GEMINI_FALLBACK_MODEL = "gemini-3.1-flash-lite"
GROQ_MODELS = {
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
    "groq/compound-mini",
    "groq/compound",
}


@dataclass(slots=True)
class DevModelResult:
    provider: str
    response_text: str
    fallback_note: str = ""


def resolve_provider(model: str) -> str:
    normalized = model.strip().lower()
    if normalized in GROQ_MODELS or normalized.startswith("groq/"):
        return "groq"
    return "gemini"


def call_dev_model(
    *,
    model: str,
    prompt: str,
    context: str | None,
    system_instruction: str | None,
    temperature: float | None,
    max_output_tokens: int | None,
    top_p: float | None,
    top_k: int | None,
    timeout_seconds: float,
    fallback_model: str | None = None,
) -> DevModelResult:
    provider = resolve_provider(model)
    if provider == "groq":
        try:
            response = call_groq(
                model=model,
                prompt=prompt,
                api_key=os.getenv("GROQ_API_KEY"),
                context=context,
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=top_p,
                timeout_seconds=timeout_seconds,
            )
            return DevModelResult(provider=provider, response_text=response.text)
        except Exception as exc:
            if not _is_groq_access_denied(exc):
                raise
            fallback = fallback_model or os.getenv("GEMINI_FALLBACK_MODEL") or DEFAULT_GEMINI_FALLBACK_MODEL
            response = call_gemini(
                model=fallback,
                prompt=prompt,
                context=context,
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=top_p,
                top_k=top_k,
                timeout_seconds=timeout_seconds,
            )
            return DevModelResult(
                provider=f"gemini-fallback:{fallback}",
                response_text=response.text,
                fallback_note=f"Groq access denied; fell back to {fallback}.",
            )

    response = call_gemini(
        model=model,
        prompt=prompt,
        context=context,
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        top_p=top_p,
        top_k=top_k,
        timeout_seconds=timeout_seconds,
    )
    return DevModelResult(provider=provider, response_text=response.text)


def _is_groq_access_denied(error: Exception) -> bool:
    message = str(error)
    return "Groq request failed with HTTP 403" in message and "error code: 1010" in message
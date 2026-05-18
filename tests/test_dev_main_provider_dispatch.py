from __future__ import annotations

from pathlib import Path

from agents.common import dev_main
from agents.common.dev_providers import call_dev_model, resolve_provider


def test_resolve_provider_routes_groq_models() -> None:
    assert resolve_provider("llama-3.1-8b-instant") == "groq"
    assert resolve_provider("groq/compound-mini") == "groq"
    assert resolve_provider("gemini-3.1-flash-lite") == "gemini"


def test_call_model_uses_groq_for_groq_models(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _Response:
        text = "groq-ok"

    def fake_groq(**kwargs):
        captured["provider"] = "groq"
        captured["kwargs"] = kwargs
        return _Response()

    def fake_gemini(**kwargs):
        raise AssertionError("Gemini caller should not be used for Groq models")

    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setattr("agents.common.dev_providers.call_groq", fake_groq)
    monkeypatch.setattr("agents.common.dev_providers.call_gemini", fake_gemini)

    result = call_dev_model(
        model="llama-3.1-8b-instant",
        prompt="hello",
        context="ctx",
        system_instruction="sys",
        temperature=0.2,
        max_output_tokens=64,
        top_p=0.95,
        top_k=40,
        timeout_seconds=5.0,
    )

    assert result.provider == "groq"
    assert result.response_text == "groq-ok"
    assert captured["kwargs"]["model"] == "llama-3.1-8b-instant"
    assert captured["kwargs"]["prompt"] == "hello"
    assert captured["kwargs"]["api_key"] == "groq-key"


def test_call_model_uses_gemini_for_non_groq_models(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _Response:
        text = "gemini-ok"

    def fake_groq(**kwargs):
        raise AssertionError("Groq caller should not be used for Gemini models")

    def fake_gemini(**kwargs):
        captured["provider"] = "gemini"
        captured["kwargs"] = kwargs
        return _Response()

    monkeypatch.setattr("agents.common.dev_providers.call_groq", fake_groq)
    monkeypatch.setattr("agents.common.dev_providers.call_gemini", fake_gemini)

    result = call_dev_model(
        model="gemini-3.1-flash-lite",
        prompt="hello",
        context="ctx",
        system_instruction="sys",
        temperature=0.2,
        max_output_tokens=64,
        top_p=0.95,
        top_k=40,
        timeout_seconds=5.0,
    )

    assert result.provider == "gemini"
    assert result.response_text == "gemini-ok"
    assert captured["kwargs"]["model"] == "gemini-3.1-flash-lite"


def test_main_writes_output_without_echoing_response(monkeypatch, tmp_path, capsys) -> None:
    output_file = tmp_path / "dev_output.md"

    monkeypatch.setattr(dev_main, "load_env_file", lambda: None)
    monkeypatch.setattr(dev_main, "parse_args", lambda: type("Args", (), {"config": "ignored", "prompt": None})())
    monkeypatch.setattr(
        dev_main,
        "load_run_config",
        lambda config_path: {
            "model": "gemini-3.1-flash-lite",
            "prompt_file": "prompt.md",
            "context_file": "context.md",
            "system_instruction_file": "system.md",
            "output_file": str(output_file),
            "temperature": 0.2,
            "max_output_tokens": 64,
            "top_p": 0.95,
            "top_k": 40,
            "timeout_seconds": 5.0,
        },
    )
    monkeypatch.setattr(dev_main, "read_text_file", lambda path_value, **kwargs: {"prompt.md": "prompt text", "context.md": "context text", "system.md": "system text"}[path_value])
    monkeypatch.setattr(dev_main, "call_dev_model", lambda **kwargs: type("Result", (), {"provider": "gemini", "response_text": "response text", "fallback_note": ""})())

    dev_main.main()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert output_file.exists()
    assert "response text" in output_file.read_text(encoding="utf-8")


def test_main_falls_back_to_gemini_when_groq_is_access_denied(monkeypatch, tmp_path, capsys) -> None:
    output_file = tmp_path / "dev_output.md"

    monkeypatch.setattr(dev_main, "load_env_file", lambda: None)
    monkeypatch.setattr(dev_main, "parse_args", lambda: type("Args", (), {"config": "ignored", "prompt": None})())
    monkeypatch.setattr(
        dev_main,
        "load_run_config",
        lambda config_path: {
            "model": "llama-3.1-8b-instant",
            "prompt_file": "prompt.md",
            "context_file": "context.md",
            "system_instruction_file": "system.md",
            "output_file": str(output_file),
            "temperature": 0.2,
            "max_output_tokens": 64,
            "top_p": 0.95,
            "top_k": 40,
            "timeout_seconds": 5.0,
            "fallback_model": "gemini-3.1-flash-lite",
        },
    )
    monkeypatch.setattr(dev_main, "read_text_file", lambda path_value, **kwargs: {"prompt.md": "prompt text", "context.md": "context text", "system.md": "system text"}[path_value])
    monkeypatch.setattr(
        dev_main,
        "call_dev_model",
        lambda **kwargs: type("Result", (), {"provider": "gemini-fallback:gemini-3.1-flash-lite", "response_text": "fallback text", "fallback_note": "Groq access denied; fell back to gemini-3.1-flash-lite."})(),
    )

    dev_main.main()

    captured = capsys.readouterr()
    assert captured.out == ""
    output_text = output_file.read_text(encoding="utf-8")
    assert "fallback text" in output_text
    assert "Groq access denied; fell back to gemini-3.1-flash-lite." in output_text
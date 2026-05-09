from __future__ import annotations

import json
import os

from agents.common.gemini import call_gemini, load_env_file


class _DummyResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def __enter__(self) -> "_DummyResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_load_env_file_reads_agents_folder_env(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("GEMINI_API_KEY=test-key\n", encoding="utf-8")

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    load_env_file(env_path)

    assert os.getenv("GEMINI_API_KEY") == "test-key"


def test_call_gemini_builds_generate_content_request(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = dict(request.headers)
        captured["timeout"] = timeout
        return _DummyResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "ok"}],
                        }
                    }
                ]
            }
        )

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    response = call_gemini(
        model="gemini-3-flash-preview",
        prompt="status",
        context="role: captain",
        system_instruction="You are a helper.",
        temperature=0.4,
        max_output_tokens=128,
    )

    assert response.text == "ok"
    assert "gemini-3-flash-preview:generateContent" in captured["url"]
    assert captured["body"]["contents"][0]["parts"][0]["text"] == "role: captain"
    assert captured["body"]["contents"][0]["parts"][1]["text"] == "status"
    assert captured["body"]["systemInstruction"]["parts"][0]["text"] == "You are a helper."
    assert captured["body"]["generationConfig"]["temperature"] == 0.4
    assert captured["body"]["generationConfig"]["maxOutputTokens"] == 128
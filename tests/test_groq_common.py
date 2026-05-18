from __future__ import annotations

import json

from agents.common.groq import call_groq


class _DummyResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def __enter__(self) -> "_DummyResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_call_groq_builds_chat_completions_request(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = dict(request.headers)
        captured["timeout"] = timeout
        return _DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "ok",
                        }
                    }
                ]
            }
        )

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    response = call_groq(
        model="llama-3.1-8b-instant",
        prompt="status",
        context="role: captain",
        system_instruction="You are a helper.",
        temperature=0.4,
        max_output_tokens=128,
        top_p=0.95,
    )

    assert response.text == "ok"
    assert captured["url"].endswith("/chat/completions")
    assert captured["body"]["model"] == "llama-3.1-8b-instant"
    assert captured["body"]["messages"][0]["role"] == "system"
    assert captured["body"]["messages"][1]["content"] == "role: captain\n\nstatus"
    assert captured["body"]["temperature"] == 0.4
    assert captured["body"]["max_tokens"] == 128
    assert captured["body"]["top_p"] == 0.95
from __future__ import annotations

import json

from agents.base import AgentRole
from agents.common.functions import (
    broadcast_team_message,
    build_activity_context,
    build_activity_prompt,
    build_team_activity_payload,
    call_agent_activity,
    read_role_memory,
    send_inter_agent_message,
)
from agents.manager import TeamAgentManager
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import MapData


def _build_state() -> GameState:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    return GameState(
        map_data=map_data,
        subs={"BLUE": SubmarineState(x=1, y=1), "RED": SubmarineState(x=2, y=2)},
    )


def test_read_role_memory_reads_markdown(tmp_path) -> None:
    root = tmp_path / "agents"
    captain_dir = root / "captain"
    captain_dir.mkdir(parents=True)
    (captain_dir / "memory.md").write_text("# Captain\n", encoding="utf-8")

    assert read_role_memory("captain", root) == "# Captain\n"


def test_build_activity_context_and_prompt() -> None:
    state = _build_state()
    payload = build_team_activity_payload(state, "BLUE", AgentRole.CAPTAIN)

    context = build_activity_context(
        team_view=payload,
        role=AgentRole.CAPTAIN,
        message_history=[{"sender": "first_mate", "text": "ready"}],
        role_memory="memory text",
    )
    prompt = build_activity_prompt("Choose the next action", ["Use JSON", "Stay brief"])

    assert "role=captain" in context
    assert "memory text" in context
    assert "first_mate" in context
    assert "Choose the next action" in prompt
    assert "Use JSON" in prompt


def test_inter_agent_message_helpers_and_gemini_call(monkeypatch) -> None:
    manager = TeamAgentManager("BLUE")
    manager.register_agent(
        _DummyAgent("BLUE", AgentRole.CAPTAIN),
        active=True,
    )
    manager.register_agent(
        _DummyAgent("BLUE", AgentRole.FIRST_MATE),
        active=True,
    )
    state = _build_state()
    payload = build_team_activity_payload(state, "BLUE", AgentRole.FIRST_MATE)

    class _DummyResponse:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return json.dumps(self._payload).encode("utf-8")

    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _DummyResponse({"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert send_inter_agent_message(manager, AgentRole.CAPTAIN, AgentRole.FIRST_MATE, "status") is True
    assert broadcast_team_message(manager, AgentRole.FIRST_MATE, "broadcast") is True

    response = call_agent_activity(
        model="gemini-3-flash-preview",
        prompt="Respond with JSON",
        team_view=payload,
        role=AgentRole.FIRST_MATE,
        system_instruction="You are a team assistant.",
        temperature=0.2,
    )

    assert response.text == "ok"
    assert captured["body"]["contents"][0]["role"] == "user"


class _DummyAgent:
    def __init__(self, team: str, role: AgentRole) -> None:
        self.team = team
        self.role = role
        self.last_observation: dict[str, object] = {}

    def observe(self, state_snapshot: dict[str, object]) -> None:
        self.last_observation = dict(state_snapshot)

    def act(self, deadline_ms: int) -> dict[str, object]:
        return {"role": self.role.value, "action": "noop"}
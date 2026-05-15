from __future__ import annotations

from pathlib import Path

from agents.base import AgentBase, AgentRole
from agents.manager import AgentManagerConfig, TeamAgentManager
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import MapData


class SimpleAgent(AgentBase):
    def __init__(self, team: str, role: AgentRole, proposal: dict | None = None) -> None:
        super().__init__(team=team, role=role)
        self._proposal = proposal or {"type": "OMIT"}

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        return dict(self._proposal)

    def act(self, deadline_ms: int) -> dict[str, object]:
        return {"type": "OMIT"}


def _build_state() -> GameState:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    return GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1), "RED": SubmarineState(x=2, y=2)})


def test_iteration_ledger_written(tmp_path: Path) -> None:
    """Run a turn and assert JSON and Markdown iteration ledgers exist and contain expected keys."""
    ledger_dir = tmp_path / "ledgers"
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig(ledger_base_path=ledger_dir))
    manager.register_agent(SimpleAgent("BLUE", AgentRole.CAPTAIN, proposal={"type": "MOVE", "payload": {}}), active=True)
    manager.register_agent(SimpleAgent("BLUE", AgentRole.FIRST_MATE, proposal={"type": "OMIT"}), active=True)
    manager.register_agent(SimpleAgent("BLUE", AgentRole.ENGINEER, proposal={"type": "OMIT"}), active=True)

    state = _build_state()
    manager.activate_agents(state, roles=[AgentRole.CAPTAIN, AgentRole.FIRST_MATE, AgentRole.ENGINEER], duration_ms=10)

    report = manager.run_turn_cycle(state, max_iterations=1)

    # ledger files are written under the configured ledger directory
    base = ledger_dir
    json_path = base / f"turn_{state.turn}_iterations.json"
    md_path = base / f"turn_{state.turn}_iterations.md"

    assert json_path.exists(), f"expected json ledger at {json_path}"
    assert md_path.exists(), f"expected md ledger at {md_path}"

    # basic JSON shape
    import json

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "iterations" in data and isinstance(data["iterations"], list)
    assert "accepted" in data and isinstance(data["accepted"], list)

    # markdown contains header and turn number
    md = md_path.read_text(encoding="utf-8")
    assert "# Turn Iterations" in md
    assert f"- turn_id: {state.turn}" in md

    # cleanup
    try:
        json_path.unlink()
    except Exception:
        pass
    try:
        md_path.unlink()
    except Exception:
        pass

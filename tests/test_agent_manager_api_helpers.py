from __future__ import annotations

from agents.manager import AgentManagerConfig, TeamAgentManager
from agents.base import AgentRole
from captain_sonar.game_state import SubmarineState, GameState
from captain_sonar.map_loader import MapData


def _build_state() -> GameState:
    map_data = MapData(width=5, height=5, tiles=[["."] * 5 for _ in range(5)])
    return GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=2, y=2), "RED": SubmarineState(x=4, y=4)})


def test_get_state_snapshot_returns_dict() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig())
    state = _build_state()
    snap = manager.get_state_snapshot(state)
    assert isinstance(snap, dict)
    assert "turn" in snap


def test_get_possible_actions_for_role_with_state() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig())
    state = _build_state()
    actions = manager.get_possible_actions(AgentRole.CAPTAIN, state=state)
    assert isinstance(actions, list)
    assert actions
    # captain actions should include MOVE or SURFACE action kinds
    kinds = {a.get("action_kind") for a in actions if isinstance(a, dict)}
    assert any(k in {"MOVE", "SURFACE"} for k in kinds)

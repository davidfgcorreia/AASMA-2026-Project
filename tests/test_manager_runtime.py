from __future__ import annotations

from agents.base import AgentRole
from agents.manager.runtime import build_game_state, build_team_agent_manager, start_team_turn
from agents.manager import AgentManagerConfig


def test_build_team_agent_manager_registers_default_roles() -> None:
    manager = build_team_agent_manager("BLUE", config=AgentManagerConfig())

    assert set(manager.agents) == {
        AgentRole.CAPTAIN,
        AgentRole.FIRST_MATE,
        AgentRole.ENGINEER,
        AgentRole.RADIO_OPERATOR,
    }


def test_start_team_turn_runs_one_cycle() -> None:
    state = build_game_state(
        "assets/maps/default_map.json",
        {"BLUE": (1, 1), "RED": (8, 8)},
    )
    manager = build_team_agent_manager("BLUE", config=AgentManagerConfig())

    report = start_team_turn(manager, state, max_iterations=1, deadline_ms=0)

    assert report["turn_id"] == 1
    assert "iterations" in report
    assert report["iterations"]
    assert state.turn == 1
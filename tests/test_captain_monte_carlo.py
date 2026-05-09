from __future__ import annotations

from agents.captain.agent import CaptainAgent


def test_captain_monte_carlo_selects_best_action() -> None:
    captain = CaptainAgent("BLUE")
    team_view = {
        "team": "BLUE",
        "turn": 3,
        "own_submarine": {"x": 1, "y": 1, "damage": 0},
        "system_utilization": {"ready": {"torpedo": True}},
        "radio_operator": {"confidence": 0.8},
        "last_action_system": False,
        "skip_turns": 0,
    }
    candidates = [
        {"type": "MOVE", "payload": {"direction": "N"}},
        {"type": "TORPEDO", "payload": {"target": {"x": 1, "y": 3}}},
    ]

    result = captain.monte_carlo_exploration(team_view, candidates, rollouts=8, seed=7)

    assert result["selected_action"]["type"] == "TORPEDO"
    assert len(result["scores"]) == 2
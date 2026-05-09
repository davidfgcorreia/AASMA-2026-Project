from __future__ import annotations

from agents.captain.agent import CaptainAgent
from agents.engineer.agent import EngineerAgent
from agents.first_mate.agent import FirstMateAgent
from agents.radio_operator.agent import RadioOperatorAgent
from captain_sonar.possible_actions import all_possible_actions, possible_actions_for_role


def test_all_possible_actions_has_core_rulebook_actions() -> None:
    actions = all_possible_actions()
    action_types = {item["type"] for item in actions}

    assert {"MOVE", "SILENCE", "TORPEDO", "MINE", "TRIGGER_MINE", "DRONE", "SONAR", "REPAIR", "SURFACE"}.issubset(action_types)


def test_propose_action_exists_for_all_roles() -> None:
    team_view = {
        "team": "BLUE",
        "turn": 1,
        "map": {"width": 5, "height": 5},
        "own_submarine": {"x": 2, "y": 2, "damage": 0},
        "own_gauges": {"torpedo": 2, "mine": 1, "sonar": 0, "drone": 0, "silence": 0, "scenario": 0},
        "system_utilization": {"ready": {"torpedo": True, "sonar": False, "drone": False}},
        "engineer_board": {"buttons_by_direction": {"N": [{"button_id": "N-not-green-0", "slot_index": 0, "circuit_part": "not", "function_type": "green"}]}},
        "radio_operator": {"most_likely_position": {"x": 3, "y": 3}, "most_likely_sector": 2, "confidence": 0.7},
        "own_routes": [],
    }

    captain = CaptainAgent("BLUE")
    first_mate = FirstMateAgent("BLUE")
    engineer = EngineerAgent("BLUE")
    radio = RadioOperatorAgent("BLUE")

    captain_proposal = captain.propose_action(team_view)
    first_mate_proposal = first_mate.propose_action(team_view)
    engineer_proposal = engineer.propose_action(team_view)
    radio_proposal = radio.propose_action(team_view)

    assert captain_proposal["role"] == "captain"
    assert "first_step" in captain_proposal
    assert "possible_actions" in captain_proposal
    assert first_mate_proposal["first_step"]["type"] == "CHARGE"
    assert engineer_proposal["first_step"]["type"] == "ENGINEER_SELECTION"
    assert radio_proposal["first_step"]["type"] == "TRACK"


def test_role_possible_actions_are_role_specific() -> None:
    team_view = {"team": "BLUE", "own_submarine": {"x": 2, "y": 2}, "map": {"width": 5, "height": 5}}

    captain_actions = possible_actions_for_role("captain", team_view)
    engineer_actions = possible_actions_for_role("engineer", team_view)

    assert any(item["type"] == "MOVE" for item in captain_actions)
    assert any(item["type"] == "ENGINEER_SELECTION" for item in engineer_actions)
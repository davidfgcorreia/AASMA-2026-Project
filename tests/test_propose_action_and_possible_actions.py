from __future__ import annotations

from agents.captain.agent import CaptainAgent
from agents.engineer.agent import EngineerAgent
from agents.first_mate.agent import FirstMateAgent
from agents.radio_operator.agent import RadioOperatorAgent
from captain_sonar.api import create_game_state, get_team_view
from captain_sonar.actions import Action, ActionType
from captain_sonar.engineer_layout import ENGINEER_BUTTON_SPECS
from captain_sonar.game_state import SubmarineState
from captain_sonar.map_loader import MapData
from captain_sonar.possible_actions import all_possible_actions, possible_actions_for_role
import json


def build_full_team_view(team: str = "BLUE") -> dict[str, object]:
    # Test game view: a simple open 5x5 map with BLUE and RED submarines placed far apart,
    # then updated gauges so the captain action tree includes movement, loading, and activation branches.
    map_data = MapData(width=5, height=5, tiles=[["."] * 5 for _ in range(5)])
    state = create_game_state(
        map_data,
        subs={
            "BLUE": SubmarineState(x=2, y=2),
            "RED": SubmarineState(x=4, y=4),
        },
    )
    state.apply_actions(
        [
            Action(actor="BLUE", type=ActionType.MOVE, payload={"direction": "N", "charge": "torpedo"}),
            Action(actor="RED", type=ActionType.MOVE, payload={"direction": "W", "charge": "sonar"}),
        ]
    )
    state.gauges["BLUE"]["torpedo"] = 4
    state.gauges["BLUE"]["sonar"] = 0
    state.gauges["BLUE"]["drone"] = 0
    state.gauges["BLUE"]["mine"] = 0
    return get_team_view(state, team)


def build_state_view_near_island() -> dict[str, object]:
    tiles = [
        [".", "#", "."],
        [".", ".", "."],
        [".", ".", "."],
    ]
    map_data = MapData(width=3, height=3, tiles=tiles)
    state = create_game_state(
        map_data,
        subs={
            "BLUE": SubmarineState(x=1, y=1),
            "RED": SubmarineState(x=2, y=2),
        },
    )
    return get_team_view(state, "BLUE")


def build_state_view_with_crossed_button(direction: str) -> dict[str, object]:
    map_data = MapData(width=5, height=5, tiles=[["."] * 5 for _ in range(5)])
    state = create_game_state(
        map_data,
        subs={
            "BLUE": SubmarineState(x=2, y=2),
            "RED": SubmarineState(x=4, y=4),
        },
    )
    spec = ENGINEER_BUTTON_SPECS[direction][0]
    state.breakdowns["BLUE"].crossed_by_direction[direction].add(spec.button_id)
    return get_team_view(state, "BLUE")


def assert_action_schema(action: dict[str, object]) -> None:
    """Validate action schema. Handles both tree format (captain) and phase format (catalog)."""
    assert isinstance(action.get("action_kind"), str)

    # Captain actions now use the tree layout.
    if action["action_kind"] in {"MOVE", "SURFACE"} and (
        "directions" in action or "engineer_picks" in action or "system_hypotheses" in action
    ):
        assert_tree_action_schema(action)
    # Otherwise check phase format (catalog actions)
    else:
        assert_phase_action_schema(action)


def assert_tree_action_schema(action: dict[str, object]) -> None:
    """Validate tree-structured action (captain role)."""
    assert isinstance(action.get("action_kind"), str)
    if action["action_kind"] == "MOVE":
        assert isinstance(action.get("directions"), list)
        assert len(action["directions"]) > 0
        for direction_branch in action["directions"]:
            assert isinstance(direction_branch, dict)
            assert direction_branch.get("direction") in {"N", "S", "E", "W"}
            assert isinstance(direction_branch.get("load_systems"), list)
            assert isinstance(direction_branch.get("system_hypotheses"), list)
            assert len(direction_branch["load_systems"]) > 0
            assert len(direction_branch["system_hypotheses"]) > 0
            for load_branch in direction_branch["load_systems"]:
                assert isinstance(load_branch, dict)
                assert isinstance(load_branch.get("load_system"), str)
                assert isinstance(load_branch.get("engineer_picks"), list)
                for engineer_selection in load_branch["engineer_picks"]:
                    if engineer_selection != "NONE":
                        assert isinstance(engineer_selection, dict)
                        assert "direction" in engineer_selection
                        assert engineer_selection.get("system_to_load") == load_branch.get("load_system")
                        assert isinstance(engineer_selection.get("possible_activations"), list)
                        assert len(engineer_selection.get("possible_activations", [])) > 0
                        assert "slot_index" in engineer_selection
                        assert "circuit_part" in engineer_selection
                        assert "function_type" in engineer_selection
            for activation in direction_branch["system_hypotheses"]:
                assert isinstance(activation, (str, dict))
                if isinstance(activation, dict):
                    assert "type" in activation
    else:
        assert "engineer_picks" in action
        assert "system_hypotheses" in action
        assert isinstance(action.get("engineer_picks"), list)
        assert isinstance(action.get("system_hypotheses"), list)
        assert action["engineer_picks"] == ["NONE"]
        assert action["system_hypotheses"] == ["NONE"]


def assert_phase_action_schema(action: dict[str, object]) -> None:
    """Validate phase-structured action (catalog)."""
    phase_1 = action.get("phase_1")
    phase_2 = action.get("phase_2")
    assert isinstance(phase_1, dict)
    assert isinstance(phase_2, dict)
    assert set(phase_1.keys()) == {"movement", "load_system", "engineer_selection"}
    assert set(phase_2.keys()) == {"activate_system"}

    movement = phase_1["movement"]
    assert isinstance(movement, dict)
    assert "type" in movement
    if movement["type"] in {"MOVE", "SILENCE"}:
        assert "direction" in movement
    if movement["type"] == "SILENCE":
        if "steps" in movement:
            assert isinstance(movement["steps"], int)

    assert isinstance(phase_1["load_system"], str)
    activate_system = phase_2["activate_system"]
    assert isinstance(activate_system, (str, dict))

    engineer_selection = phase_1["engineer_selection"]
    if engineer_selection != "NONE":
        assert isinstance(engineer_selection, dict)
        assert "direction" in engineer_selection
        assert "slot_index" in engineer_selection
        assert "circuit_part" in engineer_selection
        assert "function_type" in engineer_selection

    # role_action removed from phase_1; action-specific payloads live in phase_2.activate_system now

    if isinstance(activate_system, dict):
        assert "type" in activate_system
        payload = activate_system.get("payload", {})
        if activate_system["type"] == "SILENCE":
            if "coordinates" in payload:
                assert isinstance(payload["coordinates"], list)
            else:
                assert "direction" in payload
                assert "steps" in payload
        if activate_system["type"] == "DRONE":
            assert "sectors" in payload
            assert payload["sectors"] == list(range(1, 10))


def test_all_possible_actions_has_core_rulebook_actions() -> None:
    actions = all_possible_actions()
    action_kinds = {item["action_kind"] for item in actions}

    assert {"MOVE", "SILENCE", "TORPEDO", "MINE", "TRIGGER_MINE", "DRONE", "SONAR", "REPAIR", "SURFACE"}.issubset(action_kinds)


def test_propose_action_exists_for_all_roles() -> None:
    team_view = build_full_team_view()

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

    for proposal in (captain_proposal, first_mate_proposal, engineer_proposal, radio_proposal):
        possible_actions = proposal["possible_actions"]
        assert possible_actions
        for action in possible_actions:
            assert_action_schema(action)


def test_role_possible_actions_are_role_specific() -> None:
    team_view = build_full_team_view()

    captain_actions = possible_actions_for_role("captain", team_view)
    engineer_actions = possible_actions_for_role("engineer", team_view)

    assert any(item["action_kind"] == "MOVE" for item in captain_actions)
    assert any(item["action_kind"] == "ENGINEER_SELECTION" for item in engineer_actions)


def test_all_possible_actions_match_schema() -> None:
    actions = all_possible_actions()
    for action in actions:
        assert_action_schema(action)


def test_team_blue_possible_actions_from_full_state() -> None:
    team_view = build_full_team_view("BLUE")
    actions = possible_actions_for_role("captain", team_view)
    assert actions
    for action in actions:
        assert_action_schema(action)
        if action.get("action_kind") == "MOVE":
            directions = action.get("directions", [])
            assert len(directions) > 0
            for direction_branch in directions:
                direction = direction_branch.get("direction")
                assert direction in {"N", "S", "E", "W"}
                assert isinstance(direction_branch.get("system_hypotheses"), list)
                for load_branch in direction_branch.get("load_systems", []):
                    assert isinstance(load_branch.get("load_system"), str)
                    assert len(load_branch.get("engineer_picks", [])) > 0
                    for engineer_selection in load_branch.get("engineer_picks", []):
                        if engineer_selection != "NONE":
                            assert engineer_selection.get("direction") == direction
                            assert engineer_selection.get("system_to_load") == load_branch.get("load_system")
                            assert isinstance(engineer_selection.get("possible_activations"), list)
                            assert len(engineer_selection.get("possible_activations", [])) > 0
        if action.get("action_kind") == "SURFACE":
            assert action.get("engineer_picks") == ["NONE"]
            assert action.get("system_hypotheses") == ["NONE"]


def test_captain_actions_block_island_direction() -> None:
    team_view = build_state_view_near_island()
    actions = possible_actions_for_role("captain", team_view)
    move_action = next(action for action in actions if action.get("action_kind") == "MOVE")
    move_north = any(
        direction_branch.get("direction") == "N"
        for direction_branch in move_action.get("directions", [])
    )
    assert move_north is False


def test_first_mate_does_not_suggest_fully_charged_system() -> None:
    team_view = build_full_team_view("BLUE")
    team_view["system_utilization"]["ready"]["torpedo"] = True
    actions = possible_actions_for_role("first_mate", team_view)
    charge_actions = [
        action
        for action in actions
        if action.get("action_kind") == "CHARGE"
    ]
    assert charge_actions
    for action in charge_actions:
        load_system = action.get("phase_1", {}).get("load_system")
        assert load_system != "torpedo"


def test_engineer_actions_skip_crossed_button() -> None:
    team_view = build_state_view_with_crossed_button("N")
    actions = possible_actions_for_role("engineer", team_view)
    crossed_id = ENGINEER_BUTTON_SPECS["N"][0].button_id
    suggested_ids = [
        action.get("phase_1", {}).get("engineer_selection", {}).get("button_id")
        for action in actions
        if action.get("action_kind") == "ENGINEER_SELECTION"
    ]
    assert crossed_id not in suggested_ids


def test_system_activation_respects_charge_and_breakdowns() -> None:
    team_view = build_full_team_view("BLUE")
    team_view["system_utilization"]["ready"]["torpedo"] = True
    team_view["system_utilization"]["ready"]["drone"] = True
    team_view["system_utilization"]["ready"]["sonar"] = False
    team_view["own_gauges"]["drone"] = 3
    sonar_button = next(
        spec
        for specs in ENGINEER_BUTTON_SPECS.values()
        for spec in specs
        if spec.function_type == "yellow"
    )
    for entry in team_view["engineer_board"]["buttons_by_direction"][sonar_button.direction]:
        if entry["button_id"] == sonar_button.button_id:
            entry["crossed"] = True
            break

    actions = possible_actions_for_role("captain", team_view)
    all_activations = []
    for action in actions:
        if action.get("action_kind") != "MOVE":
            continue
        for direction_branch in action.get("directions", []):
            all_activations.extend(direction_branch.get("system_hypotheses", []))

    has_torpedo = any(
        isinstance(item, dict) and item.get("type") == "torpedo" for item in all_activations
    )
    has_sonar = any(
        item == "sonar" or (isinstance(item, dict) and item.get("type") == "sonar")
        for item in all_activations
    )
    assert has_torpedo is True
    assert has_sonar is False

    torpedo_activation = next(
        item for item in all_activations if isinstance(item, dict) and item.get("type") == "torpedo"
    )
    torpedo_targets = torpedo_activation.get("payload", {}).get("targets", [])
    assert isinstance(torpedo_targets, list)
    assert len(torpedo_targets) > 0
    assert all(isinstance(target, dict) and {"x", "y"}.issubset(target.keys()) for target in torpedo_targets)


def test_team_view_includes_trajectories() -> None:
    team_view = build_full_team_view()
    assert team_view["own_trajectory"] == [{"x": 2, "y": 2}, {"x": 2, "y": 1}]
    assert team_view["enemy_trajectory_predicted"] == ["W"]


def test_debug_print_actions() -> None:
    """Temporary debug test: print catalog and captain actions for BLUE."""
    team_view = build_full_team_view("BLUE")
    captain_actions = possible_actions_for_role("captain", team_view)
    # Generated game state: an empty 5x5 map with BLUE at the center and RED in the
    # bottom-right corner, plus boosted BLUE gauges so the captain tree exposes most branches.
    print("\n=== CAPTAIN_POSSIBLE_ACTIONS (BLUE) ===")
    print(json.dumps(captain_actions, indent=2, default=str))


def test_engineer_board_crossing_blocks_systems() -> None:
    """Test that crossed engineer buttons block corresponding systems."""
    team_view = build_full_team_view("BLUE")
    
    # Cross a red button (blocks torpedo and mine)
    red_button = next(
        spec
        for specs in ENGINEER_BUTTON_SPECS.values()
        for spec in specs
        if spec.function_type == "red"
    )
    for entry in team_view["engineer_board"]["buttons_by_direction"][red_button.direction]:
        if entry["button_id"] == red_button.button_id:
            entry["crossed"] = True
            break
    
    actions = possible_actions_for_role("captain", team_view)
    move_action = next(action for action in actions if action.get("action_kind") == "MOVE")
    
    # Verify no torpedo or mine in any direction's activations
    for direction_branch in move_action.get("directions", []):
        activations = direction_branch.get("system_hypotheses", [])
        
        # Check that torpedo and mine are not in hypotheses
        has_torpedo = any(
            isinstance(item, dict) and item.get("type") == "torpedo" for item in activations
        )
        has_mine = any(
            isinstance(item, dict) and item.get("type") == "mine" for item in activations
        )
        
        assert not has_torpedo, f"Torpedo should be blocked by red crossed button in {direction_branch.get('direction')}"
        assert not has_mine, f"Mine should be blocked by red crossed button in {direction_branch.get('direction')}"
        
        # Check that engineer picks don't have torpedo or mine activations
        for load_branch in direction_branch.get("load_systems", []):
            for engineer_pick in load_branch.get("engineer_picks", []):
                if engineer_pick != "NONE":
                    activations = engineer_pick.get("possible_activations", [])
                    assert "torpedo" not in activations
                    assert "mine" not in activations


def test_captain_cannot_move_to_visited_positions() -> None:
    """Test that captain cannot move back to already-visited positions."""
    team_view = build_full_team_view("BLUE")
    
    # own_trajectory shows BLUE moved from (2,2) to (2,1)
    # So moving SOUTH (back to 2,2) should be blocked
    actions = possible_actions_for_role("captain", team_view)
    move_action = next(action for action in actions if action.get("action_kind") == "MOVE")
    
    # Check that direction N is available (moving to 2,0)
    has_north = any(d.get("direction") == "N" for d in move_action.get("directions", []))
    assert has_north is True, "North should be available (new position)"
    
    # Check that direction S is NOT available (would move back to 2,2 which was visited)
    has_south = any(d.get("direction") == "S" for d in move_action.get("directions", []))
    assert has_south is False, "South should be blocked (already visited 2,2)"


def first_activation_hypothesis(options: list[object]) -> object:
    for option in options:
        if option != "NONE":
            if isinstance(option, dict):
                return option.get("type", "NONE")
            return option
    return "NONE"
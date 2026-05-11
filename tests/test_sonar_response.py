"""Test sonar response handling with defender's choices."""

from captain_sonar.actions import Action, ActionType
from captain_sonar.config import GAUGE_MAX_DEFAULT
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import load_map


def test_sonar_with_defender_choice():
    """Test that sonar correctly uses defender's chosen false type and value."""
    map_data = load_map("assets/maps/default_map.json")
    subs = {
        "RED": SubmarineState(x=7, y=7, damage=0),
        "BLUE": SubmarineState(x=3, y=4, damage=0),
    }
    state = GameState(map_data=map_data, subs=subs)
    
    # Charge the sonar system
    state.gauges["RED"]["sonar"] = GAUGE_MAX_DEFAULT

    # RED activates sonar, requesting row info, and BLUE chooses:
    # - true_type: row (what RED requested)
    # - false_type: col
    # - false_value: 5
    action = Action(
        actor="RED",
        type=ActionType.SONAR,
        payload={"true_type": "row", "false_type": "col", "false_value": 5},
    )
    state.apply_actions([action])

    # Find the sonar event
    sonar_events = [e for e in state.events if e["type"] == "sonar"]
    assert len(sonar_events) == 1

    event = sonar_events[0]
    assert event["actor"] == "RED"
    assert event["true_info"]["type"] == "row"
    assert event["true_info"]["value"] == "E"  # BLUE is at (3, 4) -> row E (5th row, 0-indexed)
    assert event["false_info"]["type"] == "col"
    assert event["false_info"]["value"] == 5


def test_sonar_all_type_combinations():
    """Test all possible true/false type combinations."""
    map_data = load_map("assets/maps/default_map.json")
    subs = {
        "RED": SubmarineState(x=0, y=0, damage=0),
        "BLUE": SubmarineState(x=5, y=5, damage=0),
    }

    test_cases = [
        ("row", "col", 3),
        ("row", "sector", 5),
        ("col", "row", 7),
        ("col", "sector", 2),
        ("sector", "row", 8),
        ("sector", "col", 10),
    ]

    for true_type, false_type, false_value in test_cases:
        state = GameState(map_data=map_data, subs=subs)
        state.gauges["RED"]["sonar"] = GAUGE_MAX_DEFAULT

        action = Action(
            actor="RED",
            type=ActionType.SONAR,
            payload={
                "true_type": true_type,
                "false_type": false_type,
                "false_value": false_value,
            },
        )
        state.apply_actions([action])

        event = state.events[-1]
        assert event["type"] == "sonar"
        assert event["true_info"]["type"] == true_type
        assert event["false_info"]["type"] == false_type
        assert event["false_info"]["value"] == false_value
        assert event["true_info"]["type"] != event["false_info"]["type"]


def test_sonar_fallback_to_defaults():
    """Test that sonar falls back to default behavior when choices not provided."""
    map_data = load_map("assets/maps/default_map.json")
    subs = {
        "RED": SubmarineState(x=0, y=0, damage=0),
        "BLUE": SubmarineState(x=5, y=5, damage=0),
    }
    state = GameState(map_data=map_data, subs=subs)
    state.gauges["RED"]["sonar"] = GAUGE_MAX_DEFAULT

    # No true_type, false_type, false_value provided - should use defaults
    action = Action(actor="RED", type=ActionType.SONAR, payload={})
    state.apply_actions([action])

    event = state.events[-1]
    assert event["type"] == "sonar"
    assert event["true_info"]["type"] in ("row", "col", "sector")
    assert event["false_info"]["type"] in ("row", "col", "sector")
    assert event["true_info"]["type"] != event["false_info"]["type"]


def test_sonar_rejects_invalid_false_types():
    """Test that sonar rejects invalid type combinations."""
    map_data = load_map("assets/maps/default_map.json")
    subs = {
        "RED": SubmarineState(x=0, y=0, damage=0),
        "BLUE": SubmarineState(x=5, y=5, damage=0),
    }
    state = GameState(map_data=map_data, subs=subs)
    state.gauges["RED"]["sonar"] = GAUGE_MAX_DEFAULT

    # Same type for true and false - should default the false_type
    action = Action(
        actor="RED",
        type=ActionType.SONAR,
        payload={
            "true_type": "row",
            "false_type": "row",  # Invalid - same as true_type
            "false_value": 3,
        },
    )
    state.apply_actions([action])

    event = state.events[-1]
    assert event["true_info"]["type"] == "row"
    # False type should be adjusted to a different one
    assert event["false_info"]["type"] != "row"


def test_get_sonar_response_options():
    """Test that sonar response options are returned correctly."""
    map_data = load_map("assets/maps/default_map.json")
    subs = {
        "RED": SubmarineState(x=0, y=0, damage=0),
        "BLUE": SubmarineState(x=5, y=5, damage=0),
    }
    state = GameState(map_data=map_data, subs=subs)
    state.gauges["BLUE"]["sonar"] = GAUGE_MAX_DEFAULT

    options = state.get_sonar_response_options("BLUE")

    assert isinstance(options, dict)
    assert "row" in options or "col" in options or "sector" in options
    # Each option should be a list (of possible values)
    for key, values in options.items():
        assert isinstance(values, list)
        for value in values:
            assert isinstance(value, (int, str))


def test_sonar_with_invalid_true_type():
    """Test that invalid true_type defaults to rotation."""
    map_data = load_map("assets/maps/default_map.json")
    subs = {
        "RED": SubmarineState(x=0, y=0, damage=0),
        "BLUE": SubmarineState(x=5, y=5, damage=0),
    }
    state = GameState(map_data=map_data, subs=subs)
    state.gauges["RED"]["sonar"] = GAUGE_MAX_DEFAULT
    
    initial_turn = state.turn

    # Invalid true_type - should default to turn%3 rotation
    action = Action(
        actor="RED",
        type=ActionType.SONAR,
        payload={"true_type": "invalid_type"},
    )
    state.apply_actions([action])

    event = state.events[-1]
    # Should use default rotation by turn number (use initial_turn, not state.turn after action)
    expected_type = ["row", "col", "sector"][initial_turn % 3]
    assert event["true_info"]["type"] == expected_type


def test_sonar_consumes_gauge():
    """Test that sonar still consumes gauge after response handling."""
    map_data = load_map("assets/maps/default_map.json")
    subs = {
        "RED": SubmarineState(x=0, y=0, damage=0),
        "BLUE": SubmarineState(x=5, y=5, damage=0),
    }
    state = GameState(map_data=map_data, subs=subs)
    state.gauges["RED"]["sonar"] = GAUGE_MAX_DEFAULT

    initial_gauge = state.gauges["RED"]["sonar"]
    assert initial_gauge > 0

    action = Action(
        actor="RED",
        type=ActionType.SONAR,
        payload={"true_type": "row", "false_type": "col", "false_value": 5},
    )
    state.apply_actions([action])

    final_gauge = state.gauges["RED"]["sonar"]
    assert final_gauge < initial_gauge


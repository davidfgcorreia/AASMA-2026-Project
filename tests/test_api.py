from captain_sonar.actions import Action, ActionType
from captain_sonar.api import apply_actions, get_engineer_board_state, get_system_utilization, get_team_view, snapshot_game_state
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import MapData


def test_snapshot_is_json_friendly_and_detached() -> None:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(
        map_data=map_data,
        subs={
            "BLUE": SubmarineState(x=1, y=1),
            "RED": SubmarineState(x=2, y=2),
        },
    )

    snapshot = snapshot_game_state(state)
    snapshot["submarines"]["BLUE"]["x"] = 99

    assert snapshot["turn"] == 0
    assert snapshot["submarines"]["BLUE"]["x"] == 99
    assert state.subs["BLUE"].x == 1
    assert isinstance(snapshot["routes"]["BLUE"], list)
    assert isinstance(snapshot["mines"], list)


def test_team_view_exposes_agent_facing_state_without_enemy_position() -> None:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(
        map_data=map_data,
        subs={
            "BLUE": SubmarineState(x=1, y=1),
            "RED": SubmarineState(x=2, y=2),
        },
    )

    view = get_team_view(state, "BLUE")

    assert view["team"] == "BLUE"
    assert view["own_submarine"] == {"x": 1, "y": 1, "damage": 0}
    assert view["radio_operator"] is not None
    assert "enemy_submarine" not in view


def test_apply_actions_wrapper_orders_and_applies_actions() -> None:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1)})

    apply_actions(
        state,
        [Action(actor="BLUE", type=ActionType.MOVE, payload={"direction": "E", "charge": "torpedo"})],
    )

    assert state.turn == 1
    assert state.subs["BLUE"].x == 2


def test_system_utilization_exposes_charge_levels_and_readiness() -> None:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1)})
    state.gauges["BLUE"]["torpedo"] = 2

    utilization = get_system_utilization(state, "BLUE")

    assert utilization["team"] == "BLUE"
    assert utilization["gauges"]["torpedo"] == 2
    assert utilization["utilization"]["torpedo"] == 0.5
    assert utilization["ready"]["torpedo"] is False


def test_engineer_board_state_exposes_button_metadata() -> None:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1)})

    board = get_engineer_board_state(state, "BLUE")

    assert board is not None
    assert board["team"] == "BLUE"
    assert "W" in board["buttons_by_direction"]
    assert board["buttons_by_direction"]["W"][0]["button_id"] == "W-not-green-0"
    assert board["buttons_by_direction"]["W"][0]["crossed"] is False
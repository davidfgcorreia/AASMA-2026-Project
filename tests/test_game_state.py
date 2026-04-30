from captain_sonar.actions import Action, ActionType
from captain_sonar.config import SURFACE_SKIP_TURNS
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import MapData


def test_move_blocked():
    map_data = MapData(width=2, height=2, tiles=[["#", "."], [".", "."]])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=0, y=0)})
    action = Action(actor="BLUE", type=ActionType.MOVE, payload={"direction": "E"})
    state.apply_actions([action])
    assert state.subs["BLUE"].x == 0
    assert state.skip_turns["BLUE"] == SURFACE_SKIP_TURNS


def test_torpedo_out_of_range_does_not_consume():
    map_data = MapData(width=5, height=5, tiles=[["."] * 5 for _ in range(5)])
    state = GameState(
        map_data=map_data,
        subs={
            "BLUE": SubmarineState(x=0, y=0),
            "RED": SubmarineState(x=4, y=4),
        },
    )
    state.gauges["BLUE"]["torpedo"] = 4
    action = Action(actor="BLUE", type=ActionType.TORPEDO, payload={"target": {"x": 4, "y": 4}})
    state.apply_actions([action])
    assert state.gauges["BLUE"]["torpedo"] == 4


def test_mine_explodes_on_enemy():
    map_data = MapData(width=3, height=3, tiles=[["."] * 3 for _ in range(3)])
    state = GameState(
        map_data=map_data,
        subs={
            "BLUE": SubmarineState(x=0, y=0),
            "RED": SubmarineState(x=1, y=0),
        },
    )
    state.gauges["BLUE"]["mine"] = 4
    deploy = Action(actor="BLUE", type=ActionType.MINE, payload={"target": {"x": 1, "y": 0}})
    move = Action(actor="BLUE", type=ActionType.MOVE, payload={"direction": "S", "charge": "torpedo"})
    trigger = Action(actor="BLUE", type=ActionType.TRIGGER_MINE, payload={"target": {"x": 1, "y": 0}})
    state.apply_actions([deploy])
    state.apply_actions([move])
    state.apply_actions([trigger])
    assert state.subs["RED"].damage > 0

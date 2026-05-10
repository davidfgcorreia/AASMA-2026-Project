from captain_sonar.actions import Action, ActionType
from captain_sonar.config import SURFACE_SKIP_TURNS, WINDOW_PADDING
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.engineer_layout import ENGINEER_BUTTON_SPECS, engineer_board_geometry
from captain_sonar.human_controller import HumanController
from captain_sonar.map_loader import MapData
import pygame


def test_move_blocked():
    map_data = MapData(width=3, height=2, tiles=[[".", ".", "."], [".", ".", "."]])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=0)})
    state.apply_actions([Action(actor="BLUE", type=ActionType.MOVE, payload={"direction": "S"})])

    action = Action(actor="BLUE", type=ActionType.MOVE, payload={"direction": "N"})
    state.apply_actions([action])

    assert state.subs["BLUE"].x == 1
    assert state.subs["BLUE"].y == 1
    assert state.skip_turns["BLUE"] == 0
    assert any(e["type"] == "action_rejected" for e in state.events)


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


def test_p_toggles_engineer_board_view():
    controller = HumanController(team="BLUE")

    assert controller.ui_state()["show_engineer_board"] is False

    handled = controller._handle_key(pygame.K_p)

    assert handled is True
    assert controller.ui_state()["show_engineer_board"] is True


def test_breakdown_stamps_move_and_blocks_systems():
    map_data = MapData(width=3, height=3, tiles=[["."] * 3 for _ in range(3)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1)})

    action = Action(
        actor="BLUE",
        type=ActionType.MOVE,
        payload={
            "direction": "N",
            "charge": "torpedo",
            "breakdown_choice": {
                "button_id": "N-central-red-3",
                "direction": "N",
                "slot": 3,
                "circuit_part": "central",
                "function_type": "red",
            },
        },
    )
    state.apply_actions([action])

    assert "N-central-red-3" in state.breakdowns["BLUE"].crossed_by_direction["N"]
    assert state._system_has_breakdown("BLUE", "torpedo") is True
    assert state._system_has_breakdown("BLUE", "mine") is True
    assert state._system_has_breakdown("BLUE", "drone") is False


def test_circuit_self_repair_and_surface_clear_breakdowns():
    map_data = MapData(width=3, height=3, tiles=[["."] * 3 for _ in range(3)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1)})

    top_ids = {
        spec.button_id
        for specs in ENGINEER_BUTTON_SPECS.values()
        for spec in specs
        if spec.circuit_part == "top"
    }
    for direction in state.breakdowns["BLUE"].crossed_by_direction:
        direction_ids = {
            button_id for button_id in top_ids if button_id.startswith(f"{direction}-")
        }
        state.breakdowns["BLUE"].crossed_by_direction[direction].update(direction_ids)

    repaired = state._repair_circuits("BLUE")
    assert "top_circuit" in repaired
    assert all(
        all(not button_id.startswith(f"{direction}-top-") for button_id in symbols)
        for direction, symbols in state.breakdowns["BLUE"].crossed_by_direction.items()
    )

    state._apply_breakdown("BLUE", "N")
    state._resolve_surface("BLUE", forced=False)

    assert all(not symbols for symbols in state.breakdowns["BLUE"].crossed_by_direction.values())


def test_engineer_board_click_updates_choice_and_queue_payload():
    map_data = MapData(width=3, height=3, tiles=[["."] * 3 for _ in range(3)])
    controller = HumanController(team="BLUE")
    controller.map_data = map_data
    controller.show_engineer_board = True

    layout = engineer_board_geometry(controller._map_width_px() + 12, WINDOW_PADDING + 32)
    assert len(layout["rows"]["W"]["buttons"]) == 6
    assert layout["rows"]["W"]["button_specs"][0].button_id == "W-not-green-0"
    assert layout["rows"]["W"]["button_specs"][5].circuit_part == "top"

    controller._queue_move("W")
    button_x, button_y = layout["rows"]["W"]["buttons"][4]

    click_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"pos": (button_x, button_y), "button": 1},
    )

    handled = controller.handle_event(click_event, map_data)

    assert handled is True
    assert controller.engineer_direction == "W"
    assert controller.engineer_index == 4

    payload = controller.queue[-1].payload

    assert payload["breakdown_choice"]["button_id"] == "W-top-green-4"
    assert payload["breakdown_choice"]["direction"] == "W"
    assert payload["breakdown_choice"]["slot"] == 4
    assert payload["breakdown_choice"]["circuit_part"] == "top"
    assert payload["breakdown_choice"]["function_type"] == "green"


def test_engineer_second_button_uses_not_circuit_part():
    map_data = MapData(width=3, height=3, tiles=[["."] * 3 for _ in range(3)])
    controller = HumanController(team="BLUE")
    controller.map_data = map_data
    controller.show_engineer_board = True

    layout = engineer_board_geometry(controller._map_width_px() + 12, WINDOW_PADDING + 32)
    button_x, button_y = layout["rows"]["W"]["buttons"][1]

    click_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"pos": (button_x, button_y), "button": 1},
    )

    handled = controller.handle_event(click_event, map_data)

    assert handled is True
    assert controller.engineer_index == 1
    assert controller.engineer_circuit_part == "not"
    assert controller.engineer_function_type == "radioactive"


def test_breakdown_blocks_system_activation():
    map_data = MapData(width=3, height=3, tiles=[["."] * 3 for _ in range(3)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1), "RED": SubmarineState(x=0, y=0)})
    state.gauges["BLUE"]["torpedo"] = 4

    state.apply_actions([
        Action(
            actor="BLUE",
            type=ActionType.MOVE,
            payload={
                "direction": "N",
                "charge": "torpedo",
                "breakdown_choice": {
                    "button_id": "N-central-red-3",
                    "direction": "N",
                    "slot": 3,
                    "circuit_part": "central",
                    "function_type": "red",
                },
            },
        )
    ])

    errors = state._validate_state(Action(actor="BLUE", type=ActionType.TORPEDO, payload={"target": {"x": 1, "y": 0}}))

    assert "torpedo system has breakdown" in errors


def test_radiation_breakdown_deals_damage_and_clears_board():
    map_data = MapData(width=3, height=3, tiles=[["."] * 3 for _ in range(3)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1)})

    radioactive_ids = [
        spec.button_id
        for specs in ENGINEER_BUTTON_SPECS.values()
        for spec in specs
        if spec.function_type == "radioactive"
    ]
    for button_id in radioactive_ids:
        direction = button_id.split("-", 1)[0]
        state.breakdowns["BLUE"].crossed_by_direction[direction].add(button_id)

    state._check_breakdown_effects("BLUE")

    assert state.subs["BLUE"].damage == 1
    assert all(not symbols for symbols in state.breakdowns["BLUE"].crossed_by_direction.values())


def test_complete_area_breakdown_deals_damage_and_clears_board():
    map_data = MapData(width=3, height=3, tiles=[["."] * 3 for _ in range(3)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1)})

    state.breakdowns["BLUE"].crossed_by_direction["N"] = {
        spec.button_id for spec in ENGINEER_BUTTON_SPECS["N"]
    }
    state._check_breakdown_effects("BLUE")

    assert state.subs["BLUE"].damage == 1
    assert all(not symbols for symbols in state.breakdowns["BLUE"].crossed_by_direction.values())


def test_turn_reset_clears_active_action():
    controller = HumanController(team="BLUE")
    controller.active_action = ActionType.TORPEDO
    controller.show_engineer_board = True
    controller.queue.append(Action(actor="BLUE", type=ActionType.MOVE, payload={"direction": "N"}))
    controller.confirmed = True

    controller.reset_turn()

    assert controller.active_action is None
    assert controller.show_engineer_board is True
    assert controller.confirmed is False
    assert controller.queue == []

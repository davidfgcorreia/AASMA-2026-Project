from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, Iterable

from .actions import Action, ActionType, action_to_dict, order_actions
from .config import GAUGE_MAX_DEFAULT
from .engineer_layout import ENGINEER_BUTTON_SPECS, engineer_button_spec_by_id
from .game_state import GameState, SubmarineState
from .map_loader import MapData


def create_game_state(map_data: MapData, subs: dict[str, SubmarineState]) -> GameState:
    """Create a new authoritative game state."""
    return GameState(map_data=map_data, subs=subs)


def apply_action(state: GameState, action: Action | dict[str, Any]) -> None:
    """Apply a single action to the game state."""
    apply_actions(state, [action])


def apply_actions(state: GameState, actions: Iterable[Action | dict[str, Any]]) -> None:
    """Normalize, order, and apply a batch of actions."""
    normalized: list[Action] = []
    for item in actions:
        normalized.extend(_expand_action(item))
    state.apply_actions(order_actions(normalized))


def _expand_action(item: Action | dict[str, Any]) -> list[Action]:
    # Backwards-compatible: accept Action objects directly
    if isinstance(item, Action):
        return [item]
    if not isinstance(item, dict):
        return []

    # New simplified request format: build primary move/surface action
    # and optionally a system activation action.
    raw = dict(item)
    actor = str(raw.get("actor", ""))

    # Determine primary request type
    req_type = raw.get("type")
    if isinstance(req_type, str):
        primary_type_name = req_type.strip().upper()
    else:
        # default to MOVE when direction provided
        primary_type_name = "MOVE" if raw.get("direction") is not None else "END_TURN"

    try:
        primary_action_type = ActionType[primary_type_name]
    except KeyError:
        return []

    primary_payload: dict[str, Any] = {}

    # Movement / surface
    if primary_action_type == ActionType.MOVE:
        direction = raw.get("direction")
        if isinstance(direction, str):
            primary_payload["direction"] = direction
    elif primary_action_type == ActionType.SURFACE:
        primary_payload = {}

    # Charge system to load
    system_to_load = raw.get("system_to_load")
    if isinstance(system_to_load, str):
        primary_payload["charge"] = system_to_load

    # Engineer button selection by id
    button_id = raw.get("engineer_button_id")
    if isinstance(button_id, str):
        spec = engineer_button_spec_by_id(button_id)
        if spec is not None:
            primary_payload["breakdown_choice"] = {
                "button_id": spec.button_id,
                "direction": spec.direction,
                "slot": spec.slot_index,
                "slot_index": spec.slot_index,
                "circuit_part": spec.circuit_part,
                "function_type": spec.function_type,
            }

    primary_action = Action(actor=actor, type=primary_action_type, payload=primary_payload)

    actions: list[Action] = [primary_action]

    # Optional system activation
    activation = raw.get("system_activation") or raw.get("system_to_activate")
    if activation is not None:
        act_type_name = None
        act_payload: dict[str, Any] = {}
        if isinstance(activation, str):
            act_type_name = activation.strip().upper()
        elif isinstance(activation, dict):
            t = activation.get("type")
            if isinstance(t, str):
                act_type_name = t.strip().upper()
            p = activation.get("payload")
            if isinstance(p, dict):
                act_payload = dict(p)

        extra_payload = raw.get("system_activation_payload")
        if isinstance(extra_payload, dict):
            act_payload.update(extra_payload)

        if act_type_name is not None:
            try:
                act_type = ActionType[act_type_name]
            except KeyError:
                act_type = None
            if act_type is not None:
                actions.append(Action(actor=actor, type=act_type, payload=act_payload))

    return actions



def get_turn(state: GameState) -> int:
    return state.turn


def is_game_over(state: GameState) -> bool:
    return state.game_over


def get_winner(state: GameState) -> str | None:
    return state.winner


def get_map_state(state: GameState) -> dict[str, Any]:
    return {
        "width": state.map_data.width,
        "height": state.map_data.height,
        "tiles": [row[:] for row in state.map_data.tiles],
    }


def get_submarine_state(state: GameState, team: str) -> dict[str, Any] | None:
    sub = state.subs.get(team)
    if sub is None:
        return None
    return {"x": sub.x, "y": sub.y, "damage": sub.damage}


def get_all_submarines(state: GameState) -> dict[str, dict[str, Any]]:
    return {
        team: {"x": sub.x, "y": sub.y, "damage": sub.damage}
        for team, sub in state.subs.items()
    }


def get_routes(state: GameState) -> dict[str, list[dict[str, int]]]:
    return {
        team: [{"x": x, "y": y} for x, y in sorted(route)]
        for team, route in state.routes.items()
    }


def get_mines(state: GameState) -> list[dict[str, Any]]:
    return [{"x": mine.x, "y": mine.y, "owner": mine.owner} for mine in state.mines]


def get_gauges(state: GameState, team: str | None = None) -> dict[str, dict[str, int]] | dict[str, int]:
    if team is None:
        return {name: dict(gauges) for name, gauges in state.gauges.items()}
    return dict(state.gauges.get(team, {}))


def get_system_utilization(state: GameState, team: str | None = None) -> dict[str, Any] | dict[str, dict[str, Any]]:
    """Return system charge levels and readiness for one team or all teams."""
    if team is None:
        return {name: get_system_utilization(state, name) for name in state.subs}

    gauges = state.gauges.get(team, {})
    return {
        "team": team,
        "gauges": dict(gauges),
        "utilization": {
            system: (level / GAUGE_MAX_DEFAULT if GAUGE_MAX_DEFAULT else 0.0)
            for system, level in gauges.items()
        },
        "ready": {
            system: state.system_ready(team, system)
            for system in gauges
        },
        "last_action_system": state.last_action_system.get(team, False),
    }


def is_system_ready(state: GameState, team: str, system: str) -> bool:
    return state.system_ready(team, system)


def get_events(state: GameState) -> list[Any]:
    return _freeze(state.events)


def get_radio_operator_state(state: GameState, team: str) -> dict[str, Any] | None:
    radio_operator = state.get_radio_operator(team)
    if radio_operator is None:
        return None
    return {
        "heard_moves": radio_operator.heard_move_sequence(),
        "heard_move_count": radio_operator.heard_move_count(),
        "possible_current_positions": _freeze_cells(radio_operator.possible_current_positions()),
        "possible_starting_positions": _freeze_cells(radio_operator.possible_starting_positions()),
        "most_likely_position": _freeze_point(radio_operator.most_likely_position()),
        "most_likely_sector": radio_operator.most_likely_sector(),
        "sector_probability_masses": _freeze(radio_operator.sector_probability_masses()),
        "confidence": radio_operator.get_confidence_estimate(),
        "belief": _freeze(radio_operator.belief_tracker.heatmap()),
    }


def get_engineer_board_state(state: GameState, team: str) -> dict[str, Any] | None:
    """Return engineer board status and selectable button metadata for a team."""
    breakdown = state.breakdowns.get(team)
    if breakdown is None:
        return None

    crossed_by_direction = {
        direction: sorted(symbols)
        for direction, symbols in breakdown.crossed_by_direction.items()
    }
    crossed_lookup = {
        direction: set(symbols)
        for direction, symbols in crossed_by_direction.items()
    }

    return {
        "team": team,
        "crossed_by_direction": crossed_by_direction,
        "circuits_status": dict(getattr(breakdown, "circuits_status", {})),
        "buttons_by_direction": {
            direction: [
                {
                    "button_id": spec.button_id,
                    "direction": spec.direction,
                    "slot_index": spec.slot_index,
                    "circuit_part": spec.circuit_part,
                    "function_type": spec.function_type,
                    "crossed": spec.button_id in crossed_lookup.get(direction, set()),
                }
                for spec in specs
            ]
            for direction, specs in ENGINEER_BUTTON_SPECS.items()
        },
    }


def get_team_view(state: GameState, team: str) -> dict[str, Any]:
    enemy_team = next((name for name in state.subs if name != team), None)
    radio_operator = state.get_radio_operator(team)
    return {
        "team": team,
        "enemy_team": enemy_team,
        "turn": state.turn,
        "game_over": state.game_over,
        "winner": state.winner,
        "map": get_map_state(state),
        "own_submarine": get_submarine_state(state, team),
        "own_routes": get_routes(state).get(team, []),
        "own_trajectory": [
            {"x": x, "y": y}
            for x, y in state.trajectory.get(team, [])
        ],
        "own_gauges": get_gauges(state, team),
        "system_utilization": get_system_utilization(state, team),
        # Provide a minimal engineer board in the team view to avoid
        # shipping the full UI button metadata every time.
        "engineer_board": (
            None
            if state.breakdowns.get(team) is None
            else {
                "team": team,
                "circuits_status": dict(getattr(state.breakdowns[team], "circuits_status", {})),
                "crossed_by_direction": {
                    direction: sorted(symbols)
                    for direction, symbols in state.breakdowns[team].crossed_by_direction.items()
                },
                "buttons_by_direction": {
                    direction: [
                        {
                            "button_id": spec.button_id,
                            "direction": spec.direction,
                            "slot_index": spec.slot_index,
                            "circuit_part": spec.circuit_part,
                            "function_type": spec.function_type,
                            "crossed": spec.button_id in state.breakdowns[team].crossed_by_direction.get(direction, set()),
                        }
                        for spec in specs
                    ]
                    for direction, specs in ENGINEER_BUTTON_SPECS.items()
                },
            }
        ),
        "last_action_system": state.last_action_system.get(team, False),
        "skip_turns": state.skip_turns.get(team, 0),
        "radio_operator": get_radio_operator_state(state, team),
        "enemy_trajectory_predicted": (
            radio_operator.heard_move_sequence() if radio_operator is not None else []
        ),
        "events": get_events(state),
    }


def snapshot_game_state(state: GameState, turn_id: int | None = None) -> dict[str, Any]:
    """Return a full, JSON-friendly copy of the authoritative game state."""
    return {
        "turn": state.turn if turn_id is None else turn_id,
        "game_over": state.game_over,
        "winner": state.winner,
        "submarines": get_all_submarines(state),
        "routes": get_routes(state),
        "mines": get_mines(state),
        "gauges": get_gauges(state),
        "system_utilization": get_system_utilization(state),
        "last_action_system": dict(state.last_action_system),
        "breakdowns": {
            team: {
                "crossed_by_direction": {
                    direction: sorted(symbols)
                    for direction, symbols in breakdown.crossed_by_direction.items()
                },
                "circuits_status": dict(getattr(breakdown, "circuits_status", {})),
            }
            for team, breakdown in state.breakdowns.items()
        },
        "skip_turns": dict(state.skip_turns),
        "engineer_boards": {
            team: {
                "team": team,
                "circuits_status": dict(getattr(breakdown, "circuits_status", {})),
                "crossed_by_direction": {
                    direction: sorted(symbols)
                    for direction, symbols in breakdown.crossed_by_direction.items()
                },
            }
            for team, breakdown in state.breakdowns.items()
        },
        "radio_operators": {
            team: get_radio_operator_state(state, team)
            for team in state.radio_operators
        },
        "events": get_events(state),
    }


def _freeze(value: Any) -> Any:
    if isinstance(value, Action):
        return action_to_dict(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _freeze(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {key: _freeze(item) for key, item in value.items()}
    if isinstance(value, set):
        return [_freeze(item) for item in sorted(value, key=repr)]
    if isinstance(value, tuple):
        return [_freeze(item) for item in value]
    if isinstance(value, list):
        return [_freeze(item) for item in value]
    return value


def _freeze_cells(cells: Iterable[tuple[int, int]]) -> list[dict[str, int]]:
    return [{"x": x, "y": y} for x, y in sorted(cells)]


def _freeze_point(point: tuple[int, int] | None) -> dict[str, int] | None:
    if point is None:
        return None
    x, y = point
    return {"x": x, "y": y}


def get_sonar_response_options(state: GameState, team: str) -> dict[str, list[int]]:
    """
    Get available false information options for a sonar response.
    Used by agents to understand what choices are available.
    
    Args:
        state: The game state
        team: The defending team (responder)
    
    Returns:
        Dict with keys row/col/sector containing possible false values
    """
    return _freeze(state.get_sonar_response_options(team))
from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, Iterable

from .actions import Action, action_from_dict, action_to_dict, order_actions
from .config import GAUGE_MAX_DEFAULT
from .engineer_layout import ENGINEER_BUTTON_SPECS
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
        if isinstance(item, Action):
            normalized.append(item)
        else:
            normalized.append(action_from_dict(item))
    state.apply_actions(order_actions(normalized))


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
    return {
        "team": team,
        "enemy_team": enemy_team,
        "turn": state.turn,
        "game_over": state.game_over,
        "winner": state.winner,
        "map": get_map_state(state),
        "own_submarine": get_submarine_state(state, team),
        "own_routes": get_routes(state).get(team, []),
        "own_gauges": get_gauges(state, team),
        "system_utilization": get_system_utilization(state, team),
        "engineer_board": get_engineer_board_state(state, team),
        "last_action_system": state.last_action_system.get(team, False),
        "skip_turns": state.skip_turns.get(team, 0),
        "radio_operator": get_radio_operator_state(state, team),
        "events": get_events(state),
    }


def snapshot_game_state(state: GameState, turn_id: int | None = None) -> dict[str, Any]:
    """Return a full, JSON-friendly copy of the authoritative game state."""
    return {
        "turn": state.turn if turn_id is None else turn_id,
        "game_over": state.game_over,
        "winner": state.winner,
        "map": get_map_state(state),
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
                "circuits_status": dict(breakdown.circuits_status),
            }
            for team, breakdown in state.breakdowns.items()
        },
        "skip_turns": dict(state.skip_turns),
        "engineer_boards": {
            team: get_engineer_board_state(state, team)
            for team in state.breakdowns
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
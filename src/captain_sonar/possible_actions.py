from __future__ import annotations

from typing import Any, Iterable

from .actions import ActionType
from .config import GAUGE_MAX_DEFAULT, MAX_SILENCE_STEPS, SYSTEM_SYMBOLS_MAP

NONE_VALUE = "NONE"


def all_possible_actions() -> list[dict[str, Any]]:
    """Return the full catalog of high-level Captain Sonar action templates."""
    catalog = [
        _action_template(
            ActionType.MOVE.value,
            phase_1=_phase_1(movement={"type": ActionType.MOVE.value, "direction": "N"}),
            phase_2=_phase_2(),
        ),
        _action_template(
            ActionType.MOVE.value,
            phase_1=_phase_1(movement={"type": ActionType.MOVE.value, "direction": "S"}),
            phase_2=_phase_2(),
        ),
        _action_template(
            ActionType.MOVE.value,
            phase_1=_phase_1(movement={"type": ActionType.MOVE.value, "direction": "E"}),
            phase_2=_phase_2(),
        ),
        _action_template(
            ActionType.MOVE.value,
            phase_1=_phase_1(movement={"type": ActionType.MOVE.value, "direction": "W"}),
            phase_2=_phase_2(),
        ),
        _action_template(
            ActionType.SILENCE.value,
            phase_1=_phase_1(),
            phase_2=_phase_2(
                activate_system={
                    "type": ActionType.SILENCE.value,
                    "payload": {"direction": "N", "steps": min(4, MAX_SILENCE_STEPS)},
                }
            ),
        ),
        _action_template(
            ActionType.SILENCE.value,
            phase_1=_phase_1(),
            phase_2=_phase_2(
                activate_system={
                    "type": ActionType.SILENCE.value,
                    "payload": {"direction": "S", "steps": min(4, MAX_SILENCE_STEPS)},
                }
            ),
        ),
        _action_template(
            ActionType.SILENCE.value,
            phase_1=_phase_1(),
            phase_2=_phase_2(
                activate_system={
                    "type": ActionType.SILENCE.value,
                    "payload": {"direction": "E", "steps": min(4, MAX_SILENCE_STEPS)},
                }
            ),
        ),
        _action_template(
            ActionType.SILENCE.value,
            phase_1=_phase_1(),
            phase_2=_phase_2(
                activate_system={
                    "type": ActionType.SILENCE.value,
                    "payload": {"direction": "W", "steps": min(4, MAX_SILENCE_STEPS)},
                }
            ),
        ),
        _action_template(ActionType.TORPEDO.value, phase_1=_phase_1(), phase_2=_phase_2(activate_system="torpedo")),
        _action_template(ActionType.MINE.value, phase_1=_phase_1(), phase_2=_phase_2(activate_system="mine")),
        _action_template(ActionType.TRIGGER_MINE.value, phase_1=_phase_1(), phase_2=_phase_2(activate_system="trigger_mine")),
        _action_template(ActionType.DRONE.value, phase_1=_phase_1(), phase_2=_phase_2(activate_system="drone")),
        _action_template(ActionType.SONAR.value, phase_1=_phase_1(), phase_2=_phase_2(activate_system="sonar")),
        _action_template(ActionType.REPAIR.value, phase_1=_phase_1(), phase_2=_phase_2(activate_system="repair")),
        _action_template(ActionType.SURFACE.value, phase_1=_phase_1(movement={"type": ActionType.SURFACE.value}), phase_2=_phase_2()),
    ]
    return catalog


def possible_actions_for_role(role: str, team_view: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return a role-aware action list or proposal catalog."""
    role_name = str(role).lower()
    catalog = all_possible_actions()

    if role_name == "captain":
        return _captain_actions(team_view or {}, catalog)
    if role_name == "first_mate":
        return _first_mate_actions(team_view or {}, catalog)
    if role_name == "engineer":
        return _engineer_actions(team_view or {}, catalog)
    if role_name == "radio_operator":
        return _radio_operator_actions(team_view or {}, catalog)
    return catalog


def _captain_actions(team_view: dict[str, Any], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    move_directions: list[dict[str, Any]] = []
    own_submarine = team_view.get("own_submarine", {})
    x = own_submarine.get("x")
    y = own_submarine.get("y")
    if not isinstance(x, int) or not isinstance(y, int):
        return _merge_catalog([], catalog, team_view)

    load_options = _chargeable_systems(team_view)
    engineer_by_direction = _engineer_selections_by_direction(team_view)

    # Build tree-like structure: action_kind -> directions -> load_systems -> engineer_picks
    # with shared system hypotheses stored once per direction.
    for direction in ("N", "S", "E", "W"):
        if not _direction_is_clear(team_view, x, y, direction):
            continue
        engineer_options = engineer_by_direction.get(direction, [])
        if not engineer_options:
            continue
        load_branches: list[dict[str, Any]] = []
        system_hypotheses: list[str | dict[str, Any]] = [NONE_VALUE]
        seen_hypotheses: set[str] = {NONE_VALUE}
        for load_system in load_options:
            system_options = _system_activation_options(team_view, x, y, load_system)
            for option in system_options:
                hypothesis_key = str(option)
                if hypothesis_key in seen_hypotheses:
                    continue
                seen_hypotheses.add(hypothesis_key)
                system_hypotheses.append(option)
            possible_activations = _activation_type_names(system_options)
            load_branches.append(
                {
                    "load_system": load_system,
                    "engineer_picks": [
                        (
                            lambda sel: {
                                **sel,
                                "system_to_load": load_system,
                                "possible_activations": (
                                    lambda acts: acts if acts else [NONE_VALUE]
                                )(
                                    _filter_activations_by_engineer_button(
                                        possible_activations, sel.get("function_type")
                                    )
                                ),
                            }
                        )(engineer_selection)
                        for engineer_selection in engineer_options
                    ],
                }
            )
        if load_branches:
            move_directions.append(
                {
                    "direction": direction,
                    "system_hypotheses": system_hypotheses,
                    "load_systems": load_branches,
                }
            )

    # If there are no move directions available (for example all engineer picks
    # are blocked or no clear direction), do not offer MOVE — only allow SURFACE.
    if not move_directions:
        actions: list[dict[str, Any]] = [
            {
                "action_kind": ActionType.SURFACE.value,
                "engineer_picks": [NONE_VALUE],
                "system_hypotheses": [NONE_VALUE],
            }
        ]
    else:
        actions = [
            {
                "action_kind": ActionType.MOVE.value,
                "directions": move_directions,
            },
            {
                "action_kind": ActionType.SURFACE.value,
                "engineer_picks": [NONE_VALUE],
                "system_hypotheses": [NONE_VALUE],
            },
        ]

    return actions


def _first_mate_actions(team_view: dict[str, Any], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gauges = team_view.get("own_gauges", {})
    ready = team_view.get("system_utilization", {}).get("ready", {})
    preferred_system = NONE_VALUE
    for candidate in ("torpedo", "sonar", "drone", "silence", "mine", "scenario"):
        if not ready.get(candidate, False):
            preferred_system = candidate
            break

    return [
        _action_template(
            "CHARGE",
            phase_1=_phase_1(load_system=preferred_system),
            phase_2=_phase_2(),
        ),
        _action_template(
            "ACTIVATE",
            phase_1=_phase_1(),
            phase_2=_phase_2(activate_system=preferred_system),
        ),
        _action_template(ActionType.REPAIR.value, phase_1=_phase_1(), phase_2=_phase_2(activate_system="repair")),
    ] + _merge_catalog([], catalog, team_view)


def _engineer_actions(team_view: dict[str, Any], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    board = team_view.get("engineer_board", {})
    buttons = board.get("buttons_by_direction", {}) if isinstance(board, dict) else {}
    proposals: list[dict[str, Any]] = []
    for direction, entries in buttons.items():
        if not entries:
            continue
        first_button = next((entry for entry in entries if not entry.get("crossed", False)), None)
        if first_button is None:
            continue
        proposals.append(
            _action_template(
                "ENGINEER_SELECTION",
                phase_1=_phase_1(
                    engineer_selection={
                        "direction": direction,
                        "button_id": first_button.get("button_id"),
                        "slot_index": first_button.get("slot_index"),
                        "circuit_part": first_button.get("circuit_part"),
                        "function_type": first_button.get("function_type"),
                    }
                ),
                phase_2=_phase_2(),
            )
        )
    if not proposals:
        proposals.append(
            _action_template(
                "ENGINEER_SELECTION",
                phase_1=_phase_1(
                    engineer_selection={
                        "direction": "N",
                        "button_id": None,
                        "slot_index": 0,
                        "circuit_part": "not",
                        "function_type": "radioactive",
                    }
                ),
                phase_2=_phase_2(),
            )
        )
    proposals.append(_action_template(ActionType.REPAIR.value, phase_1=_phase_1(), phase_2=_phase_2(activate_system="repair")))
    return proposals + _merge_catalog([], catalog, team_view)


def _radio_operator_actions(team_view: dict[str, Any], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    radio = team_view.get("radio_operator", {})
    likely_position = radio.get("most_likely_position")
    likely_sector = radio.get("most_likely_sector")
    proposals = [
        _action_template(
            "TRACK",
            phase_1=_phase_1(),
            phase_2=_phase_2(activate_system={"type": "TRACK", "payload": {"most_likely_position": likely_position, "confidence": radio.get("confidence", 0.0)}}),
        ),
        _action_template(
            "SENSOR_SUGGESTION",
            phase_1=_phase_1(),
            phase_2=_phase_2(activate_system={"type": "SENSOR_SUGGESTION", "payload": {"system": "drone" if likely_sector else "sonar"}}),
        ),
    ]
    return proposals + _merge_catalog([], catalog, team_view)


def _orthogonal_targets(x: int, y: int, team_view: dict[str, Any]) -> list[tuple[int, int]]:
    map_view = team_view.get("map", {})
    width = map_view.get("width")
    height = map_view.get("height")
    if not isinstance(width, int) or not isinstance(height, int):
        return []
    targets: list[tuple[int, int]] = []
    for distance in range(1, 5):
        for tx, ty in ((x + distance, y), (x - distance, y), (x, y + distance), (x, y - distance)):
            if 0 <= tx < width and 0 <= ty < height:
                targets.append((tx, ty))
    return targets


def _adjacent_targets(x: int, y: int, team_view: dict[str, Any]) -> list[tuple[int, int]]:
    map_view = team_view.get("map", {})
    width = map_view.get("width")
    height = map_view.get("height")
    if not isinstance(width, int) or not isinstance(height, int):
        return []
    targets: list[tuple[int, int]] = []
    for tx, ty in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= tx < width and 0 <= ty < height:
            targets.append((tx, ty))
    return targets


def _merge_catalog(proposals: list[dict[str, Any]], catalog: list[dict[str, Any]], team_view: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    seen = {proposal.get("action_kind") for proposal in proposals}
    merged = list(proposals)
    for item in catalog:
        kind = item.get("action_kind")
        if kind in seen:
            continue

        # If team_view provided, filter out system activations that are not allowed
        if team_view is not None:
            phase_2 = item.get("phase_2", {}) or {}
            activate = phase_2.get("activate_system")
            # normalize activate to string system name when possible
            system_name = None
            if isinstance(activate, str) and activate != NONE_VALUE:
                system_name = activate
            elif isinstance(activate, dict):
                system_name = activate.get("type")
            if isinstance(system_name, str):
                # map ActionType string names to our system keys if needed
                sys_lower = system_name.lower()
                if not _system_allowed(team_view, sys_lower):
                    # skip this catalog item
                    continue

        merged.append(dict(item))
        seen.add(kind)
    return merged


def _direction_is_clear(team_view: dict[str, Any], x: int, y: int, direction: str) -> bool:
    """Check if movement in direction is valid.
    
    Cannot move:
    - Outside map bounds
    - Into an island (#)
    - To an already-visited position (own_trajectory)
    """
    map_view = team_view.get("map", {})
    tiles = map_view.get("tiles")
    width = map_view.get("width")
    height = map_view.get("height")
    if not isinstance(width, int) or not isinstance(height, int):
        return True
    if not isinstance(tiles, list) or not tiles:
        return True
    dx, dy = 0, 0
    if direction == "N":
        dy = -1
    elif direction == "S":
        dy = 1
    elif direction == "E":
        dx = 1
    elif direction == "W":
        dx = -1
    nx, ny = x + dx, y + dy
    
    # Check map bounds
    if not (0 <= nx < width and 0 <= ny < height):
        return False
    
    # Check island
    row = tiles[ny] if 0 <= ny < len(tiles) else None
    if not isinstance(row, list) or not (0 <= nx < len(row)):
        return True
    if row[nx] == "#":
        return False
    
    # Check already visited positions
    trajectory = team_view.get("own_trajectory", [])
    if isinstance(trajectory, list):
        for pos in trajectory:
            if isinstance(pos, dict) and pos.get("x") == nx and pos.get("y") == ny:
                return False
    
    return True


def _system_ready(team_view: dict[str, Any], system: str) -> bool:
    ready = team_view.get("system_utilization", {}).get("ready", {})
    return bool(ready.get(system, False))


def _system_has_breakdown(team_view: dict[str, Any], system: str) -> bool:
    board = team_view.get("engineer_board", {})
    if not isinstance(board, dict):
        return False
    target_color = SYSTEM_SYMBOLS_MAP.get(system)
    if target_color is None:
        return False
    buttons_by_direction = board.get("buttons_by_direction", {})
    if not isinstance(buttons_by_direction, dict):
        return False
    for entries in buttons_by_direction.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("crossed") and entry.get("function_type") == target_color:
                return True
    return False


def _system_allowed(team_view: dict[str, Any], system: str) -> bool:
    if system == "trigger_mine":
        return True
    if not _system_ready(team_view, system):
        return False
    return not _system_has_breakdown(team_view, system)


def _suggest_charge_system(team_view: dict[str, Any]) -> str:
    ready = team_view.get("system_utilization", {}).get("ready", {})
    for candidate in ("torpedo", "mine", "drone", "silence"):
        if not ready.get(candidate, False):
            return candidate
    return NONE_VALUE


def _chargeable_systems(team_view: dict[str, Any]) -> list[str]:
    ready = team_view.get("system_utilization", {}).get("ready", {})
    options = [candidate for candidate in ("torpedo", "mine", "drone", "silence") if not ready.get(candidate, False)]
    return options or [NONE_VALUE]


def _engineer_selections_by_direction(team_view: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    board = team_view.get("engineer_board", {})
    if not isinstance(board, dict):
        return {}
    buttons = board.get("buttons_by_direction", {})
    if not isinstance(buttons, dict):
        return {}
    selections: dict[str, list[dict[str, Any]]] = {}
    for direction, entries in buttons.items():
        if not isinstance(entries, list):
            continue
        choices = []
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("crossed", False):
                continue
            choices.append(
                {
                    "direction": direction,
                    "button_id": entry.get("button_id"),
                    "slot_index": entry.get("slot_index"),
                    "circuit_part": entry.get("circuit_part"),
                    "function_type": entry.get("function_type"),
                }
            )
        selections[direction] = choices
    return selections


def _get_blocked_systems(team_view: dict[str, Any]) -> set[str]:
    """Return set of systems blocked by crossed engineer buttons.
    
    Red crossed buttons block: torpedo and mine (deploy mine)
    Yellow crossed buttons block: sonar and drone
    Green crossed buttons block: silence
    """
    blocked = set()
    board = team_view.get("engineer_board", {})
    buttons_by_direction = board.get("buttons_by_direction", {})
    
    if not isinstance(buttons_by_direction, dict):
        return blocked
    
    for entries in buttons_by_direction.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("crossed", False):
                continue
            function_type = entry.get("function_type")
            if function_type == "red":
                blocked.update(["torpedo", "mine"])
            elif function_type == "yellow":
                blocked.update(["sonar", "drone"])
            elif function_type == "green":
                blocked.add("silence")
    
    return blocked


def _filter_activations_by_engineer_button(possible_activations: list[str], function_type: str | None) -> list[str]:
    """Filter activation options based on the engineer button's function type.
    
    When an engineer button is selected, it will be crossed after the action.
    Red buttons block: torpedo and mine
    Yellow buttons block: sonar and drone
    Green buttons block: silence
    """
    if not function_type:
        return possible_activations
    
    blocked_by_button = set()
    if function_type == "red":
        blocked_by_button.update(["torpedo", "mine"])
    elif function_type == "yellow":
        blocked_by_button.update(["sonar", "drone"])
    elif function_type == "green":
        blocked_by_button.add("silence")
    
    return [act for act in possible_activations if act not in blocked_by_button]


def _system_activation_options(team_view: dict[str, Any], x: int, y: int, load_system: str) -> list[str | dict[str, Any]]:
    options: list[str | dict[str, Any]] = [NONE_VALUE]
    blocked_systems = _get_blocked_systems(team_view)
    has_own_mines = False
    own_mines = team_view.get("own_mines")
    if isinstance(own_mines, list) and own_mines:
        has_own_mines = True

    if _system_can_activate(team_view, "torpedo", load_system) and "torpedo" not in blocked_systems:
        torpedo_targets = [{"x": tx, "y": ty} for tx, ty in _orthogonal_targets(x, y, team_view)]
        if torpedo_targets:
            options.append({"type": "torpedo", "payload": {"targets": torpedo_targets}})
    if _system_can_activate(team_view, "mine", load_system) and "mine" not in blocked_systems:
        mine_targets = [{"x": tx, "y": ty} for tx, ty in _adjacent_targets(x, y, team_view)]
        if mine_targets:
            options.append({"type": "mine", "payload": {"targets": mine_targets}})
    if _system_can_activate(team_view, "drone", load_system) and "drone" not in blocked_systems:
        options.append({"type": "drone", "payload": {"sectors": list(range(1, 10))}})
    if _system_can_activate(team_view, "sonar", load_system) and "sonar" not in blocked_systems:
        options.append("sonar")
    if _system_can_activate(team_view, "silence", load_system) and "silence" not in blocked_systems:
        silence_coordinates = [
            {"x": tx, "y": ty}
            for tx, ty in _orthogonal_targets(x, y, team_view)
        ]
        if silence_coordinates:
            options.append({"type": "silence", "payload": {"coordinates": silence_coordinates}})
    if has_own_mines and _system_allowed(team_view, "trigger_mine") and "trigger_mine" not in blocked_systems:
        options.append({"type": "trigger_mine", "payload": {"target": {"x": x, "y": y}}})
    if _system_allowed(team_view, "repair"):
        options.append("repair")

    return options


def _first_activation_hypothesis(options: list[str | dict[str, Any]]) -> str | dict[str, Any]:
    for option in options:
        if option != NONE_VALUE:
            if isinstance(option, dict):
                return str(option.get("type", NONE_VALUE))
            return str(option)
    return NONE_VALUE


def _activation_type_names(options: list[str | dict[str, Any]]) -> list[str]:
    types: list[str] = []
    for option in options:
        if option == NONE_VALUE:
            continue
        if isinstance(option, dict):
            type_name = option.get("type")
            if type_name:
                types.append(str(type_name))
        else:
            types.append(str(option))
    return types


def _system_can_activate(team_view: dict[str, Any], system: str, load_system: str) -> bool:
    if system == "trigger_mine":
        return True
    if _system_allowed(team_view, system):
        return True
    gauges = team_view.get("own_gauges", {})
    if load_system == system and isinstance(gauges, dict):
        current = gauges.get(system)
        if isinstance(current, int) and current >= GAUGE_MAX_DEFAULT - 1:
            return True
    return False


def _engineer_selection_for_direction(team_view: dict[str, Any], direction: str) -> dict[str, Any] | str:
    board = team_view.get("engineer_board", {})
    if not isinstance(board, dict):
        return NONE_VALUE
    buttons = board.get("buttons_by_direction", {})
    if not isinstance(buttons, dict):
        return NONE_VALUE
    entries = buttons.get(direction)
    if not isinstance(entries, list) or not entries:
        return NONE_VALUE
    first_button = next((entry for entry in entries if not entry.get("crossed", False)), None)
    if not isinstance(first_button, dict):
        return NONE_VALUE
    return {
        "direction": direction,
        "button_id": first_button.get("button_id"),
        "slot_index": first_button.get("slot_index"),
        "circuit_part": first_button.get("circuit_part"),
        "function_type": first_button.get("function_type"),
    }


def _phase_1(
    movement: dict[str, Any] | None = None,
    load_system: str = NONE_VALUE,
    engineer_selection: dict[str, Any] | str = NONE_VALUE,
) -> dict[str, Any]:
    return {
        "movement": movement or {"type": NONE_VALUE},
        "load_system": load_system,
        "engineer_selection": engineer_selection,
    }


def _phase_2(activate_system: str | dict[str, Any] = NONE_VALUE) -> dict[str, Any]:
    return {"activate_system": activate_system}


def _action_template(action_kind: str, phase_1: dict[str, Any], phase_2: dict[str, Any]) -> dict[str, Any]:
    return {
        "action_kind": action_kind,
        "phase_1": phase_1,
        "phase_2": phase_2,
    }



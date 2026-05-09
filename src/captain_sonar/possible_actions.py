from __future__ import annotations

from typing import Any, Iterable

from .actions import ActionType
from .config import MAX_SILENCE_STEPS


def all_possible_actions() -> list[dict[str, Any]]:
    """Return the full catalog of high-level Captain Sonar action templates."""
    return [
        {"type": ActionType.MOVE.value, "label": "Move north", "step_1": "move", "step_2": "charge"},
        {"type": ActionType.MOVE.value, "label": "Move south", "step_1": "move", "step_2": "charge"},
        {"type": ActionType.MOVE.value, "label": "Move east", "step_1": "move", "step_2": "charge"},
        {"type": ActionType.MOVE.value, "label": "Move west", "step_1": "move", "step_2": "charge"},
        {"type": ActionType.SILENCE.value, "label": "Silent move north", "step_1": "move", "step_2": "system"},
        {"type": ActionType.SILENCE.value, "label": "Silent move south", "step_1": "move", "step_2": "system"},
        {"type": ActionType.SILENCE.value, "label": "Silent move east", "step_1": "move", "step_2": "system"},
        {"type": ActionType.SILENCE.value, "label": "Silent move west", "step_1": "move", "step_2": "system"},
        {"type": ActionType.TORPEDO.value, "label": "Fire torpedo", "step_1": "system", "step_2": "confirm target"},
        {"type": ActionType.MINE.value, "label": "Drop mine", "step_1": "system", "step_2": "confirm target"},
        {"type": ActionType.TRIGGER_MINE.value, "label": "Trigger mine", "step_1": "system", "step_2": "confirm target"},
        {"type": ActionType.DRONE.value, "label": "Launch drone", "step_1": "system", "step_2": "sector check"},
        {"type": ActionType.SONAR.value, "label": "Activate sonar", "step_1": "system", "step_2": "truth check"},
        {"type": ActionType.REPAIR.value, "label": "Repair", "step_1": "system", "step_2": "recover"},
        {"type": ActionType.SURFACE.value, "label": "Surface", "step_1": "move", "step_2": "reset route"},
    ]


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
    actions: list[dict[str, Any]] = []
    own_submarine = team_view.get("own_submarine", {})
    x = own_submarine.get("x")
    y = own_submarine.get("y")
    if isinstance(x, int) and isinstance(y, int):
        for direction in ("N", "S", "E", "W"):
            actions.append({"type": ActionType.MOVE.value, "payload": {"direction": direction}})
            actions.append({"type": ActionType.SILENCE.value, "payload": {"direction": direction, "steps": min(4, MAX_SILENCE_STEPS)}})
        for tx, ty in _orthogonal_targets(x, y, team_view):
            actions.append({"type": ActionType.TORPEDO.value, "payload": {"target": {"x": tx, "y": ty}}})
        for tx, ty in _adjacent_targets(x, y, team_view):
            actions.append({"type": ActionType.MINE.value, "payload": {"target": {"x": tx, "y": ty}}})
        actions.append({"type": ActionType.SURFACE.value, "payload": {}})
        actions.append({"type": ActionType.REPAIR.value, "payload": {}})

    if team_view.get("radio_operator", {}).get("most_likely_sector"):
        actions.append({"type": ActionType.DRONE.value, "payload": {"sector": team_view["radio_operator"]["most_likely_sector"]}})
    actions.append({"type": ActionType.SONAR.value, "payload": {}})
    actions.append({"type": ActionType.TRIGGER_MINE.value, "payload": {"target": {"x": x, "y": y}}})
    return _merge_catalog(actions, catalog)


def _first_mate_actions(team_view: dict[str, Any], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gauges = team_view.get("own_gauges", {})
    ready = team_view.get("system_utilization", {}).get("ready", {})
    preferred_system = "torpedo"
    if ready.get("torpedo"):
        preferred_system = "torpedo"
    elif ready.get("sonar"):
        preferred_system = "sonar"
    elif ready.get("drone"):
        preferred_system = "drone"
    elif gauges.get("silence", 0) < gauges.get("torpedo", 0):
        preferred_system = "silence"

    return [
        {"type": "CHARGE", "payload": {"system": preferred_system}},
        {"type": "ACTIVATE", "payload": {"system": preferred_system}},
        {"type": ActionType.REPAIR.value, "payload": {}},
    ] + _merge_catalog([], catalog)


def _engineer_actions(team_view: dict[str, Any], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    board = team_view.get("engineer_board", {})
    buttons = board.get("buttons_by_direction", {}) if isinstance(board, dict) else {}
    proposals: list[dict[str, Any]] = []
    for direction, entries in buttons.items():
        if not entries:
            continue
        first_button = entries[0]
        proposals.append(
            {
                "type": "ENGINEER_SELECTION",
                "payload": {
                    "direction": direction,
                    "button_id": first_button.get("button_id"),
                    "slot_index": first_button.get("slot_index"),
                    "circuit_part": first_button.get("circuit_part"),
                    "function_type": first_button.get("function_type"),
                },
            }
        )
    if not proposals:
        proposals.append(
            {
                "type": "ENGINEER_SELECTION",
                "payload": {
                    "direction": "N",
                    "button_id": None,
                    "slot_index": 0,
                    "circuit_part": "not",
                    "function_type": "radioactive",
                },
            }
        )
    proposals.append({"type": ActionType.REPAIR.value, "payload": {}})
    return proposals + _merge_catalog([], catalog)


def _radio_operator_actions(team_view: dict[str, Any], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    radio = team_view.get("radio_operator", {})
    likely_position = radio.get("most_likely_position")
    likely_sector = radio.get("most_likely_sector")
    proposals = [
        {"type": "TRACK", "payload": {"most_likely_position": likely_position, "confidence": radio.get("confidence", 0.0)}},
        {"type": "SENSOR_SUGGESTION", "payload": {"system": "drone" if likely_sector else "sonar"}},
    ]
    return proposals + _merge_catalog([], catalog)


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


def _merge_catalog(proposals: list[dict[str, Any]], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = {proposal.get("type") for proposal in proposals}
    merged = list(proposals)
    for item in catalog:
        if item["type"] not in seen:
            merged.append(dict(item))
            seen.add(item["type"])
    return merged
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class ActionType(str, Enum):
    MOVE = "MOVE"
    SILENCE = "SILENCE"
    SONAR = "SONAR"
    DRONE = "DRONE"
    TORPEDO = "TORPEDO"
    MINE = "MINE"
    TRIGGER_MINE = "TRIGGER_MINE"
    REPAIR = "REPAIR"
    SURFACE = "SURFACE"
    END_TURN = "END_TURN"


DIRECTIONS = {"N", "S", "E", "W"}


@dataclass(frozen=True)
class Action:
    actor: str
    type: ActionType
    payload: Dict[str, Any]


def normalize_action(raw: Dict[str, Any]) -> Action:
    action_type = ActionType(raw.get("type", "END_TURN"))
    return Action(
        actor=str(raw.get("actor", "")),
        type=action_type,
        payload=dict(raw.get("payload", {})),
    )


def action_to_dict(action: Action) -> Dict[str, Any]:
    return {"actor": action.actor, "type": action.type.value, "payload": dict(action.payload)}


def action_from_dict(raw: Dict[str, Any]) -> Action:
    return normalize_action(raw)


def validate_action(action: Action) -> List[str]:
    errors: List[str] = []
    if not action.actor:
        errors.append("actor is required")
    if action.type == ActionType.MOVE:
        direction = action.payload.get("direction")
        if direction not in DIRECTIONS:
            errors.append("MOVE requires direction in N/S/E/W")
    if action.type == ActionType.SILENCE:
        direction = action.payload.get("direction")
        steps = action.payload.get("steps")
        if direction not in DIRECTIONS:
            errors.append("SILENCE requires direction in N/S/E/W")
        if not isinstance(steps, int):
            errors.append("SILENCE requires integer steps")
    if action.type == ActionType.TORPEDO:
        target = action.payload.get("target")
        if not isinstance(target, dict):
            errors.append("TORPEDO requires target {x, y}")
        else:
            if not isinstance(target.get("x"), int) or not isinstance(target.get("y"), int):
                errors.append("TORPEDO target requires integer x,y")
    if action.type in (ActionType.SONAR, ActionType.MINE, ActionType.TRIGGER_MINE):
        target = action.payload.get("target")
        if action.type in (ActionType.MINE, ActionType.TRIGGER_MINE) and not isinstance(target, dict):
            errors.append(f"{action.type.value} requires target {{x, y}}")
        if target is not None:
            if not isinstance(target, dict):
                errors.append(f"{action.type.value} target must be {{x, y}} if provided")
            elif not isinstance(target.get("x"), int) or not isinstance(target.get("y"), int):
                errors.append(f"{action.type.value} target requires integer x,y")
    if action.type == ActionType.DRONE:
        sector = action.payload.get("sector")
        if not isinstance(sector, int):
            errors.append("DRONE requires integer sector")
    return errors


ACTION_PRIORITY = {
    ActionType.SURFACE: 10,
    ActionType.MOVE: 20,
    ActionType.SILENCE: 30,
    ActionType.REPAIR: 40,
    ActionType.TORPEDO: 50,
    ActionType.MINE: 50,
    ActionType.TRIGGER_MINE: 50,
    ActionType.SONAR: 60,
    ActionType.DRONE: 60,
    ActionType.END_TURN: 90,
}


def action_priority(action: Action) -> int:
    return ACTION_PRIORITY.get(action.type, 999)


def order_actions(actions: List[Action]) -> List[Action]:
    indexed = list(enumerate(actions))
    indexed.sort(key=lambda item: (action_priority(item[1]), item[1].actor, item[0]))
    return [item[1] for item in indexed]

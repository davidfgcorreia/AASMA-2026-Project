from __future__ import annotations

import random
from typing import List

from .actions import Action, ActionType


def choose_actions(team: str, rng: random.Random, state, phase: str = "move") -> List[Action]:
    sub = state.subs.get(team)
    if not sub:
        return []

    if phase == "move":
        return _choose_move(team, rng, state, sub)
    return _choose_system(team, rng, state, sub)


def _choose_move(team: str, rng: random.Random, state, sub) -> List[Action]:
    directions = ["N", "S", "E", "W"]
    rng.shuffle(directions)
    for direction in directions:
        dx, dy = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}[direction]
        nx, ny = sub.x + dx, sub.y + dy
        if not state.map_data.in_bounds(nx, ny) or state.map_data.is_blocked(nx, ny):
            continue
        if (nx, ny) in state.routes.get(team, set()):
            continue
        if any(mine.owner == team and mine.x == nx and mine.y == ny for mine in state.mines):
            continue
        return [
            Action(
                actor=team,
                type=ActionType.MOVE,
                payload={"direction": direction, "charge": "torpedo"},
            )
        ]
    return [Action(actor=team, type=ActionType.SURFACE, payload={})]


def _choose_system(team: str, rng: random.Random, state, sub) -> List[Action]:
    enemy = next((name for name in state.subs.keys() if name != team), None)
    enemy_sub = state.subs.get(enemy) if enemy else None

    if enemy_sub and not state.last_action_system.get(team, False):
        distance = abs(sub.x - enemy_sub.x) + abs(sub.y - enemy_sub.y)
        orthogonal = sub.x == enemy_sub.x or sub.y == enemy_sub.y
        if (
            orthogonal
            and 1 <= distance <= 4
            and state.system_ready(team, "torpedo")
            and rng.random() < 0.4
        ):
            return [
                Action(
                    actor=team,
                    type=ActionType.TORPEDO,
                    payload={"target": {"x": enemy_sub.x, "y": enemy_sub.y}},
                )
            ]

    if state.system_ready(team, "mine") and not state.last_action_system.get(team, False):
        adjacent = [(sub.x + 1, sub.y), (sub.x - 1, sub.y), (sub.x, sub.y + 1), (sub.x, sub.y - 1)]
        rng.shuffle(adjacent)
        for nx, ny in adjacent:
            if not state.map_data.in_bounds(nx, ny) or state.map_data.is_blocked(nx, ny):
                continue
            if any(mine.owner == team and mine.x == nx and mine.y == ny for mine in state.mines):
                continue
            return [Action(actor=team, type=ActionType.MINE, payload={"target": {"x": nx, "y": ny}})]

    return []

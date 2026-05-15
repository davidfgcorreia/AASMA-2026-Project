"""Start-position helpers for `TeamAgentManager`.

Small utilities to compute and validate legal starting tiles for a team.
These helpers are deliberately simple and operate on the manager instance
for configuration values like the team id.
"""

from __future__ import annotations

from typing import Mapping, Tuple
from captain_sonar.map_loader import MapData

GridPos = Tuple[int, int]


def default_start_position(manager, map_data: MapData, confirmed: Mapping[str, object]) -> GridPos | None:
    preferred = (1, 1) if manager.team == "BLUE" else (max(0, map_data.width - 2), max(0, map_data.height - 2))
    if is_legal_start_tile(manager, map_data, preferred, confirmed):
        return preferred

    for y in range(map_data.height):
        for x in range(map_data.width):
            candidate = (x, y)
            if is_legal_start_tile(manager, map_data, candidate, confirmed):
                return candidate
    return None


def is_legal_start_tile(manager, map_data: MapData, candidate: GridPos, confirmed: Mapping[str, object]) -> bool:
    x, y = candidate
    if not map_data.in_bounds(x, y):
        return False
    if map_data.is_blocked(x, y):
        return False
    return all(getattr(sub, "x", None) != x or getattr(sub, "y", None) != y for sub in confirmed.values())

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class MapData:
    width: int
    height: int
    tiles: List[List[str]]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_blocked(self, x: int, y: int) -> bool:
        return self.tiles[y][x] == "#"


def load_map(path: str) -> MapData:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    rows = data["rows"]
    width = int(data["width"])
    height = int(data["height"])
    if len(rows) != height:
        raise ValueError("Row count does not match height")
    tiles = [list(row) for row in rows]
    for row in tiles:
        if len(row) != width:
            raise ValueError("Row width does not match width")
    return MapData(width=width, height=height, tiles=tiles)

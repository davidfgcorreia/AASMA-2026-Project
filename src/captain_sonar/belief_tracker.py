from __future__ import annotations

from typing import List

from .map_loader import MapData


class BeliefTracker:
    def __init__(self, map_data: MapData) -> None:
        self.map_data = map_data
        self._uniform = self._build_uniform()

    def _build_uniform(self) -> List[List[float]]:
        total = self.map_data.width * self.map_data.height
        prob = 1.0 / float(total)
        return [[prob for _ in range(self.map_data.width)] for _ in range(self.map_data.height)]

    def update(self, _events: list[dict]) -> None:
        return

    def heatmap(self) -> List[List[float]]:
        return self._uniform

    def probability_at(self, x: int, y: int) -> float:
        if not self.map_data.in_bounds(x, y):
            return 0.0
        return self._uniform[y][x]

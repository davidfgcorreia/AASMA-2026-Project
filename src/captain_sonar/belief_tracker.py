from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from .map_loader import MapData
from .config import MAX_SILENCE_STEPS, SECTOR_COLS, SECTOR_ROWS


class BeliefTracker:
    def __init__(self, map_data: MapData, own_team: str = "BLUE") -> None:
        self.map_data = map_data
        self.own_team = own_team
        self._belief = self._build_uniform()

    def _build_uniform(self) -> List[List[float]]:
        cells = [(x, y) for y in range(self.map_data.height) for x in range(self.map_data.width) if not self.map_data.is_blocked(x, y)]
        total = len(cells)
        if total <= 0:
            return [[0.0 for _ in range(self.map_data.width)] for _ in range(self.map_data.height)]
        prob = 1.0 / float(total)
        grid = [[0.0 for _ in range(self.map_data.width)] for _ in range(self.map_data.height)]
        for x, y in cells:
            grid[y][x] = prob
        return grid

    def reset_uniform(self) -> None:
        self._belief = self._build_uniform()

    def set_point_prior(self, x: int, y: int) -> None:
        grid = [[0.0 for _ in range(self.map_data.width)] for _ in range(self.map_data.height)]
        if self.map_data.in_bounds(x, y) and not self.map_data.is_blocked(x, y):
            grid[y][x] = 1.0
        self._belief = grid

    def update(self, events: list[dict]) -> None:
        enemy = self._infer_enemy(events)
        for event in events:
            etype = event.get("type")
            actor = event.get("actor")
            if actor == enemy:
                if etype == "surface":
                    sector = event.get("sector")
                    if isinstance(sector, int):
                        self._apply_surface_sector(sector)
                elif etype == "move":
                    direction = event.get("direction")
                    if isinstance(direction, str):
                        self._apply_move(direction)
                elif etype == "silence":
                    direction = event.get("direction")
                    steps = event.get("steps")
                    self._apply_silence(direction if isinstance(direction, str) else None, steps)

            # Sensors are actions by our team that reveal info about the enemy.
            if actor == self.own_team:
                if etype == "drone":
                    sector = event.get("sector")
                    response = event.get("response")
                    if isinstance(sector, int) and isinstance(response, bool):
                        self._apply_drone(sector, response)
                elif etype == "sonar":
                    true_info = event.get("true_info")
                    false_info = event.get("false_info")
                    info_1 = event.get("info_1")
                    info_2 = event.get("info_2")
                    if isinstance(true_info, dict) and isinstance(false_info, dict):
                        self._apply_sonar(true_info, false_info)
                    elif isinstance(info_1, dict) and isinstance(info_2, dict):
                        self._apply_sonar(info_1, info_2)
                elif etype == "explosion":
                    hits = event.get("hits", [])
                    impact = event.get("impact")
                    # If explosion had no hits, opponent was NOT at that location
                    if not hits and isinstance(impact, (list, tuple)) and len(impact) == 2:
                        self._apply_torpedo_miss(impact[0], impact[1])

    def heatmap(self) -> List[List[float]]:
        return self._belief

    def probability_at(self, x: int, y: int) -> float:
        if not self.map_data.in_bounds(x, y):
            return 0.0
        return self._belief[y][x]

    def sector_masses(self) -> Dict[int, float]:
        """Return a probability mass per sector (1-indexed)."""
        masses: Dict[int, float] = {}
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                if self.map_data.is_blocked(x, y):
                    continue
                p = self._belief[y][x]
                if p <= 0.0:
                    continue
                sector = self._sector_for(x, y)
                masses[sector] = masses.get(sector, 0.0) + p
        return masses

    def most_likely_sector(self) -> int | None:
        masses = self.sector_masses()
        if not masses:
            return None
        return max(masses, key=lambda sector: masses[sector])

    def most_likely_cell(self) -> Tuple[int, int] | None:
        best: Tuple[int, int] | None = None
        best_p = 0.0
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                if self.map_data.is_blocked(x, y):
                    continue
                p = self._belief[y][x]
                if p > best_p:
                    best_p = p
                    best = (x, y)
        return best if best_p > 0.0 else None

    def _infer_enemy(self, events: Iterable[dict]) -> str | None:
        for event in events:
            actor = event.get("actor")
            if isinstance(actor, str) and actor and actor != self.own_team:
                return actor
        return None

    def _normalize(self) -> None:
        total = 0.0
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                total += self._belief[y][x]
        if total <= 0.0:
            self.reset_uniform()
            return
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                self._belief[y][x] /= total

    def _apply_mask(self, allowed: set[Tuple[int, int]]) -> None:
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                if (x, y) not in allowed:
                    self._belief[y][x] = 0.0
        self._normalize()

    def _apply_move(self, direction: str) -> None:
        dx, dy = self._dir_delta(direction)
        new = [[0.0 for _ in range(self.map_data.width)] for _ in range(self.map_data.height)]
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                if self.map_data.is_blocked(x, y):
                    continue
                sx, sy = x - dx, y - dy
                if not self.map_data.in_bounds(sx, sy):
                    continue
                if self.map_data.is_blocked(sx, sy):
                    continue
                new[y][x] += self._belief[sy][sx]
        self._belief = new
        self._normalize()

    def _apply_silence(self, direction: str | None, steps: object) -> None:
        if isinstance(steps, int):
            step_values = [max(1, min(MAX_SILENCE_STEPS, steps))]
        else:
            step_values = list(range(1, MAX_SILENCE_STEPS + 1))

        directions = [direction] if direction in {"N", "S", "E", "W"} else ["N", "S", "E", "W"]

        acc = [[0.0 for _ in range(self.map_data.width)] for _ in range(self.map_data.height)]
        weight = 0
        for d in directions:
            for k in step_values:
                grid = [row[:] for row in self._belief]
                tmp = BeliefTracker(self.map_data, own_team=self.own_team)
                tmp._belief = grid
                for _ in range(k):
                    tmp._apply_move(d)
                for y in range(self.map_data.height):
                    for x in range(self.map_data.width):
                        acc[y][x] += tmp._belief[y][x]
                weight += 1

        if weight <= 0:
            return
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                acc[y][x] /= float(weight)
        self._belief = acc
        self._normalize()

    def _apply_surface_sector(self, sector: int) -> None:
        allowed = self._cells_in_sector(sector)
        self._apply_mask(allowed)

    def _apply_drone(self, sector: int, response: bool) -> None:
        in_sector = self._cells_in_sector(sector)
        if response:
            self._apply_mask(in_sector)
        else:
            allowed = {(x, y) for y in range(self.map_data.height) for x in range(self.map_data.width) if not self.map_data.is_blocked(x, y) and (x, y) not in in_sector}
            self._apply_mask(allowed)

    def _apply_sonar(self, true_info: dict, false_info: dict) -> None:
        pred_true = self._info_predicate(true_info)
        pred_false = self._info_predicate(false_info)
        allowed: set[Tuple[int, int]] = set()
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                if self.map_data.is_blocked(x, y):
                    continue
                a = pred_true(x, y)
                b = pred_false(x, y)
                if (a and not b) or (b and not a):
                    allowed.add((x, y))
        self._apply_mask(allowed)

    def _apply_torpedo_miss(self, x: int, y: int) -> None:
        """Exclude a location from belief (torpedo missed there)."""
        allowed = {(ox, oy) for oy in range(self.map_data.height) for ox in range(self.map_data.width) if not self.map_data.is_blocked(ox, oy) and (ox, oy) != (x, y)}
        self._apply_mask(allowed)

    def _cells_in_sector(self, sector: int) -> set[Tuple[int, int]]:
        allowed: set[Tuple[int, int]] = set()
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                if self.map_data.is_blocked(x, y):
                    continue
                if self._sector_for(x, y) == sector:
                    allowed.add((x, y))
        return allowed

    def _sector_for(self, x: int, y: int) -> int:
        row = min(SECTOR_ROWS - 1, (y * SECTOR_ROWS) // self.map_data.height)
        col = min(SECTOR_COLS - 1, (x * SECTOR_COLS) // self.map_data.width)
        return row * SECTOR_COLS + col + 1

    def _dir_delta(self, direction: str) -> Tuple[int, int]:
        if direction == "N":
            return (0, -1)
        if direction == "S":
            return (0, 1)
        if direction == "E":
            return (1, 0)
        if direction == "W":
            return (-1, 0)
        return (0, 0)

    def _info_predicate(self, info: dict):
        itype = info.get("type")
        value = info.get("value")
        if itype == "row" and isinstance(value, str) and value:
            target = value[0].upper()
            def pred(x: int, y: int) -> bool:
                return chr(ord("A") + y) == target
            return pred
        if itype == "col" and isinstance(value, int):
            def pred(x: int, y: int) -> bool:
                return (x + 1) == value
            return pred
        if itype == "sector" and isinstance(value, int):
            def pred(x: int, y: int) -> bool:
                return self._sector_for(x, y) == value
            return pred
        def always_false(_x: int, _y: int) -> bool:
            return False
        return always_false

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .actions import Action, ActionType, validate_action
from .config import (
    DAMAGE_DIRECT,
    DAMAGE_INDIRECT,
    GAUGE_MAX_DEFAULT,
    MAX_DAMAGE,
    MAX_SILENCE_STEPS,
    SECTOR_COLS,
    SECTOR_ROWS,
    SURFACE_SKIP_TURNS,
    TORPEDO_RANGE,
)
from .map_loader import MapData

SYSTEMS = ("torpedo", "mine", "drone", "sonar", "silence", "scenario")
SYSTEM_ACTION = {
    ActionType.TORPEDO: "torpedo",
    ActionType.MINE: "mine",
    ActionType.DRONE: "drone",
    ActionType.SONAR: "sonar",
    ActionType.SILENCE: "silence",
    ActionType.TRIGGER_MINE: "mine",
}


@dataclass
class SubmarineState:
    x: int
    y: int
    damage: int = 0


@dataclass(frozen=True)
class MineState:
    x: int
    y: int
    owner: str


@dataclass
class GameState:
    map_data: MapData
    subs: Dict[str, SubmarineState]
    turn: int = 0
    events: List[dict] = field(default_factory=list)
    mines: List[MineState] = field(default_factory=list)
    routes: Dict[str, set[Tuple[int, int]]] = field(default_factory=dict)
    gauges: Dict[str, Dict[str, int]] = field(default_factory=dict)
    last_action_system: Dict[str, bool] = field(default_factory=dict)
    skip_turns: Dict[str, int] = field(default_factory=dict)
    winner: str | None = None
    game_over: bool = False

    def __post_init__(self) -> None:
        if not self.routes:
            self.routes = {team: {(sub.x, sub.y)} for team, sub in self.subs.items()}
        if not self.gauges:
            self.gauges = {team: {system: 0 for system in SYSTEMS} for team in self.subs.keys()}
        if not self.last_action_system:
            self.last_action_system = {team: False for team in self.subs.keys()}
        if not self.skip_turns:
            self.skip_turns = {team: 0 for team in self.subs.keys()}

    def apply_actions(self, ordered_actions: List[Action]) -> None:
        if self.game_over:
            return
        self.events.clear()
        skip_snapshot = dict(self.skip_turns)
        for action in ordered_actions:
            if self.skip_turns.get(action.actor, 0) > 0:
                self.events.append({"type": "action_skipped", "actor": action.actor, "reason": "surfaced"})
                continue
            errors = validate_action(action)
            errors.extend(self._validate_state(action))
            if errors:
                self.events.append({"type": "action_rejected", "action": action, "errors": errors})
                continue
            self._resolve_action(action)
        for team, remaining in skip_snapshot.items():
            if remaining > 0:
                self.skip_turns[team] = max(0, self.skip_turns.get(team, 0) - 1)
        self._check_game_over()
        self.turn += 1

    def system_ready(self, team: str, system: str) -> bool:
        return self.gauges.get(team, {}).get(system, 0) >= GAUGE_MAX_DEFAULT

    def _consume_gauge(self, team: str, system: str) -> None:
        if team in self.gauges and system in self.gauges[team]:
            self.gauges[team][system] = 0

    def _charge_gauge(self, team: str, system: str) -> None:
        if team not in self.gauges or system not in self.gauges[team]:
            return
        self.gauges[team][system] = min(GAUGE_MAX_DEFAULT, self.gauges[team][system] + 1)

    def _validate_state(self, action: Action) -> List[str]:
        errors: List[str] = []
        sub = self.subs.get(action.actor)
        if not sub:
            errors.append("unknown actor")
            return errors
        if action.type in SYSTEM_ACTION:
            system = SYSTEM_ACTION[action.type]
            if action.type != ActionType.TRIGGER_MINE and not self.system_ready(action.actor, system):
                errors.append(f"{system} system not ready")
            if self.last_action_system.get(action.actor, False):
                errors.append("cannot activate two systems in a row")
        if action.type in (ActionType.TORPEDO, ActionType.MINE, ActionType.TRIGGER_MINE, ActionType.SONAR):
            target = action.payload.get("target")
            if isinstance(target, dict):
                tx, ty = target.get("x"), target.get("y")
                if isinstance(tx, int) and isinstance(ty, int):
                    if not self.map_data.in_bounds(tx, ty):
                        errors.append("target out of bounds")
        if action.type == ActionType.DRONE:
            sector = action.payload.get("sector")
            if isinstance(sector, int):
                max_sector = SECTOR_ROWS * SECTOR_COLS
                if sector < 1 or sector > max_sector:
                    errors.append("sector out of bounds")
        if action.type == ActionType.SILENCE:
            steps = action.payload.get("steps")
            if not isinstance(steps, int) or steps < 1 or steps > MAX_SILENCE_STEPS:
                errors.append(f"SILENCE steps must be 1-{MAX_SILENCE_STEPS}")
        return errors

    def _resolve_action(self, action: Action) -> None:
        if action.type == ActionType.MOVE:
            self._resolve_move(action)
        elif action.type == ActionType.SILENCE:
            self._resolve_silence(action)
        elif action.type == ActionType.TORPEDO:
            self._resolve_torpedo(action)
        elif action.type == ActionType.MINE:
            self._resolve_mine(action)
        elif action.type == ActionType.TRIGGER_MINE:
            self._resolve_trigger_mine(action)
        elif action.type == ActionType.DRONE:
            self._resolve_drone(action)
        elif action.type == ActionType.SONAR:
            self._resolve_sonar(action)
        elif action.type == ActionType.REPAIR:
            self._resolve_repair(action)
        elif action.type == ActionType.SURFACE:
            self._resolve_surface(action.actor, forced=False)
        else:
            self.events.append({"type": "action_noop", "action": action})

    def _resolve_move(self, action: Action) -> None:
        sub = self.subs.get(action.actor)
        if not sub:
            return
        direction = action.payload.get("direction")
        dx, dy = 0, 0
        if direction == "N":
            dy = -1
        elif direction == "S":
            dy = 1
        elif direction == "E":
            dx = 1
        elif direction == "W":
            dx = -1
        nx, ny = sub.x + dx, sub.y + dy
        if self._route_blocked(action.actor, nx, ny):
            self._resolve_surface(action.actor, forced=True)
            return
        sub.x, sub.y = nx, ny
        self.routes[action.actor].add((nx, ny))
        charge = action.payload.get("charge", "torpedo")
        self._charge_gauge(action.actor, charge)
        self.last_action_system[action.actor] = False
        self.events.append({"type": "move", "actor": action.actor, "to": (nx, ny), "charge": charge})

    def _resolve_silence(self, action: Action) -> None:
        sub = self.subs.get(action.actor)
        if not sub:
            return
        direction = action.payload.get("direction")
        steps = action.payload.get("steps", 1)
        dx, dy = 0, 0
        if direction == "N":
            dy = -1
        elif direction == "S":
            dy = 1
        elif direction == "E":
            dx = 1
        elif direction == "W":
            dx = -1
        moved = 0
        for _ in range(int(steps)):
            nx, ny = sub.x + dx, sub.y + dy
            if self._route_blocked(action.actor, nx, ny):
                self._resolve_surface(action.actor, forced=True)
                return
            sub.x, sub.y = nx, ny
            self.routes[action.actor].add((nx, ny))
            moved += 1
        self._consume_gauge(action.actor, "silence")
        charge = action.payload.get("charge", "torpedo")
        self._charge_gauge(action.actor, charge)
        self.last_action_system[action.actor] = True
        self.events.append({"type": "silence", "actor": action.actor, "steps": moved, "to": (sub.x, sub.y)})

    def _resolve_torpedo(self, action: Action) -> None:
        sub = self.subs.get(action.actor)
        if not sub:
            return
        target = action.payload.get("target", {})
        tx, ty = target.get("x"), target.get("y")
        if not isinstance(tx, int) or not isinstance(ty, int):
            return
        if not (sub.x == tx or sub.y == ty):
            self.events.append({"type": "action_failed", "reason": "torpedo not orthogonal", "action": action})
            return
        distance = abs(sub.x - tx) + abs(sub.y - ty)
        if distance < 1 or distance > TORPEDO_RANGE:
            self.events.append({"type": "action_failed", "reason": "torpedo out of range", "action": action})
            return
        self._consume_gauge(action.actor, "torpedo")
        self.last_action_system[action.actor] = True
        self._apply_explosion((tx, ty), source="torpedo", owner=action.actor)

    def _resolve_mine(self, action: Action) -> None:
        sub = self.subs.get(action.actor)
        if not sub:
            return
        target = action.payload.get("target")
        if not isinstance(target, dict):
            return
        tx, ty = target.get("x"), target.get("y")
        if not isinstance(tx, int) or not isinstance(ty, int):
            return
        if abs(sub.x - tx) + abs(sub.y - ty) != 1:
            self.events.append({"type": "action_failed", "reason": "mine must be adjacent", "action": action})
            return
        if self._route_blocked(action.actor, tx, ty):
            self.events.append({"type": "action_failed", "reason": "mine blocked", "action": action})
            return
        if any(mine.x == tx and mine.y == ty for mine in self.mines):
            self.events.append({"type": "action_failed", "reason": "mine exists", "action": action})
            return
        self.mines.append(MineState(x=tx, y=ty, owner=action.actor))
        self._consume_gauge(action.actor, "mine")
        self.last_action_system[action.actor] = True
        self.events.append({"type": "mine_dropped", "actor": action.actor, "target": (tx, ty)})

    def _resolve_trigger_mine(self, action: Action) -> None:
        target = action.payload.get("target")
        if not isinstance(target, dict):
            return
        tx, ty = target.get("x"), target.get("y")
        if not isinstance(tx, int) or not isinstance(ty, int):
            return
        mine_index = next(
            (idx for idx, mine in enumerate(self.mines) if mine.x == tx and mine.y == ty and mine.owner == action.actor),
            None,
        )
        if mine_index is None:
            self.events.append({"type": "action_failed", "reason": "no owned mine", "action": action})
            return
        self.mines.pop(mine_index)
        self.last_action_system[action.actor] = True
        self._apply_explosion((tx, ty), source="mine", owner=action.actor)

    def _resolve_drone(self, action: Action) -> None:
        enemy = self._enemy_of(action.actor)
        if not enemy:
            return
        enemy_sub = self.subs.get(enemy)
        if not enemy_sub:
            return
        sector = int(action.payload.get("sector"))
        enemy_sector = self._sector_for(enemy_sub.x, enemy_sub.y)
        response = sector == enemy_sector
        self._consume_gauge(action.actor, "drone")
        self.last_action_system[action.actor] = True
        self.events.append(
            {"type": "drone", "actor": action.actor, "sector": sector, "response": response, "enemy_sector": enemy_sector}
        )

    def _resolve_sonar(self, action: Action) -> None:
        enemy = self._enemy_of(action.actor)
        if not enemy:
            return
        enemy_sub = self.subs.get(enemy)
        if not enemy_sub:
            return
        true_row = self._row_label(enemy_sub.y)
        true_col = enemy_sub.x + 1
        true_sector = self._sector_for(enemy_sub.x, enemy_sub.y)
        false_row = self._row_label((enemy_sub.y + 1) % self.map_data.height)
        false_col = ((enemy_sub.x + 1) % self.map_data.width) + 1
        false_sector = (true_sector % (SECTOR_ROWS * SECTOR_COLS)) + 1
        pieces = [
            ("row", true_row, False),
            ("col", true_col, False),
            ("sector", true_sector, False),
        ]
        false_pieces = [
            ("row", false_row, True),
            ("col", false_col, True),
            ("sector", false_sector, True),
        ]
        index = self.turn % 3
        true_piece = pieces[index]
        false_piece = next(item for item in false_pieces if item[0] != true_piece[0])
        self._consume_gauge(action.actor, "sonar")
        self.last_action_system[action.actor] = True
        self.events.append(
            {
                "type": "sonar",
                "actor": action.actor,
                "true_info": {"type": true_piece[0], "value": true_piece[1]},
                "false_info": {"type": false_piece[0], "value": false_piece[1]},
            }
        )

    def _resolve_repair(self, action: Action) -> None:
        sub = self.subs.get(action.actor)
        if not sub:
            return
        sub.damage = max(0, sub.damage - 1)
        self.last_action_system[action.actor] = False
        self.events.append({"type": "repair", "actor": action.actor, "damage": sub.damage})

    def _resolve_surface(self, actor: str, forced: bool) -> None:
        sub = self.subs.get(actor)
        if not sub:
            return
        self.skip_turns[actor] = SURFACE_SKIP_TURNS
        self.routes[actor] = {(sub.x, sub.y)}
        self.last_action_system[actor] = False
        sector = self._sector_for(sub.x, sub.y)
        self.events.append({"type": "surface", "actor": actor, "sector": sector, "forced": forced})

    def _route_blocked(self, actor: str, x: int, y: int) -> bool:
        if not self.map_data.in_bounds(x, y):
            return True
        if self.map_data.is_blocked(x, y):
            return True
        if (x, y) in self.routes.get(actor, set()):
            return True
        if any(mine.owner == actor and mine.x == x and mine.y == y for mine in self.mines):
            return True
        return False

    def _apply_explosion(self, impact: Tuple[int, int], source: str, owner: str) -> None:
        ix, iy = impact
        removed = [mine for mine in self.mines if mine.x == ix and mine.y == iy]
        if removed:
            self.mines = [mine for mine in self.mines if not (mine.x == ix and mine.y == iy)]
        hits = []
        for team, sub in self.subs.items():
            distance = abs(sub.x - ix) + abs(sub.y - iy)
            damage = 0
            if distance == 0:
                damage = DAMAGE_DIRECT
            elif distance == 1:
                damage = DAMAGE_INDIRECT
            if damage > 0:
                sub.damage = min(MAX_DAMAGE, sub.damage + damage)
                hits.append({"team": team, "damage": damage})
        self.events.append(
            {
                "type": "explosion",
                "source": source,
                "owner": owner,
                "impact": impact,
                "hits": hits,
                "mine_removed": bool(removed),
            }
        )

    def _enemy_of(self, team: str) -> str | None:
        return next((name for name in self.subs.keys() if name != team), None)

    def _sector_for(self, x: int, y: int) -> int:
        row = min(SECTOR_ROWS - 1, (y * SECTOR_ROWS) // self.map_data.height)
        col = min(SECTOR_COLS - 1, (x * SECTOR_COLS) // self.map_data.width)
        return row * SECTOR_COLS + col + 1

    def _row_label(self, y: int) -> str:
        return chr(ord("A") + y)

    def _check_game_over(self) -> None:
        destroyed = [team for team, sub in self.subs.items() if sub.damage >= MAX_DAMAGE]
        if not destroyed:
            return
        alive = [team for team, sub in self.subs.items() if sub.damage < MAX_DAMAGE]
        self.game_over = True
        self.winner = alive[0] if len(alive) == 1 else None
        self.events.append({"type": "game_over", "winner": self.winner, "destroyed": destroyed})

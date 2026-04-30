from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pygame

from .actions import Action, ActionType
from .config import MAX_ACTIONS_PER_TURN, MAX_SILENCE_STEPS, SECTOR_COLS, SECTOR_ROWS, TILE_SIZE, WINDOW_PADDING
from .map_loader import MapData


@dataclass
class HumanController:
    team: str
    cursor: Tuple[int, int] = (0, 0)
    active_action: Optional[ActionType] = None
    queue: List[Action] = field(default_factory=list)
    confirmed: bool = False
    charge_choice: str = "torpedo"
    map_data: Optional[MapData] = None

    def reset_turn(self) -> None:
        self.queue.clear()
        self.confirmed = False

    def handle_event(self, event: pygame.event.Event, map_data: MapData) -> bool:
        self.map_data = map_data
        if event.type == pygame.KEYDOWN:
            return self._handle_key(event.key)
        if event.type == pygame.MOUSEMOTION:
            self.update_cursor(event.pos, map_data)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click()
        return False

    def update_cursor(self, mouse_pos: Tuple[int, int], map_data: MapData) -> None:
        mx, my = mouse_pos
        gx = (mx - WINDOW_PADDING) // TILE_SIZE
        gy = (my - WINDOW_PADDING) // TILE_SIZE
        if map_data.in_bounds(gx, gy):
            self.cursor = (int(gx), int(gy))

    def _handle_key(self, key: int) -> bool:
        if key == pygame.K_w:
            return self._queue_directional("N")
        if key == pygame.K_s:
            return self._queue_directional("S")
        if key == pygame.K_a:
            return self._queue_directional("W")
        if key == pygame.K_d:
            return self._queue_directional("E")
        if key == pygame.K_t:
            self.active_action = ActionType.TORPEDO
            return True
        if key == pygame.K_f:
            self.active_action = ActionType.SILENCE
            return True
        if key == pygame.K_o:
            self.active_action = ActionType.SONAR
            return True
        if key == pygame.K_v:
            self.active_action = ActionType.DRONE
            return True
        if key == pygame.K_m:
            self.active_action = ActionType.MINE
            return True
        if key == pygame.K_g:
            self.active_action = ActionType.TRIGGER_MINE
            return True
        if key == pygame.K_c:
            self._queue_surface()
            return True
        if key == pygame.K_r:
            self.active_action = ActionType.REPAIR
            self._queue_repair()
            return True
        if key == pygame.K_SPACE:
            self._queue_active()
            return True
        if key == pygame.K_RETURN:
            self.confirmed = True
            return True
        if key == pygame.K_BACKSPACE:
            if self.queue:
                self.queue.pop()
            return True
        if key == pygame.K_ESCAPE:
            self.active_action = None
            return True
        if key == pygame.K_1:
            self.charge_choice = "torpedo"
            return True
        if key == pygame.K_2:
            self.charge_choice = "mine"
            return True
        if key == pygame.K_3:
            self.charge_choice = "sonar"
            return True
        if key == pygame.K_4:
            self.charge_choice = "drone"
            return True
        if key == pygame.K_5:
            self.charge_choice = "silence"
            return True
        if key == pygame.K_6:
            self.charge_choice = "scenario"
            return True
        return False

    def _handle_click(self) -> bool:
        if self.active_action in (
            ActionType.TORPEDO,
            ActionType.SONAR,
            ActionType.MINE,
            ActionType.DRONE,
            ActionType.TRIGGER_MINE,
        ):
            self._queue_active()
            return True
        return False

    def _queue_directional(self, direction: str) -> bool:
        if self.active_action == ActionType.SILENCE:
            self._queue_silence(direction)
            self.active_action = None
            return True
        self.active_action = ActionType.MOVE
        self._queue_move(direction)
        return True

    def _queue_active(self) -> None:
        if self.active_action == ActionType.TORPEDO:
            self._queue_torpedo()
        elif self.active_action == ActionType.SONAR:
            self._queue_sonar()
        elif self.active_action == ActionType.DRONE:
            self._queue_drone()
        elif self.active_action == ActionType.MINE:
            self._queue_mine()
        elif self.active_action == ActionType.TRIGGER_MINE:
            self._queue_trigger_mine()

    def _queue_move(self, direction: str) -> None:
        if len(self.queue) >= MAX_ACTIONS_PER_TURN:
            return
        self.queue.append(
            Action(
                actor=self.team,
                type=ActionType.MOVE,
                payload={"direction": direction, "charge": self.charge_choice},
            )
        )

    def _queue_torpedo(self) -> None:
        if len(self.queue) >= MAX_ACTIONS_PER_TURN:
            return
        x, y = self.cursor
        self.queue.append(
            Action(actor=self.team, type=ActionType.TORPEDO, payload={"target": {"x": x, "y": y}})
        )

    def _queue_sonar(self) -> None:
        if len(self.queue) >= MAX_ACTIONS_PER_TURN:
            return
        self.queue.append(Action(actor=self.team, type=ActionType.SONAR, payload={}))

    def _queue_drone(self) -> None:
        if len(self.queue) >= MAX_ACTIONS_PER_TURN:
            return
        sector = self._cursor_sector()
        if sector is None:
            return
        self.queue.append(Action(actor=self.team, type=ActionType.DRONE, payload={"sector": sector}))

    def _queue_mine(self) -> None:
        if len(self.queue) >= MAX_ACTIONS_PER_TURN:
            return
        x, y = self.cursor
        self.queue.append(Action(actor=self.team, type=ActionType.MINE, payload={"target": {"x": x, "y": y}}))

    def _queue_trigger_mine(self) -> None:
        if len(self.queue) >= MAX_ACTIONS_PER_TURN:
            return
        x, y = self.cursor
        self.queue.append(
            Action(actor=self.team, type=ActionType.TRIGGER_MINE, payload={"target": {"x": x, "y": y}})
        )

    def _queue_silence(self, direction: str) -> None:
        if len(self.queue) >= MAX_ACTIONS_PER_TURN:
            return
        self.queue.append(
            Action(
                actor=self.team,
                type=ActionType.SILENCE,
                payload={"direction": direction, "steps": MAX_SILENCE_STEPS, "charge": self.charge_choice},
            )
        )

    def _queue_repair(self) -> None:
        if len(self.queue) >= MAX_ACTIONS_PER_TURN:
            return
        self.queue.append(Action(actor=self.team, type=ActionType.REPAIR, payload={}))

    def _queue_surface(self) -> None:
        if len(self.queue) >= MAX_ACTIONS_PER_TURN:
            return
        self.queue.append(Action(actor=self.team, type=ActionType.SURFACE, payload={}))

    def ui_state(self) -> Dict[str, object]:
        return {
            "active_action": self.active_action.name if self.active_action else None,
            "queue": [self._format_action(action) for action in self.queue],
            "cursor": self.cursor,
            "charge_choice": self.charge_choice,
        }

    def _format_action(self, action: Action) -> str:
        if action.type == ActionType.MOVE:
            return f"MOVE {action.payload.get('direction')}"
        if action.type == ActionType.TORPEDO:
            target = action.payload.get("target", {})
            return f"TORPEDO ({target.get('x')},{target.get('y')})"
        if action.type == ActionType.REPAIR:
            return "REPAIR"
        if action.type == ActionType.SONAR:
            return "SONAR"
        if action.type == ActionType.DRONE:
            return f"DRONE S{action.payload.get('sector')}"
        if action.type == ActionType.MINE:
            target = action.payload.get("target", {})
            return f"MINE ({target.get('x')},{target.get('y')})"
        if action.type == ActionType.TRIGGER_MINE:
            target = action.payload.get("target", {})
            return f"TRIGGER MINE ({target.get('x')},{target.get('y')})"
        if action.type == ActionType.SILENCE:
            return f"SILENCE {action.payload.get('direction')}"
        if action.type == ActionType.SURFACE:
            return "SURFACE"
        return action.type.value

    def _cursor_sector(self) -> Optional[int]:
        if not self.map_data:
            return None
        x, y = self.cursor
        if not self.map_data.in_bounds(x, y):
            return None
        row = min(SECTOR_ROWS - 1, (y * SECTOR_ROWS) // self.map_data.height)
        col = min(SECTOR_COLS - 1, (x * SECTOR_COLS) // self.map_data.width)
        return row * SECTOR_COLS + col + 1

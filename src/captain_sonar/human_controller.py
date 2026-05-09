from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, cast

import pygame

from .actions import Action, ActionType
from .config import (
    MAP_INNER_PADDING_RIGHT,
    MAP_MARGIN_X,
    MAP_MARGIN_Y,
    MAX_ACTIONS_PER_TURN,
    MAX_SILENCE_STEPS,
    SECTOR_COLS,
    SECTOR_ROWS,
    TILE_SIZE,
    WINDOW_PADDING,
)
from .engineer_layout import engineer_board_geometry, engineer_button_spec, point_in_rect
from .map_loader import MapData


@dataclass
class HumanController:
    team: str
    cursor: Tuple[int, int] = (0, 0)
    active_action: Optional[ActionType] = None
    queue: List[Action] = field(default_factory=list)
    confirmed: bool = False
    charge_choice: str = "torpedo"
    silence_steps: int = MAX_SILENCE_STEPS
    show_engineer_board: bool = False
    engineer_direction: str = "N"
    engineer_index: int = -1
    engineer_button_id: str = ""
    engineer_circuit_part: str = "not"
    engineer_function_type: str = "radioactive"
    _last_mouse_pos: Tuple[int, int] = (0, 0)
    map_data: Optional[MapData] = None

    def reset_turn(self) -> None:
        self.queue.clear()
        self.confirmed = False
        self.active_action = None
        self.silence_steps = MAX_SILENCE_STEPS
        self.engineer_index = -1
        self.engineer_button_id = ""
        self.engineer_circuit_part = "not"
        self.engineer_function_type = "radioactive"

    def handle_event(self, event: pygame.event.Event, map_data: MapData) -> bool:
        self.map_data = map_data
        if event.type == pygame.KEYDOWN:
            return self._handle_key(event.key)
        if event.type == pygame.MOUSEMOTION:
            self._last_mouse_pos = event.pos
            self.update_cursor(event.pos, map_data)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._last_mouse_pos = event.pos
            return self._handle_click(event.pos)
        return False

    def update_cursor(self, mouse_pos: Tuple[int, int], map_data: MapData) -> None:
        mx, my = mouse_pos
        local_x = mx - WINDOW_PADDING - MAP_MARGIN_X
        local_y = my - WINDOW_PADDING - MAP_MARGIN_Y
        if local_x < 0 or local_y < 0:
            return
        gx = local_x // TILE_SIZE
        gy = local_y // TILE_SIZE
        if map_data.in_bounds(int(gx), int(gy)):
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
        if key == pygame.K_q and self.active_action == ActionType.SILENCE:
            self.silence_steps = max(1, self.silence_steps - 1)
            return True
        if key == pygame.K_e and self.active_action == ActionType.SILENCE:
            self.silence_steps = min(MAX_SILENCE_STEPS, self.silence_steps + 1)
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
        if key == pygame.K_p:
            self.show_engineer_board = not self.show_engineer_board
            return True
        if key == pygame.K_1:
            self._set_charge_choice("torpedo")
            return True
        if key == pygame.K_2:
            self._set_charge_choice("mine")
            return True
        if key == pygame.K_3:
            self._set_charge_choice("sonar")
            return True
        if key == pygame.K_4:
            self._set_charge_choice("drone")
            return True
        if key == pygame.K_5:
            self._set_charge_choice("silence")
            return True
        if key == pygame.K_6:
            self._set_charge_choice("scenario")
            return True
        return False

    def _set_charge_choice(self, system: str) -> None:
        """Set preferred charging system and update queued move/silence payloads."""
        self.charge_choice = system
        for action in self.queue:
            if action.type in (ActionType.MOVE, ActionType.SILENCE):
                action.payload["charge"] = system

    def _handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        if self.show_engineer_board and self._handle_engineer_click(mouse_pos):
            return True
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

    def _handle_engineer_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Handle clicks on the image-backed engineer board layout."""
        if not self.map_data:
            return False

        # If a MOVE/SILENCE is already queued, only allow clicking the matching direction.
        queued_direction: str | None = None
        for action in self.queue:
            if action.type in (ActionType.MOVE, ActionType.SILENCE):
                payload_direction = action.payload.get("direction")
                if isinstance(payload_direction, str):
                    queued_direction = payload_direction
                break

        panel_x = self._map_width_px() + 12
        panel_y = WINDOW_PADDING + 32
        layout = engineer_board_geometry(panel_x, panel_y)
        board_rect = cast(Tuple[int, int, int, int], layout["board_rect"])
        if not point_in_rect(mouse_pos, board_rect):
            return False

        def click_on_slot(slot_x: int, slot_y: int, click_x: int, click_y: int) -> bool:
            dx = slot_x - click_x
            dy = slot_y - click_y
            return dx * dx + dy * dy <= 12 * 12

        for direction in ("W", "N", "S", "E"):
            if queued_direction is not None and direction != queued_direction:
                continue
            rows = cast(Dict[str, Dict[str, object]], layout["rows"])
            buttons = cast(List[Tuple[int, int]], rows[direction]["buttons"])
            for slot_idx, (slot_x, slot_y) in enumerate(buttons):
                if click_on_slot(slot_x, slot_y, mouse_pos[0], mouse_pos[1]):
                    spec = engineer_button_spec(direction, slot_idx)
                    if spec is None:
                        return False
                    # When selecting directly on the board (no queued move), follow the clicked direction.
                    self.engineer_direction = direction
                    self.engineer_index = int(slot_idx)
                    self.engineer_button_id = spec.button_id
                    self.engineer_circuit_part = spec.circuit_part
                    self.engineer_function_type = spec.function_type
                    self._sync_engineer_choice_payload()
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

    def _has_system_action(self) -> bool:
        return any(
            action.type
            in (
                ActionType.TORPEDO,
                ActionType.SONAR,
                ActionType.DRONE,
                ActionType.MINE,
                ActionType.TRIGGER_MINE,
                ActionType.REPAIR,
            )
            for action in self.queue
        )

    def _queue_move(self, direction: str) -> None:
        if len(self.queue) >= MAX_ACTIONS_PER_TURN:
            return
        # Move must be the first action in the queue.
        if self._has_system_action():
            return
        self.engineer_direction = direction
        self.queue.append(
            Action(
                actor=self.team,
                type=ActionType.MOVE,
                payload={
                    "direction": direction,
                    "charge": self.charge_choice,
                    "breakdown_choice": self._engineer_choice_payload(direction),
                },
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
        if self._has_system_action():
            return
        self.engineer_direction = direction
        self.queue.append(
            Action(
                actor=self.team,
                type=ActionType.SILENCE,
                payload={
                    "direction": direction,
                    "steps": self.silence_steps,
                    "charge": self.charge_choice,
                    "breakdown_choice": self._engineer_choice_payload(direction),
                },
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

    def _current_engineer_direction(self) -> str | None:
        for action in self.queue:
            if action.type in (ActionType.MOVE, ActionType.SILENCE):
                payload_direction = action.payload.get("direction")
                if isinstance(payload_direction, str):
                    return payload_direction
        if self.engineer_direction in ("N", "S", "E", "W"):
            return self.engineer_direction
        return None

    def _sync_engineer_choice_payload(self) -> None:
        """Push the current engineer button selection into the queued movement action."""
        for action in self.queue:
            if action.type in (ActionType.MOVE, ActionType.SILENCE):
                direction = action.payload.get("direction")
                if isinstance(direction, str):
                    action.payload["breakdown_choice"] = self._engineer_choice_payload(direction)
                break

    def ui_state(self) -> Dict[str, object]:
        return {
            "team": self.team,
            "active_action": self.active_action.name if self.active_action else None,
            "queue": [self._format_action(action) for action in self.queue],
            "cursor": self.cursor,
            "charge_choice": self.charge_choice,
            "silence_steps": self.silence_steps,
            "show_engineer_board": self.show_engineer_board,
            "engineer_direction": self._current_engineer_direction(),
            "engineer_choice": self._engineer_choice_payload(None),
        }

    def _engineer_choice_payload(self, direction: str | None) -> Dict[str, object]:
        choice_direction = direction or self.engineer_direction
        return {
            "button_id": self.engineer_button_id,
            "direction": choice_direction,
            "slot": self.engineer_index,
            "circuit_part": self.engineer_circuit_part,
            "function_type": self.engineer_function_type,
        }

    def _map_width_px(self) -> int:
        if not self.map_data:
            return 0
        return self.map_data.width * TILE_SIZE + MAP_MARGIN_X + MAP_INNER_PADDING_RIGHT

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

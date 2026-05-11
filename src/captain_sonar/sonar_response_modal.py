from __future__ import annotations

from dataclasses import dataclass

import pygame

from .actions import Action
from .game_state import GameState
from .renderer import Renderer


@dataclass
class SonarResponseModal:
    state: GameState
    active: bool = False
    pending_team: str | None = None
    pending_action: Action | None = None
    true_type: str | None = None
    false_type: str | None = None
    false_value: str | int | None = None
    stage: str = "true_type"
    buffer: str = ""

    def start(self, action: Action, defending_team: str) -> None:
        self.pending_action = Action(actor=action.actor, type=action.type, payload=dict(action.payload))
        self.pending_team = defending_team
        self.active = True
        self.stage = "true_type"
        self.true_type = None
        self.false_type = None
        self.false_value = None
        self.buffer = ""

    def cancel(self) -> None:
        self.active = False
        self.pending_team = None
        self.pending_action = None
        self.stage = "true_type"
        self.true_type = None
        self.false_type = None
        self.false_value = None
        self.buffer = ""

    def handle_event(self, event: pygame.event.Event) -> Action | None:
        if not self.active:
            return None

        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            self.cancel()
            return None

        if self.stage == "true_type":
            chosen = self._type_from_key(event.key)
            if chosen is not None:
                self.true_type = chosen
                self.stage = "false_type"
            return None

        if self.stage == "false_type":
            chosen = self._false_type_from_key(event.key)
            if chosen is not None and chosen != self.true_type:
                self.false_type = chosen
                self.stage = "false_value"
                self.buffer = ""
            return None

        if self.stage == "false_value":
            if event.key == pygame.K_BACKSPACE:
                self.buffer = self.buffer[:-1]
                return None
            if event.key == pygame.K_RETURN:
                if self._value_is_valid(self.buffer, self.false_type):
                    self.false_value = self._normalize_value(self.buffer, self.false_type)
                    return self.commit()
                return None

            typed = getattr(event, "unicode", "")
            if not typed:
                return None
            if self.false_type == "row":
                if typed.isalpha():
                    candidate = (self.buffer + typed.upper())[:1]
                    if self._value_is_valid(candidate, self.false_type):
                        self.buffer = candidate
            else:
                if typed.isdigit():
                    candidate = self.buffer + typed
                    if len(candidate) <= 2:
                        self.buffer = candidate
            return None

        return None

    def render(self, renderer: Renderer) -> None:
        if not self.active or self.pending_team is None:
            return
        renderer.draw_sonar_response_menu(
            self.pending_team,
            self.true_type,
            self.false_type,
            self.false_value,
            self.state,
            self.stage,
            self.buffer,
        )

    def commit(self) -> Action | None:
        if self.pending_action is None:
            return None
        self.pending_action.payload["true_type"] = self.true_type
        self.pending_action.payload["false_type"] = self.false_type
        self.pending_action.payload["false_value"] = self.false_value
        action = self.pending_action
        self.cancel()
        return action

    @property
    def waiting_team(self) -> str | None:
        return self.pending_team if self.active else None

    def _type_from_key(self, key: int) -> str | None:
        mapping = {
            pygame.K_1: "row",
            pygame.K_KP1: "row",
            pygame.K_2: "col",
            pygame.K_KP2: "col",
            pygame.K_3: "sector",
            pygame.K_KP3: "sector",
        }
        return mapping.get(key)

    def _false_type_from_key(self, key: int) -> str | None:
        options = [t for t in ("row", "col", "sector") if t != self.true_type]
        mapping = {
            pygame.K_1: options[0] if len(options) > 0 else None,
            pygame.K_KP1: options[0] if len(options) > 0 else None,
            pygame.K_2: options[1] if len(options) > 1 else None,
            pygame.K_KP2: options[1] if len(options) > 1 else None,
            pygame.K_3: options[2] if len(options) > 2 else None,
            pygame.K_KP3: options[2] if len(options) > 2 else None,
        }
        return mapping.get(key)

    def _value_is_valid(self, value_text: str, sonar_type: str | None) -> bool:
        if sonar_type is None:
            return False
        if sonar_type == "row":
            return len(value_text) == 1 and "A" <= value_text.upper() <= "O"
        if sonar_type == "col":
            return value_text.isdigit() and 1 <= int(value_text) <= 15
        if sonar_type == "sector":
            return value_text.isdigit() and 1 <= int(value_text) <= 9
        return False

    def _normalize_value(self, value_text: str, sonar_type: str | None) -> str | int:
        if sonar_type == "row":
            return value_text.upper()
        return int(value_text)

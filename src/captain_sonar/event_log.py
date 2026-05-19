from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable

from .actions import Action, action_to_dict


class EventLogger:
    def __init__(
        self,
        path: str,
        state_path: str | None = None,
        turn_start_log: bool = False,
        possible_actions_path: str | None = None,
    ) -> None:
        self.path = path
        self.state_path = state_path
        self.turn_start_log = turn_start_log
        self.possible_actions_path = possible_actions_path
        self._header_written = False

    def log_header(self, meta: dict) -> None:
        if self._header_written:
            return
        if os.path.exists(self.path) and os.path.getsize(self.path) > 0:
            self._header_written = True
            return
        payload = {"type": "meta", **meta}
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
        self._header_written = True

    def log_turn(self, turn: int, actions: Iterable[Any], events: Iterable[Any]) -> None:
        payload = {
            "turn": turn,
            "actions": [self._serialize(item) for item in actions],
            "events": [self._serialize(item) for item in events],
        }
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def log_turn_start(self, turn: int, team: str, phase: str) -> None:
        if not self.turn_start_log:
            return
        payload = {
            "type": "turn_start",
            "turn": turn,
            "team": team,
            "phase": phase,
        }
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def log_possible_actions(
        self,
        turn: int,
        team: str,
        phase: str,
        role: str,
        possible_actions: Iterable[Any],
    ) -> None:
        if not self.possible_actions_path:
            return
        payload = {
            "type": "possible_actions",
            "turn": turn,
            "team": team,
            "phase": phase,
            "role": role,
            "possible_actions": [self._serialize(item) for item in possible_actions],
        }
        with open(self.possible_actions_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def log_state_snapshot(self, turn: int, state: Any) -> None:
        if not self.state_path:
            return
        payload = self._serialize(state)
        if isinstance(payload, dict):
            payload = {"type": "state_snapshot", "turn": turn, **payload}
        else:
            payload = {"type": "state_snapshot", "turn": turn, "state": payload}
        with open(self.state_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def log_team_view(self, turn: int, team: str, view: Any) -> None:
        if not self.state_path:
            return
        payload = self._serialize(view)
        if isinstance(payload, dict):
            payload = {"type": "team_view", "turn": turn, "team": team, **payload}
        else:
            payload = {"type": "team_view", "turn": turn, "team": team, "view": payload}
        with open(self.state_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def _serialize(self, item: Any) -> Any:
        if isinstance(item, Action):
            return action_to_dict(item)
        # asdict expects a dataclass instance, not a dataclass type
        if is_dataclass(item) and not isinstance(item, type):
            return asdict(item)
        if isinstance(item, dict):
            return {key: self._serialize(value) for key, value in item.items()}
        if isinstance(item, (list, tuple)):
            return [self._serialize(value) for value in item]
        return item

from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable

from .actions import Action, action_to_dict


class EventLogger:
    def __init__(self, path: str) -> None:
        self.path = path
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

    def _serialize(self, item: Any) -> Any:
        if isinstance(item, Action):
            return action_to_dict(item)
        if is_dataclass(item):
            return asdict(item)
        if isinstance(item, dict):
            return {key: self._serialize(value) for key, value in item.items()}
        if isinstance(item, (list, tuple)):
            return [self._serialize(value) for value in item]
        return item

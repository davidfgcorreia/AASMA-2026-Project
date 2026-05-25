from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Tuple, Callable, Mapping

# Small compatibility types expected by other manager helpers
GridPos = Tuple[int, int]
StartPositionPicker = Callable[[str, Any, Mapping[str, Any]], GridPos | None]


@dataclass
class AgentManagerConfig:
    activation_duration_ms: int = 1000
    operating_mode: str | None = None
    ledger_base_path: str | None = None
    disable_ledgers: bool = False
    strategy_profile: dict[str, Any] | None = None
    # Messaging limits (consumed by manager/messaging.py)
    max_message_length: int = 2048
    max_messages_per_turn: int = 32
    max_messages_per_pair_per_turn: int = 4


@dataclass
class AgentMessage:
    sender: Any
    recipient: Any | None
    turn_id: int
    text: str
    metadata: dict[str, Any] | None = None


@dataclass
class ExecutionRecord:
    record: dict | None = None


class TeamOperatingMode(Enum):
    DEFAULT = "default"

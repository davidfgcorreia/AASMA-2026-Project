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
    max_message_length: int = 2000
    max_messages_per_turn: int = 50
    max_messages_per_pair_per_turn: int = 5


@dataclass
class AgentMessage:
    sender: Any
    recipient: Any | None
    text: str
    metadata: dict[str, Any] | None = None
    turn_id: int = 0


@dataclass
class ExecutionRecord:
    record: dict | None = None


class TeamOperatingMode(Enum):
    DEFAULT = "default"

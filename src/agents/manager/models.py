from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping, Tuple
from pathlib import Path
from typing import Optional

from captain_sonar.map_loader import MapData

from ..base import AgentRole


GridPos = Tuple[int, int]
StartPositionPicker = Callable[[str, MapData, Mapping[str, Any]], GridPos | None]


class TeamOperatingMode(str, Enum):
    FULL_TEAM = "full_team"
    THREE_AGENT = "three_agent"


@dataclass(slots=True)
class AgentMessage:
    sender: AgentRole
    recipient: AgentRole | None
    turn_id: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TurnIterationRecord:
    iteration: int
    proposals: dict[str, dict[str, Any]]
    inbox_snapshot: dict[str, list[dict[str, Any]]]


@dataclass(slots=True)
class DecisionRecord:
    accepted: list[dict[str, Any]]
    omitted: list[dict[str, Any]]


@dataclass(slots=True)
class ExecutionRecord:
    turn_id: int
    accepted_intents: list[dict[str, Any]]
    executed_actions: list[dict[str, Any]]
    rejected_intents: list[dict[str, Any]]
    events: list[dict[str, Any]]
    success: bool
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AgentManagerConfig:
    max_messages_per_turn: int = 12
    max_messages_per_pair_per_turn: int = 3
    max_message_length: int = 2_000
    activation_duration_ms: int = 5_000
    operating_mode: TeamOperatingMode = TeamOperatingMode.FULL_TEAM
    human_role: AgentRole | None = None
    # If provided, ledger files (turn actions and iteration logs) will be written
    # under this path. If None, the default `src/agents/common` path is used.
    ledger_base_path: Optional[Path] = None
    # When True the manager will not write any ledger files.
    disable_ledgers: bool = False

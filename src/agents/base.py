from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentRole(str, Enum):
    CAPTAIN = "captain"
    FIRST_MATE = "first_mate"
    ENGINEER = "engineer"
    RADIO_OPERATOR = "radio_operator"


@dataclass
class AgentBase(ABC):
    """Base class for role-specific agent logic."""

    team: str
    role: AgentRole
    last_observation: dict[str, Any] = field(default_factory=dict)

    def observe(self, state_snapshot: dict[str, Any]) -> None:
        """Store the latest state snapshot for this agent."""
        self.last_observation = dict(state_snapshot)

    @abstractmethod
    def act(self, deadline_ms: int) -> dict[str, Any]:
        """Return an action payload for the current role."""
        raise NotImplementedError

    def propose_action(self, team_view: dict[str, Any]) -> dict[str, Any]:
        """Return a role-specific first-step/second-step proposal."""
        raise NotImplementedError

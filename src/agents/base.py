from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from typing import Optional


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
        """Return a role-specific first-step/second-step proposal.

        The proposal is a dict describing the role's intended turn action. In
        addition to the action payload (e.g. {"type": "MOVE", "payload": {...}})
        the proposal may include an optional `messages` field to send bounded
        inter-agent messages during the iteration cycle. The `messages` value
        must be a list of message dicts with the following keys:

        - `recipient`: Optional[str] — role name to deliver to (e.g. "engineer");
          if omitted or None the message is broadcast to all other active roles.
        - `text`: str — the message payload (max length enforced by manager).
        - `metadata`: Optional[dict] — free-form metadata the sender wishes to attach.

        Example:

        {
            "type": "MOVE",
            "payload": {"direction": "N"},
            "messages": [
                {"recipient": "engineer", "text": "Align to bearing 3", "metadata": {"urgency": 1}}
            ]
        }
        """
        raise NotImplementedError


@dataclass
class MessageSpec:
    """A convenience container describing an inter-agent message.

    Fields:
    - `recipient`: role name string or None to indicate broadcast
    - `text`: the message body
    - `metadata`: optional dict for additional data
    """
    recipient: Optional[str]
    text: str
    metadata: dict[str, Any] | None = None

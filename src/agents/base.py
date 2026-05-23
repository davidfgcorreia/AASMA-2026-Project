from __future__ import annotations

from enum import Enum
from typing import Any


class AgentRole(Enum):
    CAPTAIN = "CAPTAIN"
    FIRST_MATE = "FIRST_MATE"
    ENGINEER = "ENGINEER"
    RADIO_OPERATOR = "RADIO_OPERATOR"


class AgentBase:
    def __init__(self, team: str, role: AgentRole) -> None:
        self.team = team
        self.role = role

    def observe(self, view: Any) -> None:
        return None

    def propose_action(self, view: Any) -> Any:
        return None

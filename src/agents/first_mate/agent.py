from __future__ import annotations

from dataclasses import dataclass

from ..base import AgentBase, AgentRole
from captain_sonar.possible_actions import possible_actions_for_role


@dataclass
class FirstMateAgent(AgentBase):
    """First mate role agent placeholder."""

    def __init__(self, team: str) -> None:
        super().__init__(team=team, role=AgentRole.FIRST_MATE)

    def act(self, deadline_ms: int) -> dict[str, object]:
        raise NotImplementedError("FirstMateAgent logic is not implemented yet.")

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        possible_actions = possible_actions_for_role(self.role.value, team_view)
        ready = team_view.get("system_utilization", {}).get("ready", {})
        preferred_system = next((system for system, is_ready in ready.items() if is_ready), "torpedo")
        return {
            "role": self.role.value,
            "first_step": {"type": "CHARGE", "payload": {"system": preferred_system}},
            "second_step": {"type": "ACTIVATE", "payload": {"system": preferred_system}},
            "full_action": None,
            "possible_actions": possible_actions,
        }

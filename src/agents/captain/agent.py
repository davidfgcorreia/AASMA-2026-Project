from __future__ import annotations

from dataclasses import dataclass

from ..base import AgentBase, AgentRole
from captain_sonar.possible_actions import possible_actions_for_role


@dataclass
class CaptainAgent(AgentBase):
    """Captain role agent placeholder."""

    def __init__(self, team: str) -> None:
        super().__init__(team=team, role=AgentRole.CAPTAIN)

    def act(self, deadline_ms: int) -> dict[str, object]:
        raise NotImplementedError("CaptainAgent logic is not implemented yet.")

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        candidate_actions = possible_actions_for_role(self.role.value, team_view)
        chosen_action = candidate_actions[0] if candidate_actions else {"type": "MOVE", "payload": {"direction": "N"}}
        system_utilization = team_view.get("system_utilization")
        preferred_system = "torpedo"
        if isinstance(system_utilization, dict):
            preferred_system = str(system_utilization.get("preferred_system", preferred_system))
        first_step = chosen_action
        second_step = {
            "type": "SYSTEM",
            "payload": {
                "system": preferred_system,
            },
        }
        return {
            "role": self.role.value,
            "first_step": first_step,
            "second_step": second_step,
            "full_action": chosen_action,
            "possible_actions": candidate_actions,
        }

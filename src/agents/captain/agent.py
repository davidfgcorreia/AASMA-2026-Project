from __future__ import annotations

from dataclasses import dataclass

from ..base import AgentBase, AgentRole
from ..common.functions import monte_carlo_exploration
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
        exploration = self.monte_carlo_exploration(team_view, candidate_actions)
        chosen_action = exploration.get("selected_action") or {}
        system_utilization = team_view.get("system_utilization")
        preferred_system = "torpedo"
        if isinstance(system_utilization, dict):
            preferred_system = str(system_utilization.get("preferred_system", preferred_system))
        first_step = chosen_action if chosen_action else {"type": "MOVE", "payload": {"direction": "N"}}
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
            "exploration": exploration,
        }

    def monte_carlo_exploration(
        self,
        team_view: dict[str, object],
        candidate_actions: list[dict[str, object]],
        rollouts: int = 24,
        seed: int | None = None,
    ) -> dict[str, object]:
        """Run the simple Monte Carlo exploration helper for captain decisions."""
        return monte_carlo_exploration(
            team_view=team_view,
            role=self.role,
            candidate_actions=candidate_actions,
            rollouts=rollouts,
            seed=seed,
        )

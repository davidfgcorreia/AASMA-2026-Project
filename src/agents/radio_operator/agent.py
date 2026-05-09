from __future__ import annotations

from dataclasses import dataclass

from ..base import AgentBase, AgentRole
from captain_sonar.possible_actions import possible_actions_for_role


@dataclass
class RadioOperatorAgent(AgentBase):
    """Radio operator role agent placeholder."""

    def __init__(self, team: str) -> None:
        super().__init__(team=team, role=AgentRole.RADIO_OPERATOR)

    def act(self, deadline_ms: int) -> dict[str, object]:
        raise NotImplementedError("RadioOperatorAgent logic is not implemented yet.")

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        possible_actions = possible_actions_for_role(self.role.value, team_view)
        radio = team_view.get("radio_operator", {})
        return {
            "role": self.role.value,
            "first_step": {
                "type": "TRACK",
                "payload": {
                    "most_likely_position": radio.get("most_likely_position"),
                    "most_likely_sector": radio.get("most_likely_sector"),
                    "confidence": radio.get("confidence", 0.0),
                },
            },
            "second_step": {
                "type": "SENSOR_SUGGESTION",
                "payload": {
                    "system": "drone" if radio.get("most_likely_sector") else "sonar",
                },
            },
            "full_action": None,
            "possible_actions": possible_actions,
        }

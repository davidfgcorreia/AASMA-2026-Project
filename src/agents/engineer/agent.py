from __future__ import annotations

from dataclasses import dataclass

from ..base import AgentBase, AgentRole
from captain_sonar.possible_actions import possible_actions_for_role


@dataclass
class EngineerAgent(AgentBase):
    """Engineer role agent placeholder."""

    def __init__(self, team: str) -> None:
        super().__init__(team=team, role=AgentRole.ENGINEER)

    def act(self, deadline_ms: int) -> dict[str, object]:
        raise NotImplementedError("EngineerAgent logic is not implemented yet.")

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        possible_actions = possible_actions_for_role(self.role.value, team_view)
        engineer_board = team_view.get("engineer_board", {})
        buttons_by_direction = engineer_board.get("buttons_by_direction", {}) if isinstance(engineer_board, dict) else {}
        direction = team_view.get("own_routes", []) and team_view.get("turn") is not None
        selected_direction = next(iter(buttons_by_direction), "N")
        chosen_button = buttons_by_direction.get(selected_direction, [{}])[0] if buttons_by_direction else {}
        return {
            "role": self.role.value,
            "first_step": {
                "type": "ENGINEER_SELECTION",
                "payload": {
                    "direction": selected_direction,
                    "button_id": chosen_button.get("button_id"),
                    "slot_index": chosen_button.get("slot_index"),
                    "circuit_part": chosen_button.get("circuit_part"),
                    "function_type": chosen_button.get("function_type"),
                },
            },
            "second_step": {"type": "REPAIR", "payload": {}},
            "full_action": None,
            "possible_actions": possible_actions,
        }

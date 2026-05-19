from __future__ import annotations

from dataclasses import dataclass

from ..base import AgentBase, AgentRole
from captain_sonar.possible_actions import possible_actions_for_role
from agents.common.functions import call_agent_activity
import json
import os


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


@dataclass(init=False)
class ModelCaptainAgent(CaptainAgent):
    """Model-driven captain agent that calls the activity helper.

    The agent asks the model to choose one of the compact `possible_actions`
    and return a JSON object describing the chosen action. If the model
    output cannot be parsed, the agent falls back to the rule-based choice.
    """

    def __init__(self, team: str) -> None:
        super().__init__(team=team)

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        possible_actions = possible_actions_for_role(self.role.value, team_view)
        # Build a concise prompt asking for a single JSON action selection.
        choices = [str(action) for action in possible_actions]
        goal = (
            "Select a single action from the list named `choices` and reply ONLY with a JSON object"
            " containing keys `type` and optional `payload`. Example: {\"type\": \"MOVE\", \"payload\": {\"direction\": \"N\"}}"
        )
        constraints = [
            "Return valid JSON only.",
            "Do not include commentary.",
            "If uncertain, pick the first valid action.",
        ]
        prompt = goal + "\nchoices:\n" + "\n".join(choices)

        model = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"
        try:
            response = call_agent_activity(
                model=model,
                prompt=prompt,
                team_view=team_view,
                role=self.role,
                max_output_tokens=512,
            )
            text = response.text.strip()
            # Attempt to parse JSON from the model output.
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "type" in parsed:
                full_action = parsed
            else:
                raise ValueError("parsed JSON missing 'type'")
        except Exception:
            # Fallback to deterministic choice
            full_action = possible_actions[0] if possible_actions else {"type": "MOVE", "payload": {"direction": "N"}}

        # Build standard proposal envelope
        first_step = full_action
        second_step = {"type": "SYSTEM", "payload": {"system": "torpedo"}}
        return {
            "role": self.role.value,
            "first_step": first_step,
            "second_step": second_step,
            "full_action": full_action,
            "possible_actions": possible_actions,
        }

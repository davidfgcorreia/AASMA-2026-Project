"""Adapter to convert manager intents into engine actions and execute them.

This module exposes `ManagerGameApiAdapter` which validates a list of manager
intents, deduplicates by action signature, converts them to engine `Action`
objects and calls the Captain Sonar API to apply them to the provided
`GameState`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from captain_sonar.actions import Action, ActionType, action_to_dict
from captain_sonar.api import apply_actions
from captain_sonar.game_state import GameState

from ..base import AgentRole
from ..common.functions import action_signature
from .models import ExecutionRecord


@dataclass(slots=True)
class ManagerGameApiAdapter:
    team: str
    active_roles: set[AgentRole] = field(default_factory=set)
    turn_id: int | None = None

    def execute_turn_actions(self, state: GameState, intents: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> ExecutionRecord:
        accepted_intents: list[dict[str, Any]] = []
        rejected_intents: list[dict[str, Any]] = []
        executed_actions: list[Action] = []
        errors: list[str] = []
        seen_signatures: set[str] = set()

        for intent in intents:
            intent_data = dict(intent) if isinstance(intent, Mapping) else {"value": intent}
            validation_errors = self._validate_intent(intent_data)
            if validation_errors:
                rejected_intents.append(
                    {
                        "intent": intent_data,
                        "reason": "invalid_intent",
                        "errors": validation_errors,
                    }
                )
                errors.extend(validation_errors)
                continue

            action = self._intent_to_action(intent_data)
            if action is None:
                rejected_intents.append(
                    {
                        "intent": intent_data,
                        "reason": "invalid_intent",
                        "errors": ["unsupported action type"],
                    }
                )
                errors.append("unsupported action type")
                continue

            signature = action_signature({"type": action.type.value, "payload": action.payload})
            if signature in seen_signatures:
                accepted_intents.append(intent_data)
                continue

            seen_signatures.add(signature)
            accepted_intents.append(intent_data)
            executed_actions.append(action)

        try:
            apply_actions(state, executed_actions)
        except Exception as exc:  # pragma: no cover - defensive guard
            errors.append(str(exc))
            rejected_intents.append(
                {
                    "intent": None,
                    "reason": "execution_failed",
                    "errors": [str(exc)],
                }
            )

        events = [dict(event) for event in state.events]
        success = not errors and not any(event.get("type") in {"action_rejected", "action_failed"} for event in events)

        return ExecutionRecord(
            turn_id=self.turn_id if self.turn_id is not None else state.turn,
            accepted_intents=accepted_intents,
            executed_actions=[action_to_dict(action) for action in executed_actions],
            rejected_intents=rejected_intents,
            events=events,
            success=success,
            errors=errors,
        )

    def _validate_intent(self, intent: Mapping[str, Any]) -> list[str]:
        errors: list[str] = []
        allowed_keys = {"role", "turn_id", "type", "payload", "reasoning", "confidence"}
        unexpected = sorted(set(intent) - allowed_keys)
        if unexpected:
            errors.append(f"unexpected fields: {unexpected}")

        role_value = intent.get("role")
        if not isinstance(role_value, str):
            errors.append("role must be a string")
        else:
            try:
                role = AgentRole(role_value)
            except ValueError:
                errors.append(f"unknown role {role_value!r}")
            else:
                if self.active_roles and role not in self.active_roles:
                    errors.append(f"inactive role {role_value!r}")

        turn_id = intent.get("turn_id")
        if not isinstance(turn_id, int):
            errors.append("turn_id must be an integer")
        elif self.turn_id is not None and turn_id != self.turn_id:
            errors.append(f"turn_id {turn_id} does not match active turn {self.turn_id}")

        action_type = intent.get("type")
        if not isinstance(action_type, str):
            errors.append("type must be a string")
        elif action_type.strip().upper() not in ActionType.__members__:
            errors.append(f"unsupported action type {action_type!r}")

        payload = intent.get("payload")
        if not isinstance(payload, dict):
            errors.append("payload must be a dictionary")

        reasoning = intent.get("reasoning")
        if reasoning is not None and not isinstance(reasoning, str):
            errors.append("reasoning must be a string when provided")

        confidence = intent.get("confidence")
        if confidence is not None and not isinstance(confidence, (int, float)):
            errors.append("confidence must be numeric when provided")

        return errors

    def _intent_to_action(self, intent: Mapping[str, Any]) -> Action | None:
        type_value = str(intent.get("type", "")).strip().upper()
        try:
            action_type = ActionType[type_value]
        except KeyError:
            return None

        payload = dict(intent.get("payload", {}))
        return Action(actor=self.team, type=action_type, payload=payload)
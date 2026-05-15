"""Iteration orchestration for TeamAgentManager.

This module contains the bounded proposal/iteration loop that was previously
embedded inside `TeamAgentManager.run_turn_cycle`. Moving it here keeps the
manager focused on lifecycle concerns while making the iteration logic
independently testable.

Public API:
- `run_iteration_cycle(manager, state, max_iterations, deadline_ms)` -> list[dict]
  Runs up to `max_iterations` of proposal collection, message delivery and
  inbox observation. The function mutates the provided `manager` instance by
  recording proposals and votes through `propose_turn_action` and
  `omit_turn_action` and by sending messages via `manager.send_message`.
"""

from __future__ import annotations

from typing import Any
from captain_sonar.game_state import GameState


def run_iteration_cycle(manager, state: GameState, max_iterations: int = 1, deadline_ms: int | None = None) -> list[dict[str, Any]]:
    iterations: list[dict[str, Any]] = []
    prev_proposals: dict[str, dict[str, Any]] | None = None

    for it in range(max_iterations):
        proposals: dict[str, dict[str, Any]] = {}
        # Collect proposals from active agents
        for role in list(manager._active_roles):
            agent = manager._agents.get(role)
            if agent is None:
                continue
            try:
                proposal = agent.propose_action(manager._build_role_view(role))
            except Exception:
                proposal = {"type": "OMIT", "role": role.value, "turn_id": manager._turn_id}
            proposals[role.value] = dict(proposal or {})

        # Apply any messages embedded in proposals
        messages_sent = 0
        for r_name, prop in proposals.items():
            if not prop:
                continue
            msgs = prop.get("messages") or []
            if not isinstance(msgs, list):
                continue
            sender_role = next((rl for rl in manager._agents if rl.value == r_name), None)
            for msg in msgs:
                recipient_name = msg.get("recipient")
                if recipient_name is None:
                    recipient_role = None
                else:
                    recipient_role = next((rl for rl in manager._agents if rl.value == recipient_name), None)
                text = msg.get("text", "")
                metadata = msg.get("metadata")
                if sender_role is not None and text:
                    if manager.send_message(sender_role, recipient_role, text, metadata):
                        messages_sent += 1

        inbox_snapshot = {role.value: manager.read_inbox(role) for role in manager._active_roles}
        iterations.append({"iteration": it, "proposals": proposals, "inbox": inbox_snapshot})

        # Write proposals into manager's ledger for collection (votes/proposals)
        for r, prop in proposals.items():
            role_obj = next((rl for rl in manager._agents if rl.value == r), None)
            if role_obj is not None:
                if prop.get("type") == "OMIT":
                    manager.omit_turn_action(role_obj)
                else:
                    prop_copy = dict(prop)
                    prop_copy.pop("messages", None)
                    manager.propose_turn_action(role_obj, prop_copy)

        # If there were no messages and proposals didn't change from previous iteration, stop early
        if messages_sent == 0 and prev_proposals is not None and prev_proposals == proposals:
            break
        prev_proposals = proposals

        # let agents observe the updated inboxes before the next iteration
        for role, agent in manager._agents.items():
            if role not in manager._active_roles:
                continue
            try:
                agent.observe(manager._build_role_view(role))
            except Exception:
                # observation failures should not break the manager loop
                continue

    return iterations

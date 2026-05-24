"""Iteration orchestration helpers for TeamAgentManager.

This module contains the bounded proposal/iteration loop previously
located at the manager package root. It runs up to `max_iterations`
collecting proposals, delivering messages and updating inboxes.

Public API:
- `run_iteration_cycle(manager, state, max_iterations, deadline_ms)` -> list[dict]
  Runs up to `max_iterations` of proposal collection, message delivery and
  inbox observation. The function mutates the provided `manager` instance by
  recording proposals and votes through `propose_turn_action` and
  `omit_turn_action` and by sending messages via `manager.send_message`.
"""

from __future__ import annotations

from typing import Any

from captain_sonar.actions import Action, ActionType
from captain_sonar.game_state import GameState
from .manager_helpers import build_turn_start_context_bundle
from .manager_helpers import write_play_context_for_manager
from .manager_helpers import run_turn_start_call
# manager_api imports are performed lazily inside functions to avoid
# circular import problems between this module and `manager_api`.


def run_turn_start_phase(manager, state: GameState) -> dict[str, Any]:
    from .manager_api import begin_turn as manager_begin_turn

    context_report = manager_begin_turn(manager, state)
    write_play_context_for_manager(
        manager,
        context_report["team_view"],
        round_type=context_report["round_type"],
        source=context_report["source"],
    )
    bundle = build_turn_start_context_bundle(manager, context_report)
    bundle["turn_start_results"] = run_turn_start_call(bundle)
    return context_report


def run_discussion_phase(manager, state: GameState, max_iterations: int = 1, deadline_ms: int | None = None) -> list[dict[str, Any]]:
    # Run the bounded iteration cycle using the currently active roles.
    return run_iteration_cycle(manager, state, max_iterations=max_iterations, deadline_ms=deadline_ms)


def run_finalization_phase(manager) -> list[dict[str, Any]]:
    from .manager_api import choose_turn_actions as manager_choose_turn_actions
    return manager_choose_turn_actions(manager)


def run_send_phase(manager, accepted: list[dict[str, Any]], team: str, phase: str) -> list[Action]:
    allowed = (
        {ActionType.MOVE, ActionType.SURFACE}
        if phase == "move"
        else {
            ActionType.SILENCE,
            ActionType.TORPEDO,
            ActionType.SONAR,
            ActionType.DRONE,
            ActionType.MINE,
            ActionType.TRIGGER_MINE,
        }
    )

    actions: list[Action] = []
    for proposal in accepted:
        action = _to_action(team, proposal)
        if action is not None and action.type in allowed:
            actions.append(action)
            break
    return actions


def _to_action(default_team: str, payload: object) -> Action | None:
    if not isinstance(payload, dict):
        return None
    raw_type = payload.get("type")
    if not isinstance(raw_type, str):
        return None
    try:
        action_type = ActionType[raw_type.strip().upper()]
    except KeyError:
        return None
    raw_payload = payload.get("payload")
    normalized_payload = raw_payload if isinstance(raw_payload, dict) else {}
    actor = payload.get("actor", default_team)
    if not isinstance(actor, str):
        actor = default_team
    return Action(actor=actor, type=action_type, payload=normalized_payload)


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
                from .manager_api import build_role_view as manager_build_role_view

                proposal = agent.propose_action(manager_build_role_view(manager, role))
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
                    from .manager_api import send_message as manager_send_message

                    if manager_send_message(manager, sender_role, recipient_role, text, metadata):
                        messages_sent += 1

        from .manager_api import read_inbox as manager_read_inbox

        inbox_snapshot = {role.value: manager_read_inbox(manager, role) for role in manager._active_roles}
        iterations.append({"iteration": it, "proposals": proposals, "inbox": inbox_snapshot})

        # Write proposals into the manager's turn action records (votes/proposals)
        for r, prop in proposals.items():
            role_obj = next((rl for rl in manager._agents if rl.value == r), None)
            if role_obj is not None:
                if prop.get("type") == "OMIT":
                    from .manager_api import omit_turn_action as manager_omit_turn_action

                    manager_omit_turn_action(manager, role_obj)
                else:
                    prop_copy = dict(prop)
                    prop_copy.pop("messages", None)
                    from .manager_api import propose_turn_action as manager_propose_turn_action

                    manager_propose_turn_action(manager, role_obj, prop_copy)

        # If there were no messages and proposals didn't change from previous iteration, stop early
        if messages_sent == 0 and prev_proposals is not None and prev_proposals == proposals:
            break
        prev_proposals = proposals

        # let agents observe the updated inboxes before the next iteration
        for role, agent in manager._agents.items():
            if role not in manager._active_roles:
                continue
            try:
                from .manager_api import build_role_view as manager_build_role_view

                agent.observe(manager_build_role_view(manager, role))
            except Exception:
                # observation failures should not break the manager loop
                continue

    return iterations

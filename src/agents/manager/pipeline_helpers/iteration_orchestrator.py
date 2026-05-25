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

from pathlib import Path
from typing import Any

from captain_sonar.actions import Action, ActionType
from captain_sonar.game_state import GameState
from .manager_helpers import _extract_section
from .manager_helpers import build_turn_start_context_bundle
from .manager_helpers import run_discussion_call
from .manager_helpers import run_strategy_alignment
from .manager_helpers import write_play_context_for_manager
from .manager_helpers import run_turn_start_call
from .manager_helpers import update_memory
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
    update_memory(manager, context_report)
    return context_report


def run_discussion_phase(manager, state: GameState, max_iterations: int = 1, deadline_ms: int | None = None, context_report: dict[str, Any] | None = None) -> None:
    # Run the bounded iteration cycle using the currently active roles.
    return run_iteration_cycle(manager, state, max_iterations=max_iterations, deadline_ms=deadline_ms, context_report=context_report)


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


def _discussion_requests_early_stop(discussion_results: dict[str, Any]) -> bool:
    required_roles = ("CAPTAIN", "FIRST_MATE", "ENGINEER")
    for role_name in required_roles:
        role_result = discussion_results.get(role_name)
        output_path = role_result.get("output_path") if isinstance(role_result, dict) else None
        if not isinstance(output_path, str):
            return False

        try:
            output_text = Path(output_path).read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            return False

        support_stop = _extract_section(output_text, "suport stop").lower()
        if not support_stop.startswith("yes"):
            return False

    return True


def run_iteration_cycle(manager, state: GameState, max_iterations: int = 1, deadline_ms: int | None = None, context_report: dict[str, Any] | None = None):
    resolved_context_report: dict[str, Any] = context_report if context_report is not None else {}

    turn = int(resolved_context_report.get("team_view", {}).get("turn", 0))

    if turn > 0 and turn % 3 == 0:
        alignment_bundle = build_turn_start_context_bundle(manager, resolved_context_report)
        resolved_context_report["strategy_alignment"] = run_strategy_alignment(alignment_bundle)

    for iteration in range(max_iterations):
        # generates the context files for this iteration,
        bundle = build_turn_start_context_bundle(manager, resolved_context_report)
        bundle["discussion_results"] = run_discussion_call(bundle)

        should_stop_after_iteration = False
        discussion_results = bundle.get("discussion_results")
        if isinstance(discussion_results, dict) and discussion_results:
            should_stop_after_iteration = _discussion_requests_early_stop(discussion_results)

        update_memory(manager, resolved_context_report)

        # ── Communications part ───────────────────────────────────────────────
        # Lazy imports to avoid circular import with manager_api.
        from .manager_api import (
            propose_turn_action as _propose,
            omit_turn_action as _omit,
            send_message as _send,
            build_role_view as _role_view,
        )
        from ...base import AgentRole

        # Order: non-Captain roles first so their messages reach the Captain's
        # inbox BEFORE the Captain calls propose_action in this same iteration.
        captain_role: AgentRole | None = None
        non_captain_roles: list[AgentRole] = []
        for role in manager._active_roles:
            if role == AgentRole.CAPTAIN:
                captain_role = role
            else:
                non_captain_roles.append(role)
        ordered_roles = non_captain_roles + ([captain_role] if captain_role is not None else [])

        for role in ordered_roles:
            agent = manager._agents.get(role)
            if agent is None:
                _omit(manager, role)
                continue
            try:
                role_view = _role_view(manager, role)
                proposal = agent.propose_action(role_view)
            except Exception:
                _omit(manager, role)
                continue

            if not isinstance(proposal, dict):
                _omit(manager, role)
                continue

            # Strip and deliver outbound messages BEFORE registering the
            # proposal — later roles in this same iteration will read them.
            messages = list(proposal.pop("messages", None) or [])
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                recipient_str = str(msg.get("recipient", "")).upper()
                recipient_role: AgentRole | None = next(
                    (
                        r for r in manager._active_roles
                        if r.value.upper() == recipient_str or r.name.upper() == recipient_str
                    ),
                    None,
                )
                _send(
                    manager,
                    sender=role,
                    recipient=recipient_role,
                    text=str(msg.get("text", "")),
                    metadata=msg.get("metadata"),
                )

            _propose(manager, role, proposal)
        # ── end communications part ──────────────────────────────────────────

        if should_stop_after_iteration:
            resolved_context_report["early_stop"] = True
            break

  
    return None

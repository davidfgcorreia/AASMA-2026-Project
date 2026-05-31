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
from .manager_helpers import answer_communications
from .manager_helpers import build_turn_start_context_bundle
from .manager_helpers import extract_communications
from .manager_helpers import run_discussion_call
from .manager_helpers import run_strategy_alignment
from .manager_helpers import write_play_context_for_manager
from .manager_helpers import run_turn_start_call
from .manager_helpers import update_memory
# manager_api imports are performed lazily inside functions to avoid
# circular import problems between this module and `manager_api`.



def _run_radio_operator_phase(manager, team_view: dict[str, Any]) -> None:
    """Run the Radio Operator's analysis and deliver its messages to team inboxes.

    Called early in the turn start phase so that the Captain, First Mate, and
    Engineer can see radio operator intel in their inboxes when they run their
    own LLM analysis calls.
    """
    from agents.base import AgentRole
    from ..views import build_role_view as _build_role_view
    from .manager_api import read_inbox as _read_inbox
    from ..models import AgentMessage

    ro_role = AgentRole.RADIO_OPERATOR
    ro_agent = manager._agents.get(ro_role)
    if ro_agent is None or ro_role not in manager._active_roles:
        return

    ro_view = _build_role_view(
        role=ro_role,
        team_view=team_view,
        turn_id=manager._turn_id,
        active_roles=manager._active_roles,
        inbox_reader=lambda r: _read_inbox(manager, r),
    )

    try:
        result = ro_agent.propose_action(ro_view)
    except Exception as exc:
        print(f"[iteration_orchestrator] radio operator propose_action failed: {exc}")
        return

    for msg in (result.get("messages") or []):
        recipient_str = str(msg.get("recipient") or "").upper()
        recipient_role = next(
            (r for r in AgentRole if r.value.upper() == recipient_str or r.name.upper() == recipient_str),
            None,
        )
        if recipient_role is None or recipient_role not in manager._agents:
            continue
        message = AgentMessage(
            sender=ro_role,
            recipient=recipient_role,
            text=msg.get("text", ""),
            metadata=msg.get("metadata") or {},
            turn_id=manager._turn_id,
        )
        manager._inbox[recipient_role].append(message)
        manager._messages_this_turn.append(message)


def run_turn_start_phase(manager, state: GameState) -> dict[str, Any]:
    from .manager_api import begin_turn as manager_begin_turn

    context_report = manager_begin_turn(manager, state)
    write_play_context_for_manager(
        manager,
        context_report["team_view"],
        round_type=context_report["round_type"],
        source=context_report["source"],
    )
    # Run radio operator first so its intel lands in the Captain's inbox
    # before captain/first_mate/engineer run their turn-start analysis.
    _run_radio_operator_phase(manager, context_report["team_view"])
    bundle = build_turn_start_context_bundle(manager, context_report)
    bundle["turn_start_results"] = run_turn_start_call(manager, bundle)
    update_memory(manager, context_report, 0)
    return context_report


def run_discussion_phase(manager, state: GameState, max_iterations: int = 1, context_report: dict[str, Any] | None = None) -> None:
    # Run the bounded iteration cycle using the currently active roles.
    result = run_iteration_cycle(manager, state, max_iterations=max_iterations, context_report=context_report)
    return result


def run_finalization_phase(manager, resolved_context_report: dict[str, Any]) -> list[dict[str, Any]]:
    from .manager_api import choose_turn_actions as manager_choose_turn_actions
    accepted = manager_choose_turn_actions(manager, resolved_context_report)
    return accepted

def run_send_phase(manager, accepted: list[dict[str, Any]], team: str) -> list[Action]:
    SKIP_TYPES = {"OMIT", "END_TURN"}
    actions: list[Action] = []
    print(f"[iteration_orchestrator] run_send_phase accepted={accepted}")
    for proposal in accepted:
        raw_type = proposal.get("type")
        if not isinstance(raw_type, str) or raw_type.strip().upper() in SKIP_TYPES:
            continue
        action = _to_action(team, proposal)
        if action is not None:
            actions.append(action)
    print(f"[iteration_orchestrator] run_send_phase actions={actions}")
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


def run_iteration_cycle(manager, state: GameState, max_iterations: int, context_report: dict[str, Any] | None = None):
    resolved_context_report: dict[str, Any] = context_report if context_report is not None else {}

    turn = int(resolved_context_report.get("team_view", {}).get("turn", 0))

    team = str(resolved_context_report.get("team_view", {}).get("team", "")).lower()
    should_align = False
    if team == "blue":
        should_align = (turn % 6) == 0
    elif team == "red":
        should_align = (turn % 6) == 1

    if should_align:
        alignment_bundle = build_turn_start_context_bundle(manager, resolved_context_report)
        resolved_context_report["strategy_alignment"] = run_strategy_alignment(manager, alignment_bundle)

    for iteration in range(max_iterations):
        # generates the context files for this iteration,
        bundle = build_turn_start_context_bundle(manager, resolved_context_report)
        bundle["discussion_results"] = run_discussion_call(manager, bundle)

        should_stop_after_iteration = False
        discussion_results = bundle.get("discussion_results")
        if isinstance(discussion_results, dict) and discussion_results:
            should_stop_after_iteration = _discussion_requests_early_stop(discussion_results)

        # ── Communications part ───────────────────────────────────────────────
        # Step 1 — BEFORE update_memory: parse discussion outputs for outbound
        # questions, group by recipient, and write per-receiver files into
        # src/agents/manager/communications/. This must happen here because
        # update_memory deletes the outputs/ directory contents.
        team = str(bundle.get("team") or "team")
        comm_turn = int(bundle.get("turn") or 0)
        by_recipient = extract_communications(team, comm_turn)

        update_memory(manager, resolved_context_report, discussion_update=iteration+1)

        # Step 2 — AFTER update_memory: fire a parallel LLM call per recipient
        # whose context is ONLY the per-recipient communications file (no
        # play_context). The answers are appended to each asker's memory.md
        # with attribution and the original question included.
        if by_recipient:
            answer_communications(manager, by_recipient, team, comm_turn)
        # ── end communications part ──────────────────────────────────────────

        if should_stop_after_iteration:
            resolved_context_report["early_stop"] = True
            print(f"Iteration {iteration+1}: Early stop requested by discussion outputs.")
            break

  
    return None

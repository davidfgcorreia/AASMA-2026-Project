from __future__ import annotations

from typing import Any, Iterable, Mapping, List
from dataclasses import asdict

from captain_sonar.actions import Action, ActionType
from captain_sonar.api import get_team_view, snapshot_game_state
from captain_sonar.game_state import GameState

from .manager_helpers import run_captain_finalization_call

from ..models import AgentMessage, GridPos, StartPositionPicker
from ..views import build_role_view as _build_role_view
from ..messaging import send_message as _send_message, broadcast as _broadcast, read_inbox as _read_inbox
from ..startup.start_position import start_position as start_position
from ...common.functions import action_signature

from .iteration_orchestrator import (
    run_turn_start_phase,
    run_discussion_phase,
    run_finalization_phase,
    run_send_phase,
)
from .manager_helpers import write_play_context_for_manager
from .manager_helpers import summarize_memory


def begin_turn(manager, state: GameState, turn_id: int | None = None) -> dict[str, Any]:
    manager._turn_id = state.turn if turn_id is None else turn_id
    context_report = prepare_turn_context(manager, state)
    manager._last_team_view = context_report["team_view"]
    manager._messages_this_turn.clear()
    manager._pair_counts.clear()
    for role in manager._inbox:
        manager._inbox[role].clear()
    if manager._strategy_profile is None and context_report["round_type"] == "startup":
        manager._strategy_profile = None
    return context_report


def prepare_turn_context(manager, state: GameState) -> dict[str, Any]:
    context_state = state
    source = "api"
    if getattr(manager.config, "use_local_files", False):
        sandbox_path = getattr(manager.config, "local_sandbox_path", None)
        from .. import manager as manager_module

        load_sandbox = getattr(manager_module, "load_dev_sandbox", None)
        if callable(load_sandbox):
            sandbox: Any = load_sandbox(sandbox_path)
            # `load_dev_sandbox` in tests may return a simple namespace with
            # different attribute names; accept either `.state` or `.sandbox_state`.
            context_state = getattr(sandbox, "state", getattr(sandbox, "sandbox_state", None))
            team_view = sandbox.team_view(manager.team)
            source = "local"
        else:
            team_view = get_team_view(state, manager.team)
    else:
        team_view = get_team_view(state, manager.team)

    round_type = "startup" if getattr(context_state, "turn", 0) == 0 else "normal"
    manager._last_team_view = team_view
    manager._last_round_type = round_type

    return {
        "team_view": team_view,
        "state": context_state,
        "turn_id": manager._turn_id,
        "round_type": round_type,
        "source": source,
    }



def propose_turn_action(manager, role, action: dict[str, Any]) -> bool:
    if role not in manager._active_roles:
        return False
    normalized_action = dict(action)
    manager._turn_action_proposals[role] = normalized_action
    signature = action_signature(normalized_action)
    voters = manager._turn_action_votes.setdefault(signature, set())
    voters.add(role)
    return True


def omit_turn_action(manager, role) -> bool:
    if role not in manager._active_roles:
        return False
    omitted_action = {"type": "OMIT", "role": role.value, "turn_id": manager._turn_id}
    manager._turn_action_proposals[role] = omitted_action
    return True


def choose_turn_actions(manager) -> list[dict[str, Any]]:
    """Select the final turn action(s).

    Tries ``choose_turn_actions_by_captain`` first.  Falls back to
    ``_choose_turn_actions_by_vote`` if the Captain path returns ``None``
    """
    captain_result = choose_turn_actions_by_captain(manager)
    if captain_result is not None:
        return captain_result
    return _choose_turn_actions_by_vote(manager)

def _choose_turn_actions_by_vote(manager) -> list[dict[str, Any]]:
    """Voting-based fallback: returns majority-winning proposals, or all
    candidates if no majority exists.  Used by ``choose_turn_actions`` when
    the Captain-led path returns ``None``."""
    active_count = max(1, len(manager._active_roles))
    majority = active_count // 2 + 1
    accepted: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []

    votes_by_signature = {signature: len(voters) for signature, voters in manager._turn_action_votes.items()}

    majority_winners: list[dict[str, Any]] = []
    fallback_candidates: list[dict[str, Any]] = []

    for role, proposal in manager._turn_action_proposals.items():
        if proposal.get("type") == "OMIT":
            omitted.append({"role": role.value, **proposal})
            continue
        signature = action_signature(proposal)
        if votes_by_signature.get(signature, 0) >= majority:
            majority_winners.append({"role": role.value, **proposal})
        else:
            fallback_candidates.append({"role": role.value, **proposal})

    # If a majority of active roles explicitly omit, no actions are accepted
    if len(omitted) >= majority:
        accepted = []
    elif majority_winners:
        omitted.extend(fallback_candidates)
        accepted = majority_winners
    else:
        accepted = fallback_candidates

    real_actions = [p for p in accepted if p.get("type") != "END_TURN"]
    if real_actions:
        omitted.extend(p for p in accepted if p.get("type") == "END_TURN")
        accepted = real_actions

    if manager._activation_until_actions_chosen:
        manager._activation_deadline_ms = None
        manager._activation_until_actions_chosen = False
    return accepted

def choose_turn_actions_by_captain(manager) -> list[dict[str, Any]] | None:
    captain_role = next(
        (r for r in manager._active_roles if r.value == "CAPTAIN"),
        None,
    )
    if captain_role is None:
        return None

    proposals_summary: list[dict[str, Any]] = [
        {"role": role.value, **proposal}
        for role, proposal in manager._turn_action_proposals.items()
        if proposal.get("type") != "OMIT"
    ]

    possible: list[dict[str, Any]] = []
    try:
        possible = get_possible_actions(manager, captain_role)
    except Exception:
        pass

    try:
        result = run_captain_finalization_call(
            manager=manager,
            proposals=proposals_summary,
            possible_actions=possible,
        )
    except Exception:
        return None

    if not isinstance(result, dict):
        return None

    chosen = result.get("action")
    if not isinstance(chosen, dict):
        return None

    # Validate action type against the ActionType enum before accepting
    raw_type = chosen.get("type")
    if not isinstance(raw_type, str):
        return None
    try:
        ActionType[raw_type.strip().upper()]
    except KeyError:
        return None

    accepted = [{"role": "CAPTAIN", **chosen}]

    if manager._activation_until_actions_chosen:
        manager._activation_deadline_ms = None
        manager._activation_until_actions_chosen = False

    return accepted

def send_message(manager, sender, recipient, text: str, metadata: dict[str, Any] | None = None) -> bool:
    return _send_message(manager, sender, recipient, text, metadata)


def broadcast(manager, sender, text: str, metadata: dict[str, Any] | None = None) -> bool:
    return _broadcast(manager, sender, text, metadata)


def read_inbox(manager, role) -> list[dict[str, Any]]:
    return _read_inbox(manager, role)


def collect_actions(
    manager,
    state: GameState,
    max_iterations: int = 1,
) -> list[Action]:
    context_report = run_turn_start_phase(manager, state)
    run_discussion_phase(manager, state, max_iterations=max_iterations, context_report=context_report)
    accepted = run_finalization_phase(manager)

    actions = run_send_phase(manager, accepted, manager.team)
    #summarize_memory(manager, state)
    return actions


def execute_turn_actions(manager, state: GameState, intents: list[dict[str, Any]]) -> dict[str, Any]:
    prepared_intents: list[dict[str, Any]] = []
    for intent in intents:
        intent_data = dict(intent)
        intent_data.setdefault("turn_id", manager._turn_id)
        prepared_intents.append(intent_data)

    from ..api_adapter import ManagerGameApiAdapter

    adapter = ManagerGameApiAdapter(team=manager.team, active_roles=set(manager._active_roles), turn_id=manager._turn_id)
    record = adapter.execute_turn_actions(state, prepared_intents)
    record_dict = asdict(record)
    manager._last_execution_record = record_dict
    return record_dict


def get_possible_actions(manager, role, state: GameState | None = None) -> List[dict[str, Any]]:
    if state is not None:
        team_view = get_team_view(state, manager.team)
        role_view = _build_role_view(role=role, team_view=team_view, turn_id=state.turn, active_roles=manager._active_roles, inbox_reader=lambda r: read_inbox(manager, r))
    else:
        role_view = build_role_view(manager, role)
    from captain_sonar.possible_actions import possible_actions_for_role

    return possible_actions_for_role(role.value, role_view)


def team_view(manager) -> dict[str, Any]:
    return dict(manager._last_team_view)


def turn_action_status(manager) -> dict[str, Any]:
    return {
        "turn_id": manager._turn_id,
        "operating_mode": manager.config.operating_mode.value,
        "human_role": manager.config.human_role.value if manager.config.human_role is not None else None,
        "active_roles": [role.value for role in sorted(manager._active_roles, key=lambda value: value.value)],
        "activation_deadline_ms": manager._activation_deadline_ms,
        "activation_until_actions_chosen": manager._activation_until_actions_chosen,
        "proposals": [
            {"role": role.value, **proposal}
            for role, proposal in manager._turn_action_proposals.items()
        ],
        "votes": {
            signature: [role.value for role in sorted(voters, key=lambda value: value.value)]
            for signature, voters in manager._turn_action_votes.items()
        },
    }


def build_role_view(manager, role) -> dict[str, Any]:
    return _build_role_view(
        role=role,
        team_view=manager._last_team_view,
        turn_id=manager._turn_id,
        active_roles=manager._active_roles,
        inbox_reader=lambda r: read_inbox(manager, r),
    )


def get_state_snapshot(manager, state: GameState, turn_id: int | None = None) -> dict[str, Any]:
    return snapshot_game_state(state, turn_id=turn_id)
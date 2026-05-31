from __future__ import annotations

import json
from typing import Any
from dataclasses import asdict

from captain_sonar.actions import Action, ActionType
from captain_sonar.config import GAUGE_MAX_DEFAULT
from captain_sonar.api import get_team_view, snapshot_game_state
from captain_sonar.game_state import GameState

from .manager_helpers import _select_api_key, run_captain_finalization_call

from ..models import AgentMessage
from ..views import build_role_view as _build_role_view
from ..startup.start_position import start_position as start_position
from ...common.functions import action_signature, update_master_memory

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


def choose_turn_actions(manager, resolved_context_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Select the final turn action(s).

    Tries ``choose_turn_actions_by_captain`` first.  Falls back to
    ``_choose_turn_actions_by_vote`` if the Captain path returns ``None``
    """
    print("Choosing turn actions...")
    return choose_turn_actions_by_captain(manager, resolved_context_report)


def choose_turn_actions_by_captain(manager, resolved_context_report: dict[str, Any]) -> list[dict[str, Any]]:
    print ("Attempting to choose turn actions by Captain...")
    captain_role = next(
        (r for r in manager._active_roles if r.value == "CAPTAIN"),
        None,
    )
    possible: list[dict[str, Any]] = []
    try:
        possible = get_possible_actions(manager, captain_role)
    except Exception:
        pass

    invalid_note = ""
    max_attempts = 5
    for _ in range(max_attempts):
        try:
            result = run_captain_finalization_call(
                manager=manager,
                possible_actions=possible,
                resolved_context_report=resolved_context_report,
                extra_context=invalid_note,
            )
        except Exception:
            return []

        if not isinstance(result, dict):
            return []

        actions = result.get("actions")
        if actions is None:
            single = result.get("action")
            actions = [single] if isinstance(single, dict) else None
        if not isinstance(actions, list) or not actions:
            print("[manager_api] captain finalization returned no actions")
            return []

        for action in actions:
            if not isinstance(action, dict):
                print("[manager_api] captain finalization action not object")
                return []
            raw_type = action.get("type")
            if not isinstance(raw_type, str):
                print("[manager_api] captain finalization action missing type")
                return []
            try:
                ActionType[raw_type.strip().upper()]
            except KeyError:
                print(f"[manager_api] captain finalization unsupported type={raw_type!r}")
                return []

        team_view = resolved_context_report.get("team_view", {})
        is_valid, reason = _validate_captain_actions(actions, possible, team_view)
        if is_valid:
            accepted = [{"role": "CAPTAIN", **action} for action in actions]
            print(f"[manager_api] accepted captain actions={accepted}")

            team_name = str(getattr(manager, "team", "team") or "team")
            turn_id = int(getattr(manager, "_turn_id", 0) or 0)
            update_master_memory(
                "##Captain Finalized Actions",
                "\n".join(
                    [
                        f"- team: {team_name}",
                        f"- turn: {turn_id}",
                        f"- actions: {json.dumps(accepted, ensure_ascii=True)}",
                    ]
                ),
            )

            if manager._activation_until_actions_chosen:
                manager._activation_deadline_ms = None
                manager._activation_until_actions_chosen = False

            return accepted

        invalid_note = _format_invalid_action_note(actions, reason)

    return []


def _format_invalid_action_note(actions: list[dict[str, Any]], reason: str) -> str:
    actions_json = json.dumps(actions, ensure_ascii=True)
    return "\n".join(
        [
            "## Actions chosen but invalid",
            f"- actions: {actions_json}",
            f"- reason: {reason}",
            "Choose a different one.",
        ]
    )


def _validate_captain_actions(
    actions: list[dict[str, Any]],
    possible_actions: list[dict[str, Any]],
    team_view: dict[str, Any],
) -> tuple[bool, str]:
    move_action = next((a for a in actions if str(a.get("type", "")).upper() == "MOVE"), None)
    surface_action = next((a for a in actions if str(a.get("type", "")).upper() == "SURFACE"), None)

    if move_action is None and surface_action is None:
        return False, "missing MOVE or SURFACE action"

    move_info: dict[str, Any] | None = None
    if move_action is not None:
        move_ok, move_info, reason = _validate_move_action(move_action, possible_actions, team_view)
        if not move_ok:
            return False, reason

    activation_actions = [
        a
        for a in actions
        if str(a.get("type", "")).upper() not in ("MOVE", "SURFACE")
    ]
    if activation_actions:
        if move_info is None:
            return False, "activation requires a MOVE action"
        if len(activation_actions) > 1:
            return False, "multiple activation actions provided"
        activation_ok, reason = _validate_activation_action(activation_actions[0], move_info, team_view)
        if not activation_ok:
            return False, reason

    return True, ""


def _validate_move_action(
    action: dict[str, Any],
    possible_actions: list[dict[str, Any]],
    team_view: dict[str, Any],
) -> tuple[bool, dict[str, Any] | None, str]:
    payload_val = action.get("payload")
    payload: dict[str, Any] = payload_val if isinstance(payload_val, dict) else {}
    direction = payload.get("direction")
    load_system = payload.get("charge") or payload.get("load_system")
    breakdown_choice_val = payload.get("breakdown_choice")
    breakdown_choice: dict[str, Any] = breakdown_choice_val if isinstance(breakdown_choice_val, dict) else {}
    button_id = breakdown_choice.get("button_id")

    move_entry = next(
        (entry for entry in possible_actions if entry.get("action_kind") == ActionType.MOVE.value),
        None,
    )
    if not isinstance(move_entry, dict):
        return False, None, "MOVE is not allowed in possible actions"

    directions = move_entry.get("directions")
    if not isinstance(directions, list):
        return False, None, "MOVE directions missing in possible actions"

    direction_entry = next(
        (entry for entry in directions if entry.get("direction") == direction),
        None,
    )
    if not isinstance(direction_entry, dict):
        reason = _diagnose_direction_issue(team_view, direction)
        return False, None, reason

    load_systems = direction_entry.get("load_systems")
    if not isinstance(load_systems, list):
        return False, None, "load_systems missing for direction"

    load_entry = next(
        (entry for entry in load_systems if entry.get("load_system") == load_system),
        None,
    )
    if not isinstance(load_entry, dict):
        return False, None, _diagnose_load_system_issue(team_view, direction, load_system)

    engineer_picks = load_entry.get("engineer_picks")
    if not isinstance(engineer_picks, list):
        return False, None, "engineer picks missing for load system"

    engineer_pick = next(
        (entry for entry in engineer_picks if entry.get("button_id") == button_id),
        None,
    )
    if not isinstance(engineer_pick, dict):
        return False, None, _diagnose_button_issue(team_view, direction, button_id)

    possible_activations = engineer_pick.get("possible_activations")
    if not isinstance(possible_activations, list):
        possible_activations = []

    system_hypotheses = direction_entry.get("system_hypotheses")
    if not isinstance(system_hypotheses, list):
        system_hypotheses = []

    return True, {
        "direction": direction,
        "load_system": load_system,
        "button_id": button_id,
        "button_function_type": engineer_pick.get("function_type"),
        "possible_activations": possible_activations,
        "system_hypotheses": system_hypotheses,
    }, ""


def _validate_activation_action(
    action: dict[str, Any],
    move_info: dict[str, Any],
    team_view: dict[str, Any],
) -> tuple[bool, str]:
    action_type = str(action.get("type", "")).lower()
    possible_activations = move_info.get("possible_activations")
    if not isinstance(possible_activations, list):
        possible_activations = []
    allowed_types = {str(value).lower() for value in possible_activations if isinstance(value, str)}

    if action_type not in allowed_types:
        return False, _diagnose_activation_type_issue(action_type, move_info, team_view)

    hypotheses = move_info.get("system_hypotheses")
    if not isinstance(hypotheses, list):
        hypotheses = []
    options: list[dict[str, Any]] = []
    for option in hypotheses:
        if option == "NONE":
            continue
        if isinstance(option, str):
            if option.lower() == action_type:
                options.append({"type": option, "payload": {}})
            continue
        if isinstance(option, dict) and str(option.get("type", "")).lower() == action_type:
            options.append(option)

    action_payload = action.get("payload")
    if not isinstance(action_payload, dict):
        action_payload = {}
    if not options:
        if action_payload:
            return False, "activation payload is not allowed for this action"
        return True, ""

    for option in options:
        option_payload = option.get("payload")
        if not isinstance(option_payload, dict):
            option_payload = {}
        match_ok, reason = _payload_matches(action_payload, option_payload)
        if match_ok:
            return True, ""
        if reason:
            return False, reason

    return False, "activation payload is not valid for the chosen move"


def _payload_matches(action_payload: dict[str, Any], option_payload: dict[str, Any]) -> tuple[bool, str]:
    if not option_payload:
        return (not action_payload, "activation payload is not allowed for this action")

    if "targets" in option_payload:
        allowed = option_payload.get("targets")
        if not isinstance(allowed, list):
            return False, "invalid allowed targets"
        if "target" in action_payload:
            return (action_payload.get("target") in allowed, "target is not in allowed targets")
        targets = action_payload.get("targets")
        if isinstance(targets, list):
            return (all(target in allowed for target in targets), "one or more targets are not allowed")
        return False, "missing target selection"

    if "coordinates" in option_payload:
        allowed = option_payload.get("coordinates")
        if not isinstance(allowed, list):
            return False, "invalid allowed coordinates"
        if "coordinate" in action_payload:
            return (action_payload.get("coordinate") in allowed, "coordinate is not in allowed coordinates")
        coordinates = action_payload.get("coordinates")
        if isinstance(coordinates, list):
            return (all(coord in allowed for coord in coordinates), "one or more coordinates are not allowed")
        return False, "missing coordinate selection"

    if "sectors" in option_payload:
        allowed = option_payload.get("sectors")
        if not isinstance(allowed, list):
            return False, "invalid allowed sectors"
        if "sector" in action_payload:
            return (action_payload.get("sector") in allowed, "sector is not in allowed sectors")
        sectors = action_payload.get("sectors")
        if isinstance(sectors, list):
            return (all(sector in allowed for sector in sectors), "one or more sectors are not allowed")
        return False, "missing sector selection"

    if "target" in option_payload:
        return (
            action_payload.get("target") == option_payload.get("target"),
            "target is not the required value",
        )

    return False, "activation payload does not match allowed options"


def _diagnose_direction_issue(team_view: dict[str, Any], direction: Any) -> str:
    if not isinstance(direction, str) or direction not in {"N", "S", "E", "W"}:
        return f"invalid direction {direction!r}"

    own_sub = team_view.get("own_submarine", {})
    x = own_sub.get("x")
    y = own_sub.get("y")
    if not isinstance(x, int) or not isinstance(y, int):
        return f"invalid direction {direction!r}"

    dx, dy = 0, 0
    if direction == "N":
        dy = -1
    elif direction == "S":
        dy = 1
    elif direction == "E":
        dx = 1
    elif direction == "W":
        dx = -1
    nx, ny = x + dx, y + dy

    map_view = team_view.get("map", {})
    width = map_view.get("width")
    height = map_view.get("height")
    tiles = map_view.get("tiles")
    if isinstance(width, int) and isinstance(height, int):
        if not (0 <= nx < width and 0 <= ny < height):
            return "direction invalid: move goes out of the map"

    if isinstance(tiles, list) and 0 <= ny < len(tiles):
        row = tiles[ny]
        if isinstance(row, list) and 0 <= nx < len(row) and row[nx] == "#":
            return "direction invalid: move goes into an island"

    trajectory = team_view.get("own_trajectory", [])
    if isinstance(trajectory, list):
        for pos in trajectory:
            if isinstance(pos, dict) and pos.get("x") == nx and pos.get("y") == ny:
                return "direction invalid: move crosses previous path"

    if not _has_available_engineer_button(team_view, direction):
        return "direction invalid: no available engineer button for that direction"

    return f"invalid direction {direction!r}"


def _diagnose_load_system_issue(team_view: dict[str, Any], direction: Any, load_system: Any) -> str:
    if not isinstance(load_system, str) or not load_system:
        return "invalid load system: missing charge selection"

    ready = team_view.get("system_utilization", {}).get("ready", {})
    if isinstance(ready, dict) and ready.get(load_system, False):
        return f"invalid load system {load_system!r}: system already fully charged"

    if not _has_available_engineer_button(team_view, direction):
        return "invalid load system: no available engineer button for that direction"

    return f"invalid load system {load_system!r}"


def _diagnose_activation_type_issue(action_type: str, move_info: dict[str, Any], team_view: dict[str, Any]) -> str:
    blocked = _blocked_systems(team_view)
    if action_type in blocked:
        color = _blocked_system_color(action_type)
        blocked_buttons = _blocking_buttons(team_view, action_type)
        blocked_by_dir = _blocking_buttons_by_direction(team_view, action_type)
        blocked_note = f" blocked by buttons={blocked_buttons}" if blocked_buttons else ""
        suggestion = ""
        if blocked_by_dir:
            directions = sorted(blocked_by_dir.keys())
            if len(directions) == 1:
                suggestion = (
                    f"; to use this system, complete the {directions[0]} circuit "
                    "to auto-repair the crossed buttons"
                )
            else:
                suggestion = (
                    f"; crossed buttons span circuits {', '.join(directions)}. "
                    "To use this system now, surface to clear all crossed buttons"
                )
        return (
            f"activation blocked: {action_type} is blocked by crossed {color} buttons{blocked_note}"
            f"{suggestion}"
        )

    ready = team_view.get("system_utilization", {}).get("ready", {})
    if isinstance(ready, dict) and not ready.get(action_type, False):
        gauges = team_view.get("own_gauges", {})
        load_system = move_info.get("load_system")
        if isinstance(gauges, dict) and load_system == action_type:
            current = gauges.get(action_type)
            if isinstance(current, int) and current >= GAUGE_MAX_DEFAULT - 1:
                return "activation allowed only if you charge to full this move"
        return f"activation not possible: {action_type} is not fully charged"

    button_type = move_info.get("button_function_type")
    blocked_by_button = _blocked_by_button_type(button_type)
    if action_type in blocked_by_button:
        selected_button = move_info.get("button_id")
        button_note = f" (selected button {selected_button})" if selected_button else ""
        return (
            "activation blocked by selected engineer button"
            f"{button_note}; choose a different button or clear the circuit"
        )

    return f"activation type {action_type!r} is not allowed for the chosen engineer button"


def _blocked_systems(team_view: dict[str, Any]) -> set[str]:
    board = team_view.get("engineer_board", {})
    buttons_by_direction = board.get("buttons_by_direction", {})
    blocked: set[str] = set()
    if not isinstance(buttons_by_direction, dict):
        return blocked
    for entries in buttons_by_direction.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("crossed", False):
                continue
            function_type = entry.get("function_type")
            blocked.update(_blocked_by_button_type(function_type))
    return blocked


def _blocked_by_button_type(function_type: Any) -> set[str]:
    if function_type == "red":
        return {"torpedo", "mine"}
    if function_type == "yellow":
        return {"sonar", "drone"}
    if function_type == "green":
        return {"silence"}
    return set()


def _blocked_system_color(system_name: str) -> str:
    if system_name in {"torpedo", "mine"}:
        return "red"
    if system_name in {"sonar", "drone"}:
        return "yellow"
    if system_name == "silence":
        return "green"
    return "unknown"


def _blocking_buttons(team_view: dict[str, Any], system_name: str) -> list[str]:
    board = team_view.get("engineer_board", {})
    buttons_by_direction = board.get("buttons_by_direction", {})
    if not isinstance(buttons_by_direction, dict):
        return []
    blocked_buttons: list[str] = []
    for entries in buttons_by_direction.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("crossed", False):
                continue
            function_type = entry.get("function_type")
            if system_name in _blocked_by_button_type(function_type):
                button_id = entry.get("button_id")
                circuit_part = entry.get("circuit_part")
                if isinstance(button_id, str) and button_id:
                    if isinstance(circuit_part, str) and circuit_part:
                        blocked_buttons.append(f"{button_id}({circuit_part})")
                    else:
                        blocked_buttons.append(button_id)
    return blocked_buttons


def _blocking_buttons_by_direction(team_view: dict[str, Any], system_name: str) -> dict[str, list[str]]:
    board = team_view.get("engineer_board", {})
    buttons_by_direction = board.get("buttons_by_direction", {})
    blocked_by_dir: dict[str, list[str]] = {}
    if not isinstance(buttons_by_direction, dict):
        return blocked_by_dir
    for direction, entries in buttons_by_direction.items():
        if not isinstance(direction, str):
            continue
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("crossed", False):
                continue
            function_type = entry.get("function_type")
            if system_name in _blocked_by_button_type(function_type):
                button_id = entry.get("button_id")
                circuit_part = entry.get("circuit_part")
                if isinstance(button_id, str) and button_id:
                    if isinstance(circuit_part, str) and circuit_part:
                        blocked_by_dir.setdefault(direction, []).append(f"{button_id}({circuit_part})")
                    else:
                        blocked_by_dir.setdefault(direction, []).append(button_id)
    return blocked_by_dir


def _has_available_engineer_button(team_view: dict[str, Any], direction: Any) -> bool:
    if not isinstance(direction, str):
        return False
    board = team_view.get("engineer_board", {})
    buttons_by_direction = board.get("buttons_by_direction", {})
    if not isinstance(buttons_by_direction, dict):
        return True
    entries = buttons_by_direction.get(direction, [])
    if not isinstance(entries, list):
        return False
    return any(isinstance(entry, dict) and not entry.get("crossed", False) for entry in entries)


def _diagnose_button_issue(team_view: dict[str, Any], direction: Any, button_id: Any) -> str:
    if not isinstance(button_id, str) or not button_id:
        return "invalid engineer button: missing button_id"

    board = team_view.get("engineer_board", {})
    buttons_by_direction = board.get("buttons_by_direction", {})
    if not isinstance(buttons_by_direction, dict):
        return f"invalid engineer button {button_id!r}"

    found_direction = None
    found_crossed = None
    for dir_key, entries in buttons_by_direction.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("button_id") == button_id:
                found_direction = dir_key
                found_crossed = entry.get("crossed", False)
                break
        if found_direction is not None:
            break

    if found_direction is None:
        return f"invalid engineer button {button_id!r}"
    if found_crossed:
        return f"invalid engineer button {button_id!r}: button already crossed"
    if isinstance(direction, str) and found_direction != direction:
        return (
            f"invalid engineer button {button_id!r}: does not match chosen direction {direction}"
        )

    return f"invalid engineer button {button_id!r}"

def send_message(manager, sender, recipient, text: str, metadata: dict[str, Any] | None = None) -> bool:
    manager._inbox.setdefault(recipient, [])
    message = AgentMessage(
        sender=sender,
        recipient=recipient,
        text=text,
        metadata=metadata or {},
        turn_id=int(getattr(manager, "_turn_id", 0) or 0),
    )
    manager._inbox[recipient].append(message)
    manager._messages_this_turn.append(message)
    return True


def broadcast(manager, sender, text: str, metadata: dict[str, Any] | None = None) -> bool:
    sent = False
    for role in getattr(manager, "_active_roles", []):
        if role == sender:
            continue
        sent = send_message(manager, sender, role, text, metadata) or sent
    return sent


def read_inbox(manager, role) -> list[dict[str, Any]]:
    inbox = getattr(manager, "_inbox", {}).get(role, [])
    return [
        {
            "sender": message.sender.value if hasattr(message.sender, "value") else str(message.sender),
            "recipient": message.recipient.value if hasattr(message.recipient, "value") else str(message.recipient),
            "text": message.text,
            "metadata": dict(message.metadata or {}),
            "turn_id": message.turn_id,
        }
        for message in inbox
    ]


def collect_actions(
    manager,
    state: GameState,
    max_iterations: int = 1,
) -> list[Action]:
    rotation = int(getattr(manager, "_api_rotation_counter", 0) or 0)
    setattr(manager, "_api_rotation_counter", rotation)
    context_report = run_turn_start_phase(manager, state)
    run_discussion_phase(manager, state, max_iterations=max_iterations, context_report=context_report)
    
    approved = False
    attempt = 0
    max_attempts = 5

    while attempt < max_attempts and not approved:
        captain_action = _get_captain_action(manager, context_report)
        if not captain_action:
            return []

        vote_yes = 0
        vote_no = 0

        for role in manager._active_roles:
            if role.value == "CAPTAIN":
                continue
            vote = _ask_vote(manager, role, captain_action, context_report)
            if vote:
                propose_turn_action(manager, role, captain_action)
                vote_yes += 1
            else:
                omit_turn_action(manager, role)
                vote_no += 1

        # Approval check is OUTSIDE the role loop — tallied after all votes
        approved = vote_yes > vote_no
        if approved:
            print(f"[voting] Approved! {vote_yes} yes, {vote_no} no")
        else:
            print(f"[voting] Rejected ({vote_yes}/{vote_no}), captain retrying...")
            context_report["vote_feedback"] = f"Rejected. Need {vote_no + 1} yes votes."
            attempt += 1

    if not approved:
        return []

    accepted = run_finalization_phase(manager, context_report)
    actions = run_send_phase(manager, accepted, manager.team)
    summarize_memory(manager, state)
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

def _get_captain_action(manager, context_report):
    """Get a draft action from the captain for the voting round."""
    from .manager_helpers import run_captain_finalization_call

    captain_role = next(
        (r for r in manager._active_roles if r.value == "CAPTAIN"),
        None,
    )
    possible: list[dict] = []
    try:
        possible = get_possible_actions(manager, captain_role)
    except Exception:
        pass

    try:
        result = run_captain_finalization_call(
            manager,
            possible,
            context_report,
            extra_context=context_report.get("vote_feedback", ""),
        )
    except Exception:
        return None

    actions = result.get("actions") or ([result.get("action")] if result.get("action") else [])
    return actions[0] if actions else None


def _ask_vote(manager, role, action, context):
    import time
    from agents.common.functions import call_agent_activity_with_context
    from pathlib import Path

    # Prompt lives in src/agents/manager/prompts/, one level above pipeline_helpers/
    prompt_path = Path(__file__).parent.parent / "prompts" / "6_action_vote.md"
    prompt_template = prompt_path.read_text(encoding="utf-8")

    turn = (context.get("team_view") or {}).get("turn", 0)
    prompt = prompt_template.format(
        role=role.value,
        action_type=action.get("type", "UNKNOWN"),
        action_payload=json.dumps(action.get("payload", {})),
        turn=turn,
    )

    # Small delay to avoid rate-limit bursts when 3 votes fire back-to-back
    time.sleep(2)

    try:
        result = call_agent_activity_with_context(
            model="gemini-3.1-flash-lite",
            prompt=prompt,
            context="",
            role=role.value,
            api_key=_select_api_key(manager),
            temperature=0.2,
            max_output_tokens=10,
            timeout_seconds=30,
        )
        response = (getattr(result, "text", "") or "").strip().upper()
    except Exception as exc:
        print(f"[voting] {role.value} vote call failed ({exc}), defaulting YES")
        return True

    if not response:
        # Empty response = API rate-limited or transient error; default to YES
        # so a single rate-limited call doesn't block the whole turn.
        print(f"[voting] {role.value} returned empty response, defaulting YES")
        return True

    vote = "YES" in response
    print(f"[voting] {role.value} voted {'YES' if vote else 'NO'} (raw: {response!r})")
    return vote
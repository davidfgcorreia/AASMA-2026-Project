from __future__ import annotations

from typing import Any, Callable

from ..base import AgentRole


def build_role_view(
    *,
    role: AgentRole,
    team_view: dict[str, Any],
    turn_id: int,
    active_roles: set[AgentRole],
    inbox_reader: Callable[[AgentRole], list[dict[str, Any]]],
) -> dict[str, Any]:
    base_view = dict(team_view)
    base_view["role"] = role.value
    base_view["turn_id"] = turn_id
    base_view["active_roles"] = [item.value for item in sorted(active_roles, key=lambda value: value.value)]
    base_view["inbox"] = inbox_reader(role)

    if role == AgentRole.FIRST_MATE:
        return {
            "role": role.value,
            "turn": base_view.get("turn"),
            "team": base_view.get("team"),
            "own_submarine": base_view.get("own_submarine"),
            "own_gauges": base_view.get("own_gauges"),
            "system_utilization": base_view.get("system_utilization"),
            "last_action_system": base_view.get("last_action_system"),
            "events": base_view.get("events", []),
            "inbox": base_view["inbox"],
            "active_roles": base_view["active_roles"],
        }
    if role == AgentRole.ENGINEER:
        return {
            "role": role.value,
            "turn": base_view.get("turn"),
            "team": base_view.get("team"),
            "own_submarine": base_view.get("own_submarine"),
            "engineer_board": base_view.get("engineer_board"),
            "skip_turns": base_view.get("skip_turns"),
            "events": base_view.get("events", []),
            "inbox": base_view["inbox"],
            "active_roles": base_view["active_roles"],
        }
    if role == AgentRole.RADIO_OPERATOR:
        return {
            "role": role.value,
            "turn": base_view.get("turn"),
            "team": base_view.get("team"),
            "map": base_view.get("map"),
            "own_submarine": base_view.get("own_submarine"),
            "radio_operator": base_view.get("radio_operator"),
            "events": base_view.get("events", []),
            "inbox": base_view["inbox"],
            "active_roles": base_view["active_roles"],
        }

    return {
        "role": role.value,
        "turn": base_view.get("turn"),
        "team": base_view.get("team"),
        "map": base_view.get("map"),
        "own_submarine": base_view.get("own_submarine"),
        "own_trajectory": base_view.get("own_trajectory"),
        "own_routes": base_view.get("own_routes"),
        "own_gauges": base_view.get("own_gauges"),
        "system_utilization": base_view.get("system_utilization"),
        "engineer_board": base_view.get("engineer_board"),
        "radio_operator": base_view.get("radio_operator"),
        "events": base_view.get("events", []),
        "inbox": base_view["inbox"],
        "active_roles": base_view["active_roles"],
    }

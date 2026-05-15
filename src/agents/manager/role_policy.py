from __future__ import annotations

from typing import Iterable

from ..base import AgentRole
from .models import AgentManagerConfig, TeamOperatingMode


def validate_mode_config(config: AgentManagerConfig) -> None:
    if config.operating_mode != TeamOperatingMode.THREE_AGENT:
        return

    human_role = config.human_role
    if human_role is not None and human_role != AgentRole.CAPTAIN:
        raise ValueError("three_agent mode only supports captain as the human role")


def derive_active_roles(
    *,
    config: AgentManagerConfig,
    registered_roles: set[AgentRole],
    requested_roles: Iterable[AgentRole] | None,
    strict: bool,
) -> set[AgentRole]:
    if requested_roles is None:
        selected = set(registered_roles)
    else:
        selected = {role for role in requested_roles if role in registered_roles}

    if config.operating_mode == TeamOperatingMode.FULL_TEAM:
        return selected

    # In three-agent mode, the captain is always a human player.
    human_role = config.human_role or AgentRole.CAPTAIN

    eligible = {role for role in registered_roles if role != human_role}
    if strict and eligible != {AgentRole.FIRST_MATE, AgentRole.ENGINEER, AgentRole.RADIO_OPERATOR}:
        raise ValueError(
            "three_agent mode requires exactly these registered AI roles: "
            "first_mate, engineer, radio_operator"
        )
    return eligible

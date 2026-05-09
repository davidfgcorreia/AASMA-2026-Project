from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from captain_sonar.api import get_team_view
from captain_sonar.game_state import GameState

from ..base import AgentBase, AgentRole
from ..common.functions import action_signature, write_turn_actions


@dataclass(slots=True)
class AgentMessage:
    sender: AgentRole
    recipient: AgentRole | None
    turn_id: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentManagerConfig:
    max_messages_per_turn: int = 12
    max_messages_per_pair_per_turn: int = 3
    max_message_length: int = 2_000
    activation_duration_ms: int = 5_000


class TeamAgentManager:
    """Manage the four role agents for one team.

    The manager controls:
    - role registration and activation
    - team-state observation
    - bounded communication between roles
    - action collection
    """

    def __init__(self, team: str, config: AgentManagerConfig | None = None) -> None:
        self.team = team
        self.config = config or AgentManagerConfig()
        self._agents: dict[AgentRole, AgentBase] = {}
        self._active_roles: set[AgentRole] = set()
        self._inbox: dict[AgentRole, list[AgentMessage]] = {role: [] for role in AgentRole}
        self._turn_id: int = 0
        self._messages_this_turn: list[AgentMessage] = []
        self._pair_counts: dict[tuple[AgentRole, AgentRole | None], int] = {}
        self._last_team_view: dict[str, Any] = {}
        self._activation_deadline_ms: int | None = None
        self._activation_until_actions_chosen: bool = False
        self._turn_action_proposals: dict[AgentRole, dict[str, Any]] = {}
        self._turn_action_votes: dict[str, set[AgentRole]] = {}

    @property
    def agents(self) -> Mapping[AgentRole, AgentBase]:
        return dict(self._agents)

    @property
    def active_roles(self) -> set[AgentRole]:
        return set(self._active_roles)

    def register_agent(self, agent: AgentBase, active: bool = True) -> None:
        if agent.team != self.team:
            raise ValueError(f"agent team {agent.team!r} does not match manager team {self.team!r}")
        self._agents[agent.role] = agent
        if active:
            self._active_roles.add(agent.role)

    def set_active_roles(self, roles: Iterable[AgentRole]) -> None:
        self._active_roles = {role for role in roles if role in self._agents}

    def activate_all_registered(self) -> None:
        self._active_roles = set(self._agents)

    def activate_agents(
        self,
        state: GameState,
        roles: Iterable[AgentRole] | None = None,
        duration_ms: int | None = None,
        until_actions_chosen: bool = True,
    ) -> None:
        """Activate a subset of agents for a turn window."""
        selected_roles = set(self._agents) if roles is None else {role for role in roles if role in self._agents}
        self._active_roles = selected_roles
        self.begin_turn(state)
        window_ms = self.config.activation_duration_ms if duration_ms is None else max(0, duration_ms)
        self._activation_deadline_ms = self._now_ms() + window_ms if window_ms > 0 else None
        self._activation_until_actions_chosen = until_actions_chosen
        self._turn_action_proposals.clear()
        self._turn_action_votes.clear()
        self._write_turn_actions_ledger(status="active")

    def is_activation_active(self) -> bool:
        if self._activation_until_actions_chosen:
            return True
        if self._activation_deadline_ms is None:
            return False
        return self._now_ms() <= self._activation_deadline_ms

    def close_activation(self, status: str = "closed") -> None:
        self._activation_deadline_ms = None
        self._activation_until_actions_chosen = False
        self._write_turn_actions_ledger(status=status)

    def begin_turn(self, state: GameState, turn_id: int | None = None) -> None:
        self._turn_id = state.turn if turn_id is None else turn_id
        self._last_team_view = get_team_view(state, self.team)
        self._messages_this_turn.clear()
        self._pair_counts.clear()
        for role in self._inbox:
            self._inbox[role].clear()

    def observe(self, state: GameState) -> None:
        """Push the current team snapshot to all active agents."""
        self.begin_turn(state)
        if self._active_roles and self._activation_deadline_ms is None:
            self._write_turn_actions_ledger(status="active")
        for role, agent in self._agents.items():
            if role not in self._active_roles:
                continue
            agent.observe(self._build_role_view(role))

    def propose_turn_action(self, role: AgentRole, action: dict[str, Any]) -> bool:
        """Record a role's proposed action for the current turn."""
        if role not in self._active_roles:
            return False
        normalized_action = dict(action)
        self._turn_action_proposals[role] = normalized_action
        signature = action_signature(normalized_action)
        voters = self._turn_action_votes.setdefault(signature, set())
        voters.add(role)
        self._write_turn_actions_ledger(status="collecting")
        return True

    def omit_turn_action(self, role: AgentRole) -> bool:
        """Record that a role omitted the current action proposal."""
        if role not in self._active_roles:
            return False
        omitted_action = {"type": "OMIT", "role": role.value, "turn_id": self._turn_id}
        self._turn_action_proposals[role] = omitted_action
        self._write_turn_actions_ledger(status="collecting")
        return True

    def choose_turn_actions(self) -> list[dict[str, Any]]:
        """Choose the accepted turn actions using a majority rule."""
        active_count = max(1, len(self._active_roles))
        majority = active_count // 2 + 1
        accepted: list[dict[str, Any]] = []
        omitted: list[dict[str, Any]] = []

        votes_by_signature = {
            signature: len(voters)
            for signature, voters in self._turn_action_votes.items()
        }

        for role, proposal in self._turn_action_proposals.items():
            if proposal.get("type") == "OMIT":
                omitted.append({"role": role.value, **proposal})
                continue
            signature = action_signature(proposal)
            if votes_by_signature.get(signature, 0) >= majority:
                accepted.append({"role": role.value, **proposal})
            else:
                omitted.append({"role": role.value, **proposal})

        self._write_turn_actions_ledger(status="resolved", accepted=accepted, omitted=omitted)
        if self._activation_until_actions_chosen:
            self.close_activation(status="resolved")
        return accepted

    def turn_action_status(self) -> dict[str, Any]:
        """Return the current turn-action ledger state."""
        return {
            "turn_id": self._turn_id,
            "active_roles": [role.value for role in sorted(self._active_roles, key=lambda value: value.value)],
            "activation_deadline_ms": self._activation_deadline_ms,
            "activation_until_actions_chosen": self._activation_until_actions_chosen,
            "proposals": [
                {"role": role.value, **proposal}
                for role, proposal in self._turn_action_proposals.items()
            ],
            "votes": {
                signature: [role.value for role in sorted(voters, key=lambda value: value.value)]
                for signature, voters in self._turn_action_votes.items()
            },
        }

    def send_message(
        self,
        sender: AgentRole,
        recipient: AgentRole | None,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send a bounded message between roles or broadcast to all active roles."""
        if sender not in self._agents:
            return False
        if len(text) > self.config.max_message_length:
            return False
        if len(self._messages_this_turn) >= self.config.max_messages_per_turn:
            return False

        message = AgentMessage(
            sender=sender,
            recipient=recipient,
            turn_id=self._turn_id,
            text=text,
            metadata=dict(metadata or {}),
        )

        if recipient is None:
            recipients = [role for role in self._active_roles if role != sender]
        else:
            recipients = [recipient] if recipient in self._agents else []

        delivered = False
        for role in recipients:
            pair_key = (sender, role)
            if self._pair_counts.get(pair_key, 0) >= self.config.max_messages_per_pair_per_turn:
                continue
            self._pair_counts[pair_key] = self._pair_counts.get(pair_key, 0) + 1
            self._inbox[role].append(message)
            delivered = True

        if delivered:
            self._messages_this_turn.append(message)
        return delivered

    def broadcast(self, sender: AgentRole, text: str, metadata: dict[str, Any] | None = None) -> bool:
        return self.send_message(sender, None, text, metadata)

    def read_inbox(self, role: AgentRole) -> list[dict[str, Any]]:
        return [self._serialize_message(message) for message in self._inbox.get(role, [])]

    def collect_actions(self, deadline_ms: int) -> dict[AgentRole, dict[str, Any]]:
        actions: dict[AgentRole, dict[str, Any]] = {}
        for role, agent in self._agents.items():
            if role not in self._active_roles:
                continue
            actions[role] = agent.act(deadline_ms)
        return actions

    def team_view(self) -> dict[str, Any]:
        return dict(self._last_team_view)

    def role_view(self, role: AgentRole) -> dict[str, Any]:
        return self._build_role_view(role)

    def _build_role_view(self, role: AgentRole) -> dict[str, Any]:
        base_view = dict(self._last_team_view)
        base_view["role"] = role.value
        base_view["turn_id"] = self._turn_id
        base_view["active_roles"] = [item.value for item in sorted(self._active_roles, key=lambda value: value.value)]
        base_view["inbox"] = self.read_inbox(role)

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
            "own_routes": base_view.get("own_routes"),
            "own_gauges": base_view.get("own_gauges"),
            "system_utilization": base_view.get("system_utilization"),
            "engineer_board": base_view.get("engineer_board"),
            "radio_operator": base_view.get("radio_operator"),
            "events": base_view.get("events", []),
            "inbox": base_view["inbox"],
            "active_roles": base_view["active_roles"],
        }

    def _serialize_message(self, message: AgentMessage) -> dict[str, Any]:
        return {
            "sender": message.sender.value,
            "recipient": message.recipient.value if message.recipient is not None else None,
            "turn_id": message.turn_id,
            "text": message.text,
            "metadata": dict(message.metadata),
        }

    def _now_ms(self) -> int:
        return int(time.monotonic() * 1000)

    def _write_turn_actions_ledger(
        self,
        *,
        status: str,
        accepted: list[dict[str, Any]] | None = None,
        omitted: list[dict[str, Any]] | None = None,
    ) -> None:
        active_roles = [role.value for role in sorted(self._active_roles, key=lambda value: value.value)]
        lines = [
            "# Turn Actions",
            "",
            "This file stores the current turn activation window, action proposals, and the final consensus result.",
            "",
            f"## Current Turn",
            "",
            f"- turn_id: {self._turn_id}",
            f"- status: {status}",
            f"- active_roles: {active_roles}",
            f"- activation_deadline_ms: {self._activation_deadline_ms}",
            f"- action_window: {'open' if self.is_activation_active() else 'closed'}",
            "",
            "## Proposals",
            "",
        ]

        if self._turn_action_proposals:
            for role, proposal in self._turn_action_proposals.items():
                lines.append(f"- {role.value}: {proposal}")
        else:
            lines.append("- none")

        lines.extend([
            "",
            "## Final Decisions",
            "",
        ])

        if accepted:
            for item in accepted:
                lines.append(f"- accepted: {item}")
        else:
            lines.append("- none")

        if omitted:
            lines.append("")
            lines.append("## Omitted")
            lines.append("")
            for item in omitted:
                lines.append(f"- omitted: {item}")

        write_turn_actions("\n".join(lines).rstrip() + "\n", base_path=Path(__file__).resolve().parent.parent / "common")
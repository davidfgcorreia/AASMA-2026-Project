from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterable, Mapping
from typing import List

from captain_sonar.api import get_team_view
from captain_sonar.game_state import GameState
from captain_sonar.map_loader import MapData

from ..common.functions import action_signature
from .api_adapter import ManagerGameApiAdapter
from .pipeline_helpers.iteration_orchestrator import run_iteration_cycle
from .pipeline_helpers.manager_helpers import (
    render_play_context,
    now_ms,
    write_turn_actions_ledger_for_manager,
)
from .pipeline_helpers import manager_api as manager_api

from .views import build_role_view
from .messaging import send_message as _send_message, broadcast as _broadcast, read_inbox as _read_inbox, serialize_message as _serialize_message
from captain_sonar.possible_actions import possible_actions_for_role
from captain_sonar.api import snapshot_game_state

from agents.manager.startup.start_position import start_position
# Local model imports (minimal replacements for removed modules)
from .models import AgentManagerConfig, AgentMessage
from agents.base import AgentBase, AgentRole
# Minimal helper functions to replace removed utilities
def validate_mode_config(config):
    return None

def derive_active_roles(config, registered_roles, requested_roles, strict=False):
    if requested_roles is None:
        return set(registered_roles)
    # intersect requested with registered
    return set(r for r in requested_roles if r in registered_roles)


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
        # Simplify: disable ledger/log writes by default to keep manager lightweight.
        setattr(self.config, "disable_ledgers", True)
        validate_mode_config(self.config)
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
        # removed turn iterations and heavy execution record storage to keep manager lightweight
        self._strategy_profile: dict[str, Any] | None = None
        self._last_round_type: str | None = None
        self._initialize_default_agents()

    @property
    def agents(self) -> Mapping[AgentRole, AgentBase]:
        return dict(self._agents)

    @property
    def active_roles(self) -> set[AgentRole]:
        return set(self._active_roles)

    @property
    def ledger_base_path(self) -> Path:
        """Return the resolved ledger base path used by this manager.

        If a path was configured in `AgentManagerConfig.ledger_base_path`, that
        path is returned; otherwise the default `src/agents/common` directory
        is used.
        """
        ledger_path = getattr(self.config, "ledger_base_path", None)
        if ledger_path is not None:
            base = Path(ledger_path)
        else:
            base = Path(__file__).resolve().parent.parent / "common"
        return base

    @property
    def ledgers_enabled(self) -> bool:
        """Return True if ledgers are enabled for this manager instance."""
        return not getattr(self.config, "disable_ledgers", False)

    def print_ledger_info(self, *, verbose: bool = False) -> str:
        """Return a short summary of ledger configuration for debugging.

        If `verbose` True, include the resolved path and enabled flag.
        """
        base = self.ledger_base_path
        enabled = self.ledgers_enabled
        summary = f"ledger_base_path={base}\nledgers_enabled={enabled}"
        if verbose:
            # include current proposals/votes counts for quick inspection
            summary += f"\nactive_roles={[r.value for r in sorted(self._active_roles, key=lambda v: v.value)]}"
            summary += f"\nproposals={list(self._turn_action_proposals.keys())}"
        return summary

    def register_agent(self, agent: AgentBase, active: bool = True) -> None:
        if agent.team != self.team:
            raise ValueError(f"agent team {agent.team!r} does not match manager team {self.team!r}")
        self._agents[agent.role] = agent
        if active:
            self._active_roles.add(agent.role)
        self._active_roles = derive_active_roles(
            config=self.config,
            registered_roles=set(self._agents),
            requested_roles=self._active_roles,
            strict=False,
        )

    def _initialize_default_agents(self) -> None:
        # Import locally to avoid loading agent modules unless needed.
        from agents.captain.agent import ModelCaptainAgent
        from agents.first_mate.agent import ModelFirstMateAgent
        from agents.engineer.agent import ModelEngineerAgent
        from agents.radio_operator.agent import RadioOperatorAgent

        self.register_agent(ModelCaptainAgent(self.team), active=True)
        self.register_agent(ModelFirstMateAgent(self.team), active=True)
        self.register_agent(ModelEngineerAgent(self.team), active=True)
        self.register_agent(RadioOperatorAgent(self.team), active=True)

    def set_active_roles(self, roles: Iterable[AgentRole]) -> None:
        self._active_roles = derive_active_roles(
            config=self.config,
            registered_roles=set(self._agents),
            requested_roles=roles,
            strict=True,
        )

    def activate_all_registered(self) -> None:
        self._active_roles = derive_active_roles(
            config=self.config,
            registered_roles=set(self._agents),
            requested_roles=None,
            strict=True,
        )


    def choose_start_position(self, map_data: MapData):
        return start_position(map_data)

    def activate_agents(
        self,
        state: GameState,
        roles: Iterable[AgentRole] | None = None,
        duration_ms: int | None = None,
        until_actions_chosen: bool = True,
    ) -> None:
        """Activate a subset of agents for a turn window."""
        self._active_roles = derive_active_roles(
            config=self.config,
            registered_roles=set(self._agents),
            requested_roles=roles,
            strict=True,
        )
        manager_api.begin_turn(self, state)
        window_ms = self.config.activation_duration_ms if duration_ms is None else max(0, duration_ms)
        self._activation_deadline_ms = now_ms() + window_ms if window_ms > 0 else None
        self._activation_until_actions_chosen = until_actions_chosen
        self._turn_action_proposals.clear()
        self._turn_action_votes.clear()
        write_turn_actions_ledger_for_manager(self, status="active")

    def is_activation_active(self) -> bool:
        if self._activation_until_actions_chosen:
            return True
        if self._activation_deadline_ms is None:
            return False
        return now_ms() <= self._activation_deadline_ms

    def close_activation(self, status: str = "closed") -> None:
        self._activation_deadline_ms = None
        self._activation_until_actions_chosen = False
        write_turn_actions_ledger_for_manager(self, status=status)

    def begin_turn(self, state: GameState, turn_id: int | None = None) -> None:
        self._turn_id = state.turn if turn_id is None else turn_id
        # use the manager_api helper to prepare context (keeps implementation centralized)
        context_report = manager_api.prepare_turn_context(self, state)
        self._last_team_view = context_report["team_view"]
        self._messages_this_turn.clear()
        self._pair_counts.clear()
        self._pair_counts.clear()

    def get_strategy_profile(self) -> dict[str, Any] | None:
        """Return the selected strategy profile for this manager, if any."""
        return dict(self._strategy_profile) if self._strategy_profile is not None else None

    def get_role_prompt(self, role: AgentRole) -> str | None:
        """Return the starting prompt for the given role, if available."""
        return None

    def get_state_snapshot(self, state: GameState, turn_id: int | None = None) -> dict[str, Any]:
        """Return a JSON-friendly snapshot of the provided game state."""
        return manager_api.get_state_snapshot(self, state, turn_id=turn_id)

    def run_turn_cycle(self, state: GameState) -> dict[str, Any]:
        """Run one turn through the direct manager action pipeline."""
        actions = manager_api.collect_actions(self, state)
        return {"turn_id": state.turn, "actions": actions}

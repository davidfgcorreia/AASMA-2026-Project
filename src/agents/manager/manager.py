from __future__ import annotations

from dataclasses import asdict
import time
from pathlib import Path
from typing import Any, Iterable, Mapping
from typing import List

from captain_sonar.api import get_team_view
from captain_sonar.game_state import GameState
from captain_sonar.map_loader import MapData

from ..base import AgentBase, AgentRole
from ..common.functions import action_signature
from .api_adapter import ManagerGameApiAdapter
from .iteration_orchestrator import run_iteration_cycle
from .ledger import write_turn_actions_ledger, write_iteration_ledger
from .models import AgentManagerConfig, AgentMessage, ExecutionRecord, GridPos, StartPositionPicker
from .role_policy import derive_active_roles, validate_mode_config
from .views import build_role_view
from .messaging import send_message as _send_message, broadcast as _broadcast, read_inbox as _read_inbox, serialize_message as _serialize_message
from .start_position import default_start_position as _default_start_position, is_legal_start_tile as _is_legal_start_tile
from captain_sonar.possible_actions import possible_actions_for_role
from captain_sonar.api import snapshot_game_state
from .strategy import select_strategy
from .prompt_bootstrap import bootstrap_prompts


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
        self._start_position_picker: StartPositionPicker | None = None
        self._turn_iterations: list[dict[str, Any]] = []
        self._last_execution_record: dict[str, Any] | None = None
        self._strategy_profile: dict[str, Any] | None = None
        self._role_prompts: dict[str, str] = {}

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

    def disable_ledgers(self) -> None:
        """Disable ledger writes at runtime for this manager instance."""
        setattr(self.config, "disable_ledgers", True)

    def enable_ledgers(self) -> None:
        """Enable ledger writes at runtime for this manager instance."""
        setattr(self.config, "disable_ledgers", False)

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

    def set_start_position_picker(self, picker: StartPositionPicker | None) -> None:
        self._start_position_picker = picker

    def choose_start_position(
        self,
        map_data: MapData,
        confirmed: Mapping[str, Any],
    ) -> GridPos | None:
        """Choose a legal start tile for this team through the configured picker."""
        if self._start_position_picker is not None:
            return self._start_position_picker(self.team, map_data, confirmed)

        return _default_start_position(self, map_data, confirmed)

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
        # Ensure we have selected a strategy and bootstrapped starting prompts
        # before the first turn begins.
        if self._strategy_profile is None and getattr(state, "turn", 0) == 0:
            try:
                self._strategy_profile = select_strategy(self.team, state.map_data, self.config.operating_mode, getattr(self.config, "strategy_profile", None))
                role_names = [r.value for r in self._agents]
                self._role_prompts = bootstrap_prompts(self.team, role_names, self._strategy_profile, self.config.operating_mode)
                # deliver starting prompts as an augmented observation for active agents
                for role, agent in self._agents.items():
                    if role not in self._active_roles:
                        continue
                    view = self._build_role_view(role)
                    prompt = self._role_prompts.get(role.value)
                    if prompt:
                        view = dict(view)
                        view["starting_prompt"] = prompt
                    try:
                        agent.observe(view)
                    except Exception:
                        continue
            except Exception:
                # strategy selection must not crash game startup
                self._strategy_profile = None
                self._role_prompts = {}

    def observe(self, state: GameState) -> None:
        """Push the current team snapshot to all active agents."""
        self._active_roles = derive_active_roles(
            config=self.config,
            registered_roles=set(self._agents),
            requested_roles=self._active_roles,
            strict=True,
        )
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
        """Choose the accepted turn actions.

        Primary path: if agents have coordinated across iterations and a
        majority-voted signature exists, only those proposals are accepted.

        Fallback path: when no proposal reaches majority (the common case in
        single-iteration mode where each role self-votes once), every non-OMIT
        proposal is accepted — each role is its own authority for its domain.

        In both cases, END_TURN pass-through proposals (submitted by support
        roles that have no direct game action this turn) are dropped whenever
        at least one real game action is present, to avoid sending spurious
        END_TURN calls to the engine.
        """
        active_count = max(1, len(self._active_roles))
        majority = active_count // 2 + 1
        accepted: list[dict[str, Any]] = []
        omitted: list[dict[str, Any]] = []

        votes_by_signature = {
            signature: len(voters)
            for signature, voters in self._turn_action_votes.items()
        }

        majority_winners: list[dict[str, Any]] = []
        fallback_candidates: list[dict[str, Any]] = []

        for role, proposal in self._turn_action_proposals.items():
            if proposal.get("type") == "OMIT":
                omitted.append({"role": role.value, **proposal})
                continue
            signature = action_signature(proposal)
            if votes_by_signature.get(signature, 0) >= majority:
                majority_winners.append({"role": role.value, **proposal})
            else:
                fallback_candidates.append({"role": role.value, **proposal})

        if majority_winners:
            # Coordinated consensus reached — use majority winners only
            omitted.extend(fallback_candidates)
            accepted = majority_winners
        else:
            # No consensus — accept every role's proposal independently
            accepted = fallback_candidates

        # Drop END_TURN pass-throughs when real game actions are present
        real_actions = [p for p in accepted if p.get("type") != "END_TURN"]
        if real_actions:
            omitted.extend(p for p in accepted if p.get("type") == "END_TURN")
            accepted = real_actions

        self._write_turn_actions_ledger(status="resolved", accepted=accepted, omitted=omitted)
        if self._activation_until_actions_chosen:
            self.close_activation(status="resolved")
        return accepted

    def turn_action_status(self) -> dict[str, Any]:
        """Return the current turn-action ledger state."""
        return {
            "turn_id": self._turn_id,
            "operating_mode": self.config.operating_mode.value,
            "human_role": self.config.human_role.value if self.config.human_role is not None else None,
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
        return _send_message(self, sender, recipient, text, metadata)

    def broadcast(self, sender: AgentRole, text: str, metadata: dict[str, Any] | None = None) -> bool:
        return _broadcast(self, sender, text, metadata)

    def read_inbox(self, role: AgentRole) -> list[dict[str, Any]]:
        return _read_inbox(self, role)

    def collect_actions(self, deadline_ms: int) -> dict[AgentRole, dict[str, Any]]:
        actions: dict[AgentRole, dict[str, Any]] = {}
        for role, agent in self._agents.items():
            if role not in self._active_roles:
                continue
            actions[role] = agent.act(deadline_ms)
        return actions

    def execute_turn_actions(self, state: GameState, intents: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate accepted intents and execute the resulting team actions."""
        prepared_intents: list[dict[str, Any]] = []
        for intent in intents:
            intent_data = dict(intent)
            intent_data.setdefault("turn_id", self._turn_id)
            prepared_intents.append(intent_data)

        adapter = ManagerGameApiAdapter(
            team=self.team,
            active_roles=set(self._active_roles),
            turn_id=self._turn_id,
        )
        record: ExecutionRecord = adapter.execute_turn_actions(state, prepared_intents)
        record_dict = asdict(record)
        self._last_execution_record = record_dict
        return record_dict

    def get_strategy_profile(self) -> dict[str, Any] | None:
        """Return the selected strategy profile for this manager, if any."""
        return dict(self._strategy_profile) if self._strategy_profile is not None else None

    def get_role_prompt(self, role: AgentRole) -> str | None:
        """Return the starting prompt for the given role, if available."""
        return self._role_prompts.get(role.value)

    def get_state_snapshot(self, state: GameState, turn_id: int | None = None) -> dict[str, Any]:
        """Return a JSON-friendly snapshot of the provided game state."""
        return snapshot_game_state(state, turn_id=turn_id)

    def get_possible_actions(self, role: AgentRole, state: GameState | None = None) -> List[dict[str, Any]]:
        """Return the role-specific possible actions using provided state or last observed view.

        If `state` is provided, build a fresh team view from it; otherwise use the
        manager's last cached team view.
        """
        if state is not None:
            team_view = get_team_view(state, self.team)
            role_view = build_role_view(
                role=role,
                team_view=team_view,
                turn_id=state.turn,
                active_roles=self._active_roles,
                inbox_reader=self.read_inbox,
            )
        else:
            role_view = self._build_role_view(role)

        return possible_actions_for_role(role.value, role_view)

    def run_turn_cycle(self, state: GameState, deadline_ms: int | None = None, max_iterations: int = 1) -> dict[str, Any]:
        """Run a bounded proposal/iteration cycle and resolve actions.

        Returns an execution-like report with iteration records and final decisions.
        Agents are expected to implement `propose_action(team_view)` for proposal stage.
        """
        self.begin_turn(state)
        self.observe(state)
        iterations = run_iteration_cycle(self, state, max_iterations=max_iterations, deadline_ms=deadline_ms)

        accepted = self.choose_turn_actions()
        execution = self.execute_turn_actions(state, accepted)
        record = {"turn_id": state.turn, "iterations": iterations, "accepted": accepted, "execution": execution}
        # persist iteration record and store a lightweight record for inspection
        try:
            if self.ledgers_enabled:
                ledger_path = getattr(self.config, "ledger_base_path", None)
                if ledger_path is not None:
                    base = Path(ledger_path)
                else:
                    base = Path(__file__).resolve().parent.parent / "common"
                write_iteration_ledger(
                    base_path=base,
                    turn_id=state.turn,
                    record=record,
                )
        except Exception:
            # ledger failures should not raise during gameplay
            pass
        self._turn_iterations.append(record)
        return record

    def team_view(self) -> dict[str, Any]:
        return dict(self._last_team_view)

    def role_view(self, role: AgentRole) -> dict[str, Any]:
        return self._build_role_view(role)

    def _build_role_view(self, role: AgentRole) -> dict[str, Any]:
        return build_role_view(
            role=role,
            team_view=self._last_team_view,
            turn_id=self._turn_id,
            active_roles=self._active_roles,
            inbox_reader=self.read_inbox,
        )

    def _serialize_message(self, message: AgentMessage) -> dict[str, Any]:
        return _serialize_message(self, message)

    def _now_ms(self) -> int:
        return int(time.monotonic() * 1000)

    def _default_start_position(self, map_data: MapData, confirmed: Mapping[str, Any]) -> GridPos | None:
        preferred = (1, 1) if self.team == "BLUE" else (max(0, map_data.width - 2), max(0, map_data.height - 2))
        if self._is_legal_start_tile(map_data, preferred, confirmed):
            return preferred

        for y in range(map_data.height):
            for x in range(map_data.width):
                candidate = (x, y)
                if self._is_legal_start_tile(map_data, candidate, confirmed):
                    return candidate
        return None

    def _is_legal_start_tile(self, map_data: MapData, candidate: GridPos, confirmed: Mapping[str, Any]) -> bool:
        x, y = candidate
        if not map_data.in_bounds(x, y):
            return False
        if map_data.is_blocked(x, y):
            return False
        return all(getattr(sub, "x", None) != x or getattr(sub, "y", None) != y for sub in confirmed.values())

    def _write_turn_actions_ledger(
        self,
        *,
        status: str,
        accepted: list[dict[str, Any]] | None = None,
        omitted: list[dict[str, Any]] | None = None,
    ) -> None:
        if not self.ledgers_enabled:
            return
        ledger_path = getattr(self.config, "ledger_base_path", None)
        if ledger_path is not None:
            base = Path(ledger_path)
        else:
            base = Path(__file__).resolve().parent.parent / "common"
        write_turn_actions_ledger(
            base_path=base,
            turn_id=self._turn_id,
            status=status,
            active_roles=self._active_roles,
            activation_deadline_ms=self._activation_deadline_ms,
            action_window_open=self.is_activation_active(),
            turn_action_proposals=self._turn_action_proposals,
            accepted=accepted,
            omitted=omitted,
        )
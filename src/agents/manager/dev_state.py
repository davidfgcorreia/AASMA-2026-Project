from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from captain_sonar.game_state import BreakdownState, GameState, MineState, SubmarineState
from captain_sonar.map_loader import load_map
from captain_sonar.radio_operator import RadioOperator
from captain_sonar.api import get_team_view

from agents.base import AgentRole
from agents.manager.models import AgentManagerConfig, TeamOperatingMode


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SANDBOX_PATH = Path(__file__).with_name("dev_sandbox.json")
DEFAULT_MAP_PATH = REPO_ROOT / "assets" / "maps" / "default_map.json"


def _resolve_path(value: str | Path | None, *, sandbox_dir: Path, fallback: Path | None = None) -> Path | None:
    if value is None:
        return fallback

    candidate = Path(value)
    if candidate.is_absolute():
        return candidate

    repo_candidate = REPO_ROOT / candidate
    if repo_candidate.exists():
        return repo_candidate

    sandbox_candidate = sandbox_dir / candidate
    if sandbox_candidate.exists():
        return sandbox_candidate

    return fallback or repo_candidate


def _coerce_role_list(value: Any) -> list[AgentRole] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        return None

    roles: list[AgentRole] = []
    for item in value:
        if not isinstance(item, str):
            continue
        name = item.strip().lower()
        if not name:
            continue
        try:
            roles.append(AgentRole(name))
        except ValueError:
            continue
    return roles or None


def _coerce_point(value: Any) -> tuple[int, int] | None:
    if isinstance(value, dict):
        x = value.get("x")
        y = value.get("y")
        if x is None or y is None:
            return None
        return int(x), int(y)
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return int(value[0]), int(value[1])
    return None


def _coerce_submarines(value: Any) -> dict[str, SubmarineState]:
    submarines: dict[str, SubmarineState] = {}
    if not isinstance(value, dict):
        return submarines

    for team, raw_state in value.items():
        point = _coerce_point(raw_state)
        if point is None:
            continue
        damage = 0
        if isinstance(raw_state, dict) and raw_state.get("damage") is not None:
            damage = int(raw_state.get("damage", 0))
        submarines[str(team)] = SubmarineState(x=point[0], y=point[1], damage=damage)
    return submarines


def _coerce_routes(value: Any) -> dict[str, set[tuple[int, int]]]:
    routes: dict[str, set[tuple[int, int]]] = {}
    if not isinstance(value, dict):
        return routes

    for team, cells in value.items():
        points: set[tuple[int, int]] = set()
        if isinstance(cells, list):
            for cell in cells:
                point = _coerce_point(cell)
                if point is not None:
                    points.add(point)
        routes[str(team)] = points
    return routes


def _coerce_trajectory(value: Any) -> dict[str, list[tuple[int, int]]]:
    trajectory: dict[str, list[tuple[int, int]]] = {}
    if not isinstance(value, dict):
        return trajectory

    for team, cells in value.items():
        points: list[tuple[int, int]] = []
        if isinstance(cells, list):
            for cell in cells:
                point = _coerce_point(cell)
                if point is not None:
                    points.append(point)
        trajectory[str(team)] = points
    return trajectory


def _coerce_mines(value: Any) -> list[MineState]:
    mines: list[MineState] = []
    if not isinstance(value, list):
        return mines

    for item in value:
        if not isinstance(item, dict):
            continue
        point = _coerce_point(item)
        owner = item.get("owner")
        if point is None or not isinstance(owner, str):
            continue
        mines.append(MineState(x=point[0], y=point[1], owner=owner))
    return mines


def _coerce_gauges(value: Any) -> dict[str, dict[str, int]]:
    gauges: dict[str, dict[str, int]] = {}
    if not isinstance(value, dict):
        return gauges

    for team, systems in value.items():
        if not isinstance(systems, dict):
            continue
        gauges[str(team)] = {str(system): int(amount) for system, amount in systems.items()}
    return gauges


def _coerce_last_action_system(value: Any) -> dict[str, bool]:
    result: dict[str, bool] = {}
    if not isinstance(value, dict):
        return result
    for team, flag in value.items():
        result[str(team)] = bool(flag)
    return result


def _coerce_skip_turns(value: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    if not isinstance(value, dict):
        return result
    for team, amount in value.items():
        result[str(team)] = int(amount)
    return result


def _coerce_breakdowns(value: Any) -> dict[str, BreakdownState]:
    breakdowns: dict[str, BreakdownState] = {}
    if not isinstance(value, dict):
        return breakdowns

    for team, raw_breakdown in value.items():
        if not isinstance(raw_breakdown, dict):
            continue
        crossed = raw_breakdown.get("crossed_by_direction")
        if not isinstance(crossed, dict):
            crossed = {}
        breakdown = BreakdownState(
            crossed_by_direction={
                direction: set(str(symbol) for symbol in symbols)
                for direction, symbols in crossed.items()
                if isinstance(symbols, list)
            }
        )
        for direction in breakdown.crossed_by_direction:
            breakdown.crossed_by_direction.setdefault(direction, set())
        if "circuits_status" in raw_breakdown and isinstance(raw_breakdown["circuits_status"], dict):
            setattr(breakdown, "circuits_status", dict(raw_breakdown["circuits_status"]))
        breakdowns[str(team)] = breakdown
    return breakdowns


def _coerce_radio_operators(map_data, value: Any, *, own_team: str | None = None) -> dict[str, RadioOperator]:
    radio_operators: dict[str, RadioOperator] = {}
    if not isinstance(value, dict):
        return radio_operators

    for team, raw_state in value.items():
        radio_operator = RadioOperator(map_data, own_team=str(team))
        if isinstance(raw_state, dict):
            heard_moves = raw_state.get("heard_moves")
            if isinstance(heard_moves, list):
                for move in heard_moves:
                    if isinstance(move, str):
                        radio_operator.add_heard_move(move)
        radio_operators[str(team)] = radio_operator
    if own_team is not None and own_team not in radio_operators:
        radio_operators[own_team] = RadioOperator(map_data, own_team=own_team)
    return radio_operators


def _load_json_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Sandbox file must contain a JSON object: {path}")
    return data


@lru_cache(maxsize=16)
def _load_cached(path_text: str, mtime_ns: int, size: int) -> dict[str, Any]:
    return _load_json_file(Path(path_text))


@dataclass(slots=True)
class DevSnapshotMemory:
    """Lightweight dev helper for snapshot-derived game state access."""
    snapshot: dict[str, Any]
    state: GameState
    map_path: Path

    def team_view(self, team: str) -> dict[str, Any]:
        return get_team_view(self.state, team)

    def submarines(self) -> dict[str, SubmarineState]:
        return dict(self.state.subs)

    def mines(self, team: str | None = None) -> list[MineState]:
        if team is None:
            return list(self.state.mines)
        return [mine for mine in self.state.mines if mine.owner == team]

    def routes(self, team: str | None = None) -> dict[str, set[tuple[int, int]]]:
        if team is None:
            return {name: set(route) for name, route in self.state.routes.items()}
        return {team: set(self.state.routes.get(team, set()))}

    def gauges(self, team: str | None = None) -> dict[str, dict[str, int]] | dict[str, int]:
        if team is None:
            return {name: dict(gauges) for name, gauges in self.state.gauges.items()}
        return dict(self.state.gauges.get(team, {}))

    def events(self) -> list[Any]:
        return list(self.state.events)


@dataclass(slots=True)
class PossibleActionsNavigator:
    """Helper to traverse the possible-actions tree structure."""
    possible_actions: list[dict[str, Any]]

    def action_kinds(self) -> list[str]:
        kinds = []
        for item in self.possible_actions:
            kind = item.get("action_kind") if isinstance(item, dict) else None
            if isinstance(kind, str):
                kinds.append(kind)
        return kinds

    def action(self, kind: str) -> dict[str, Any] | None:
        target = str(kind).upper()
        for item in self.possible_actions:
            if isinstance(item, dict) and str(item.get("action_kind", "")).upper() == target:
                return item
        return None

    def move_directions(self) -> list[str]:
        move = self.action("MOVE")
        if not isinstance(move, dict):
            return []
        directions = move.get("directions")
        if not isinstance(directions, list):
            return []
        return [
            str(entry.get("direction"))
            for entry in directions
            if isinstance(entry, dict) and isinstance(entry.get("direction"), str)
        ]

    def move_direction(self, direction: str) -> dict[str, Any] | None:
        move = self.action("MOVE")
        if not isinstance(move, dict):
            return None
        directions = move.get("directions")
        if not isinstance(directions, list):
            return None
        target = str(direction).upper()
        for entry in directions:
            if isinstance(entry, dict) and str(entry.get("direction", "")).upper() == target:
                return entry
        return None

    def system_hypotheses(self, direction: str) -> list[Any]:
        entry = self.move_direction(direction)
        if not isinstance(entry, dict):
            return []
        values = entry.get("system_hypotheses")
        return list(values) if isinstance(values, list) else []

    def load_systems(self, direction: str) -> list[str]:
        entry = self.move_direction(direction)
        if not isinstance(entry, dict):
            return []
        branches = entry.get("load_systems")
        if not isinstance(branches, list):
            return []
        return [
            str(branch.get("load_system"))
            for branch in branches
            if isinstance(branch, dict) and isinstance(branch.get("load_system"), str)
        ]

    def load_system(self, direction: str, system: str) -> dict[str, Any] | None:
        entry = self.move_direction(direction)
        if not isinstance(entry, dict):
            return None
        branches = entry.get("load_systems")
        if not isinstance(branches, list):
            return None
        target = str(system)
        for branch in branches:
            if isinstance(branch, dict) and str(branch.get("load_system", "")) == target:
                return branch
        return None

    def engineer_picks(self, direction: str, system: str) -> list[dict[str, Any]]:
        branch = self.load_system(direction, system)
        if not isinstance(branch, dict):
            return []
        picks = branch.get("engineer_picks")
        return [pick for pick in picks if isinstance(pick, dict)] if isinstance(picks, list) else []


def load_snapshot_memory(
    snapshot: Mapping[str, Any],
    *,
    map_path: str | Path | None = None,
    sandbox_dir: Path | None = None,
    fallback_team: str = "BLUE",
) -> DevSnapshotMemory:
    state = load_game_state_from_snapshot(
        snapshot,
        map_path=map_path,
        sandbox_dir=sandbox_dir,
        fallback_team=fallback_team,
    )
    resolved_map = _resolve_path(map_path, sandbox_dir=sandbox_dir or REPO_ROOT, fallback=DEFAULT_MAP_PATH) or DEFAULT_MAP_PATH
    return DevSnapshotMemory(snapshot=dict(snapshot), state=state, map_path=resolved_map)


def load_snapshot_file(
    path: str | Path,
    *,
    map_path: str | Path | None = None,
    sandbox_dir: Path | None = None,
    fallback_team: str = "BLUE",
) -> DevSnapshotMemory:
    snapshot_path = Path(path)
    raw = _load_json_file(snapshot_path)
    if not isinstance(raw, dict):
        raise ValueError("snapshot must contain a JSON object")
    return load_snapshot_memory(raw, map_path=map_path, sandbox_dir=sandbox_dir or snapshot_path.parent, fallback_team=fallback_team)


def load_possible_actions_from_payload(payload: Mapping[str, Any]) -> PossibleActionsNavigator:
    possible_actions = payload.get("possible_actions")
    if not isinstance(possible_actions, list):
        possible_actions = []
    return PossibleActionsNavigator([item for item in possible_actions if isinstance(item, dict)])


def load_possible_actions_file(path: str | Path) -> PossibleActionsNavigator:
    payload = _load_json_file(Path(path))
    if not isinstance(payload, dict):
        payload = {}
    return load_possible_actions_from_payload(payload)


@dataclass(slots=True)
class ManagerDevSandbox:
    path: Path
    raw: dict[str, Any]
    fingerprint: tuple[int, int]

    @property
    def sandbox_dir(self) -> Path:
        return self.path.parent

    @property
    def team(self) -> str:
        value = self.raw.get("team", "BLUE")
        return str(value)

    @property
    def manager_section(self) -> dict[str, Any]:
        value = self.raw.get("manager")
        return value if isinstance(value, dict) else {}

    @property
    def turn_section(self) -> dict[str, Any]:
        value = self.raw.get("turn")
        return value if isinstance(value, dict) else {}

    @property
    def state_section(self) -> dict[str, Any]:
        value = self.raw.get("state")
        return value if isinstance(value, dict) else {}

    def active_roles(self) -> list[AgentRole] | None:
        return _coerce_role_list(self.turn_section.get("active_roles") or self.raw.get("active_roles"))

    def model_captain_enabled(self) -> bool:
        value = self.turn_section.get("model_captain")
        if value is None:
            value = self.raw.get("model_captain")
        return bool(value)

    def output_path(self) -> Path | None:
        raw_output = self.turn_section.get("output_file") or self.raw.get("output_file")
        return _resolve_path(raw_output, sandbox_dir=self.sandbox_dir, fallback=None)

    def map_path(self, fallback: Path | None = None) -> Path:
        raw_map = self.state_section.get("map") or self.state_section.get("map_path") or self.raw.get("map") or self.raw.get("map_path")
        resolved = _resolve_path(raw_map, sandbox_dir=self.sandbox_dir, fallback=fallback or DEFAULT_MAP_PATH)
        return resolved or DEFAULT_MAP_PATH

    def build_manager_config(self) -> AgentManagerConfig:
        manager = self.manager_section
        operating_mode_value = manager.get("mode") or manager.get("operating_mode") or TeamOperatingMode.FULL_TEAM.value
        human_role_value = manager.get("human_role")
        ledger_value = manager.get("ledger_base_path") or manager.get("ledger_dir")
        return AgentManagerConfig(
            max_messages_per_turn=int(manager.get("max_messages_per_turn", 12)),
            max_messages_per_pair_per_turn=int(manager.get("max_messages_per_pair_per_turn", 3)),
            max_message_length=int(manager.get("max_message_length", 2_000)),
            activation_duration_ms=int(manager.get("activation_duration_ms", 5_000)),
            operating_mode=TeamOperatingMode(str(operating_mode_value)),
            human_role=AgentRole(str(human_role_value)) if human_role_value else None,
            ledger_base_path=_resolve_path(ledger_value, sandbox_dir=self.sandbox_dir, fallback=None),
            disable_ledgers=bool(manager.get("disable_ledgers", False)),
        )

    def build_game_state(self, *, map_override: str | Path | None = None) -> GameState:
        state = self.state_section
        map_path = _resolve_path(map_override, sandbox_dir=self.sandbox_dir, fallback=self.map_path()) or self.map_path()
        return load_game_state_from_snapshot(state, map_path=map_path, sandbox_dir=self.sandbox_dir, fallback_team=self.team)


def load_dev_sandbox(path: str | Path | None = None) -> ManagerDevSandbox:
    sandbox_path = Path(path) if path is not None else DEFAULT_SANDBOX_PATH
    if not sandbox_path.is_absolute():
        sandbox_path = (REPO_ROOT / sandbox_path).resolve()
    if not sandbox_path.exists():
        raise FileNotFoundError(f"Dev sandbox not found: {sandbox_path}")

    stat = sandbox_path.stat()
    raw = _load_cached(str(sandbox_path), stat.st_mtime_ns, stat.st_size)
    return ManagerDevSandbox(path=sandbox_path, raw=raw, fingerprint=(stat.st_mtime_ns, stat.st_size))


def load_game_state_from_snapshot(
    snapshot: Mapping[str, Any],
    *,
    map_path: str | Path | None = None,
    sandbox_dir: Path | None = None,
    fallback_team: str = "BLUE",
) -> GameState:
    root = sandbox_dir or REPO_ROOT
    resolved_map = _resolve_path(map_path, sandbox_dir=root, fallback=DEFAULT_MAP_PATH) or DEFAULT_MAP_PATH
    map_data = load_map(str(resolved_map))

    submarines = _coerce_submarines(snapshot.get("submarines"))
    if not submarines:
        submarines = {
            fallback_team: SubmarineState(x=1, y=1),
            "RED": SubmarineState(x=0, y=0),
        }

    state = GameState(map_data=map_data, subs=submarines)
    state.turn = int(snapshot.get("turn", state.turn))
    state.game_over = bool(snapshot.get("game_over", state.game_over))
    if snapshot.get("winner") is not None:
        state.winner = str(snapshot.get("winner"))

    routes = _coerce_routes(snapshot.get("routes"))
    if routes:
        state.routes = routes

    trajectory = _coerce_trajectory(snapshot.get("trajectory"))
    if trajectory:
        state.trajectory = trajectory

    mines = _coerce_mines(snapshot.get("mines"))
    if mines:
        state.mines = mines

    gauges = _coerce_gauges(snapshot.get("gauges"))
    if gauges:
        state.gauges = gauges

    last_action_system = _coerce_last_action_system(snapshot.get("last_action_system"))
    if last_action_system:
        state.last_action_system = last_action_system

    skip_turns = _coerce_skip_turns(snapshot.get("skip_turns"))
    if skip_turns:
        state.skip_turns = skip_turns

    breakdowns = _coerce_breakdowns(snapshot.get("breakdowns"))
    if breakdowns:
        state.breakdowns = breakdowns

    radio_operators = _coerce_radio_operators(map_data, snapshot.get("radio_operators"), own_team=fallback_team)
    if radio_operators:
        state.radio_operators = radio_operators

    events = snapshot.get("events")
    if isinstance(events, list):
        state.events = list(events)

    return state

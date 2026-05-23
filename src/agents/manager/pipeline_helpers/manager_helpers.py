from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from captain_sonar.game_state import GameState
from agents.base import AgentRole
from agents.common.functions import read_common_context, read_master_memory, read_role_memory


def _render_trajectory_map(team_view: dict[str, Any]) -> str:
    if not isinstance(team_view, dict):
        team_view = {}
    map_state = team_view.get("map") or {}
    tiles = map_state.get("tiles") or []
    width = int(map_state.get("width") or 0)
    height = int(map_state.get("height") or 0)

    if not tiles or width <= 0 or height <= 0:
        return "map: unknown"

    # Start from the game map and overlay route/current markers:
    # '-' for visited route cells, 'O' for the current submarine position.
    grid = [[str(cell) for cell in row] for row in tiles]
    own_routes = team_view.get("own_routes") or []
    own_sub = team_view.get("own_submarine") or {}
    current_x = own_sub.get("x")
    current_y = own_sub.get("y")

    for route in own_routes:
        if not isinstance(route, dict):
            continue
        rx = route.get("x")
        ry = route.get("y")
        if not isinstance(rx, int) or not isinstance(ry, int):
            continue
        if 0 <= ry < height and 0 <= rx < width:
            if rx != current_x or ry != current_y:
                grid[ry][rx] = "-"

    if isinstance(current_x, int) and isinstance(current_y, int):
        if 0 <= current_y < height and 0 <= current_x < width:
            grid[current_y][current_x] = "O"

    lines = [f"map: {width}x{height}"]
    lines.extend("".join(row) for row in grid)
    return "\n".join(lines)


def _render_belief_map(team_view: dict[str, Any]) -> str:
    if not isinstance(team_view, dict):
        team_view = {}
    radio = team_view.get("radio_operator") or {}
    belief = radio.get("belief") if isinstance(radio, dict) else None
    if not isinstance(belief, list) or not belief:
        return "(no belief map)"

    rows: list[str] = []
    for row in belief:
        if not isinstance(row, list):
            continue
        rendered_cells: list[str] = []
        for value in row:
            try:
                rendered_cells.append(f"{float(value):.2f}")
            except (TypeError, ValueError):
                rendered_cells.append("0.00")
        rows.append(" ".join(rendered_cells))

    return "\n".join(rows) if rows else "(no belief map)"


def _render_engineer_board(team_view: dict[str, Any]) -> list[str]:
    if not isinstance(team_view, dict):
        team_view = {}
    board = team_view.get("engineer_board") or {}
    crossed = board.get("crossed_by_direction") if isinstance(board, dict) else None
    if not isinstance(crossed, dict):
        return ["- W: (none)", "- N: (none)", "- S: (none)", "- E: (none)"]

    lines: list[str] = []
    for direction in ("W", "N", "S", "E"):
        symbols = crossed.get(direction, [])
        if isinstance(symbols, list) and symbols:
            lines.append(f"- {direction}: {', '.join(str(item) for item in symbols)}")
        else:
            lines.append(f"- {direction}: (none)")
    return lines


def render_play_context(team_view: dict[str, Any], *, round_type: str, source: str) -> str:
    if not isinstance(team_view, dict):
        team_view = {}

    enemy_last_play = team_view.get("enemy_last_play")
    if isinstance(enemy_last_play, dict) and enemy_last_play.get("activated_system") is None:
        enemy_last_play = {key: value for key, value in enemy_last_play.items() if key != "activated_system"}

    radio_val = team_view.get("radio_operator")
    radio_operator = radio_val if isinstance(radio_val, dict) else {}
    trimmed_radio = {
        "heard_moves": radio_operator.get("heard_moves", []),
        "most_likely_sector": radio_operator.get("most_likely_sector"),
    }

    payload = {
        "source": source,
        "round_type": round_type,
        "team": team_view.get("team"),
        "turn": team_view.get("turn"),
        "own_submarine": team_view.get("own_submarine"),
        "own_gauges": team_view.get("own_gauges"),
        "engineer_board": team_view.get("engineer_board"),
        "radio_operator": trimmed_radio,
        "enemy_last_play": enemy_last_play,
    }
    return "\n".join([
        "# Play Context",
        "",
        "## Trajectory Map",
        "```",
        _render_trajectory_map(team_view),
        "```",
        "",
        "## Belief Map",
        "```",
        _render_belief_map(team_view),
        "```",
        "",
        "## Engineer Board (Crossed)",
        *_render_engineer_board(team_view),
        "",
        f"- team: {team_view.get('team')}",
        f"- turn: {team_view.get('turn')}",
        f"- round_type: {round_type}",
        f"- source: {source}",
        f"- enemy_last_play: {payload['enemy_last_play']}",
        "",
        "```json",
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
        "```",
        "",
    ])


def build_turn_start_context_bundle(manager, context_report: dict[str, Any]) -> dict[str, Any]:
    """Formulate the files used at turn start for prompts and shared context."""
    team_view = context_report.get("team_view", {})
    round_type = str(context_report.get("round_type", "normal"))
    source = str(context_report.get("source", "api"))
    # Prefer reading an existing play_context file (single shared source).
    play_context_path = Path(__file__).resolve().parents[2] / "common" / "play_context.md"
    if play_context_path.exists():
        play_context = play_context_path.read_text(encoding="utf-8")
    else:
        play_context = render_play_context(team_view, round_type=round_type, source=source)
    common_context = read_common_context()
    master_memory = read_master_memory()

    role_files: dict[str, dict[str, str]] = {}
    for role in sorted(getattr(manager, "_active_roles", []), key=lambda value: value.value):
        role_files[role.value] = {
            "context": read_role_memory(role),
            "strategy": (Path(__file__).resolve().parents[2] / role.name.lower() / "strategy.md").read_text(encoding="utf-8")
            if (Path(__file__).resolve().parents[2] / role.name.lower() / "strategy.md").exists()
            else "",
            "memory": (Path(__file__).resolve().parents[2] / role.name.lower() / "memory.md").read_text(encoding="utf-8")
            if (Path(__file__).resolve().parents[2] / role.name.lower() / "memory.md").exists()
            else "",
            "prompt": (Path(__file__).resolve().parents[2] / role.name.lower() / "prompt.md").read_text(encoding="utf-8")
            if (Path(__file__).resolve().parents[2] / role.name.lower() / "prompt.md").exists()
            else "",
        }

    # Determine team/turn: prefer explicit team_view, otherwise try to parse from the
    # shared play_context file (either the header `- team:` line or the JSON block).
    team = None
    turn = None
    if isinstance(team_view, dict):
        team = team_view.get("team")
        turn = team_view.get("turn")

    if not team or not turn:
        # try to find a header line like '- team: NAME'
        import re

        m = re.search(r"^-\s*team:\s*(\S+)", play_context, flags=re.MULTILINE)
        if m and not team:
            team = m.group(1)
        # try to parse embedded JSON block
        if (not team or not turn) and "```json" in play_context:
            start = play_context.find("```json")
            end = play_context.find("```", start + 1)
            if start != -1 and end != -1:
                json_block = play_context[start + len("```json"):end].strip()
                try:
                    obj = json.loads(json_block)
                    if not team:
                        team = obj.get("team")
                    if not turn:
                        turn = obj.get("turn")
                except Exception:
                    pass

    if not team:
        team = "team"
    if not isinstance(turn, int):
        try:
            turn = int(turn)
        except Exception:
            turn = 0

    bundle = {
        "team": team,
        "turn": turn,
        "round_type": round_type,
        "source": source,
        "common_context": common_context,
        "master_memory": master_memory,
        "play_context": play_context,
        "roles": role_files,
    }

    bundle_path = Path(__file__).resolve().parents[2] / "common" / "turn_start_context.md"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text(
        "\n".join([
            "# Turn Start Context",
            "",
            f"- team: {bundle['team']}",
            f"- turn: {bundle['turn']}",
            f"- round_type: {bundle['round_type']}",
            f"- source: {bundle['source']}",
            "",
            "## Shared Context",
            "```",
            common_context,
            "```",
            "",
            "## Master Memory",
            "```",
            master_memory,
            "```",
            "",
            "## Play Context",
            "```",
            play_context,
            "```",
            "",
            "## Role Files",
            *[
                f"### {role_name}\n```\ncontext.md:\n{files['context']}\n\nmemory.md:\n{files['memory']}\n\nprompt.md:\n{files['prompt']}\n```"
                for role_name, files in role_files.items()
            ],
            "",
        ]),
        encoding="utf-8",
    )
    bundle["bundle_path"] = str(bundle_path)
    # Also write per-role context files into the manager `contexts` folder.
    contexts_dir = Path(__file__).resolve().parents[1] / "contexts"
    contexts_dir.mkdir(parents=True, exist_ok=True)
    team_name = str(bundle.get("team") or "team").replace(" ", "_").lower()
    for role_name, files in role_files.items():
        safe_role = str(role_name).replace(" ", "_").lower()
        file_name = f"{safe_role}_{team_name}.md"
        file_path = contexts_dir / file_name
        parts = [
            f"# Turn Context for {role_name} (team: {bundle.get('team')})",
            "",
            "## Context",
            "```",
            files.get("context", ""),
            "```",
            "",
            "## Strategy",
            "```",
            files.get("strategy", ""),
            "```",
            "",
            "## Memory",
            "```",
            files.get("memory", ""),
            "```",
            "",
            "## Master Memory",
            "```",
            master_memory,
            "```",
            "",
            "## Play Context",
            "```",
            play_context,
            "```",
            "",
        ]
        file_path.write_text("\n".join(parts), encoding="utf-8")

    return bundle


def write_play_context_for_manager(manager, team_view: dict[str, Any], *, round_type: str, source: str) -> str:
    play_context_path = Path(__file__).resolve().parents[2] / "common" / "play_context.md"
    play_context_path.parent.mkdir(parents=True, exist_ok=True)
    play_context_path.write_text(render_play_context(team_view, round_type=round_type, source=source), encoding="utf-8")
    return str(play_context_path)


def now_ms() -> int:
    return int(time.monotonic() * 1000)


def write_turn_actions_ledger_for_manager(
    manager,
    *,
    status: str,
    accepted: list[dict[str, Any]] | None = None,
    omitted: list[dict[str, Any]] | None = None,
) -> None:
    return

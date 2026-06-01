from __future__ import annotations



import json

import time

import os

import re

import shutil

from concurrent.futures import ThreadPoolExecutor, as_completed

from pathlib import Path

from typing import Any



from captain_sonar.game_state import GameState

from agents.base import AgentRole

from agents.common.functions import (

    call_agent_activity_with_context,

    read_common_context,

    read_master_memory,

    read_role_memory,

    update_master_memory,

)

from agents.common.gemini import load_env_file





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





def _load_rotating_keys() -> list[str]:

    keys: list[str] = []

    index = 1

    while True:

        value = os.getenv(f"GEMINI_API_KEY{index}")

        if not value:

            break

        keys.append(value)

        index += 1

    return keys





def _select_api_key(manager) -> str | None:

    load_env_file()

    keys = _load_rotating_keys()

    if not keys:

        return None

    counter = int(getattr(manager, "_api_rotation_counter", 0) or 0)

    key = keys[counter % len(keys)]

    setattr(manager, "_api_rotation_counter", counter + 1)

    return key





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

        "own_gauges (X/4)" : team_view.get("own_gauges"),

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

    play_context = play_context_path.read_text(encoding="utf-8")

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

            turn_value = 0 if turn is None else turn

            turn = int(turn_value)

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



    contexts_dir = Path(__file__).resolve().parents[1] / "contexts"

    contexts_dir.mkdir(parents=True, exist_ok=True)

    team_name = str(bundle.get("team") or "team").replace(" ", "_").lower()

    for role_name, files in role_files.items():

        if role_name == AgentRole.RADIO_OPERATOR.value:

            continue

        safe_role = str(role_name).replace(" ", "_").lower()

        file_name = f"{safe_role}_{team_name}.md"

        file_path = contexts_dir / file_name

        parts = [

            f"# Turn Context for {role_name} (team: {bundle.get('team')})",

            "",

            "# Context",

            files.get("context", ""),

            "",

            "# Strategy",

            files.get("strategy", ""),

            "",

            "# Memory",

            files.get("memory", ""),

            "",

            "# Master Memory",

            master_memory,

            "",

            "# Play Context",

            play_context,

            "",

        ]

        file_path.write_text("\n".join(parts), encoding="utf-8")



    return bundle





def write_play_context_for_manager(manager, team_view: dict[str, Any], *, round_type: str, source: str) -> str:

    play_context_path = Path(__file__).resolve().parents[2] / "common" / "play_context.md"

    play_context_path.parent.mkdir(parents=True, exist_ok=True)

    play_context_path.write_text(render_play_context(team_view, round_type=round_type, source=source), encoding="utf-8")

    return str(play_context_path)




def _append_ro_intel_to_play_context(messages: list[dict[str, Any]]) -> None:
    # Append Radio Operator intel as a section in play_context.md.
    # Called after write_play_context_for_manager so all agents see the RO intel
    # when build_turn_start_context_bundle reads play_context.md.
    captain_msg = next(
        (m for m in (messages or []) if str(m.get("recipient", "")).upper() == "CAPTAIN"),
        None,
    )
    if captain_msg is None:
        return
    play_context_path = Path(__file__).resolve().parents[2] / "common" / "play_context.md"
    existing = play_context_path.read_text(encoding="utf-8") if play_context_path.exists() else ""
    section = "\n## Radio Operator Intel\n\n" + captain_msg["text"].strip() + "\n"
    play_context_path.write_text(existing.rstrip() + "\n" + section, encoding="utf-8")


def reset_agent_state() -> None:
    # Reset all agent memory files and scratch directories for a fresh game.
    base = Path(__file__).resolve().parents[2]  # src/agents/

    role_headers: dict[str, str] = {
        "captain": "# Captain Role Context\n",
        "first_mate": "# First Mate Role Context\n",
        "engineer": "# Engineer Role Context\n",
        "radio_operator": (
            "# Radio Operator Agent Memory\n\n"
            "- Primary responsibility: hidden-position reasoning and enemy tracking.\n"
            "- Reads the radio operator snapshot and belief data from the manager.\n"
            "- Shares likely positions, sectors, and sensor interpretation with the team.\n"
        ),
    }
    for role_name, header in role_headers.items():
        memory_path = base / role_name / "memory.md"
        if memory_path.exists():
            memory_path.write_text(header, encoding="utf-8")

    master_path = base / "common" / "master_memory.md"
    if master_path.exists():
        master_path.write_text("# Master Team Memory\n", encoding="utf-8")

    manager_base = base / "manager"
    for scratch_dir in ("outputs", "communications"):
        d = manager_base / scratch_dir
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)

    print("[agent] memory reset — ready for new game")


def _run_turn_start_role(

    manager,

    role_name: str,

    prompt_path: Path,

    team: str,

    turn: int,

    outputs_dir: Path,

) -> dict[str, Any]:

    prompt = prompt_path.read_text(encoding="utf-8").strip()

    team_name = str(team or "team").replace(" ", "_").lower()

    role_slug = str(role_name).replace(" ", "_").lower()

    context_path = Path(__file__).resolve().parents[1] / "contexts" / f"{role_slug}_{team_name}.md"

    context_text = context_path.read_text(encoding="utf-8")



    model_name = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"

    result = call_agent_activity_with_context(

        model=model_name,

        prompt=prompt,

        context=context_text,

        role=role_name,

        api_key=_select_api_key(manager),

        temperature=0.7,

        max_output_tokens=512,

        timeout_seconds=45.0,

    )

    output_text = getattr(result, "text", "") or ""

    output_path = outputs_dir / f"{role_slug}_{team_name}_turn_{turn}.md"

    output_path.write_text(output_text, encoding="utf-8")

    return {

        "output_path": str(output_path),

        "output": output_text,

    }





def _extract_section(text: str, header: str) -> str:

    pattern = rf"^## {re.escape(header)}\s*$([\s\S]*?)(?=^##\s+|\Z)"

    match = re.search(pattern, text, flags=re.MULTILINE)

    if not match:

        return ""

    return match.group(1).strip()





def _role_from_output_filename(file_name: str) -> AgentRole | None:

    role_slugs = {

        role.name.lower(): role

        for role in AgentRole

        if role != AgentRole.RADIO_OPERATOR

    }

    for slug, role in sorted(role_slugs.items(), key=lambda item: len(item[0]), reverse=True):

        if file_name.startswith(f"{slug}_"):

            return role

    return None





def _turn_from_output_filename(file_name: str) -> str:

    match = re.search(r"_turn_(\d+)\.md$", file_name)

    return match.group(1) if match else "unknown"





def _build_reasoning_append(role: AgentRole | None, turn_label: str, content: str, discussion_update: int) -> str:

    role_label = role.name.title().replace("_", " ") if role else "Turn"

    cleaned_content = content.strip()

    if discussion_update > 0:

        return f"## {role_label} Turn {turn_label} Discussion Update {discussion_update}\n\n{cleaned_content}"

    return f"## {role_label} Turn {turn_label} Reasoning\n\n{cleaned_content}" if cleaned_content else ""





def run_turn_start_call(manager, bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:

    base_path = Path(__file__).resolve().parents[2]

    role_specs: list[tuple[str, Path]] = [

        ("CAPTAIN", base_path / "captain" / "prompts" / "1_analysis.md"),

        ("FIRST_MATE", base_path / "first_mate" / "prompts" / "1_strategy_lock.md"),

        ("ENGINEER", base_path / "engineer" / "prompts" / "1_board_analysis.md"),

    ]

    roles_to_run = [

        (role_name, prompt_path)

        for role_name, prompt_path in role_specs

        if role_name in bundle.get("roles", {})

    ]

    if not roles_to_run:

        return {}



    outputs_dir = Path(__file__).resolve().parents[1] / "outputs"

    outputs_dir.mkdir(parents=True, exist_ok=True)

    team = str(bundle.get("team") or "team")

    turn = int(bundle.get("turn") or 0)



    results: dict[str, dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=len(roles_to_run)) as executor:

        futures = {

            executor.submit(_run_turn_start_role, manager, role_name, prompt_path, team, turn, outputs_dir): role_name

            for role_name, prompt_path in roles_to_run

        }

        for future in as_completed(futures):

            role_name = futures[future]

            results[role_name] = future.result()

    return results







def _load_strategy_alignment_prompt() -> str:

    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "3_strategy_alignment.md"

    return prompt_path.read_text(encoding="utf-8")





def _parse_strategy_alignment_payload(output_text: str) -> dict[str, str]:

    cleaned = output_text.strip()

    if not cleaned:

        return {}



    if cleaned.startswith("```"):

        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)

        cleaned = re.sub(r"\s*```$", "", cleaned).strip()



    start = cleaned.find("{")

    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:

        cleaned = cleaned[start:end + 1]



    payload = json.loads(cleaned)

    if not isinstance(payload, dict):

        return {}



    normalized: dict[str, str] = {}

    for role_name in (AgentRole.CAPTAIN.value, AgentRole.FIRST_MATE.value, AgentRole.ENGINEER.value):

        raw_value = payload.get(role_name)

        if isinstance(raw_value, dict):

            section_text = raw_value.get("strategy_to_follow")

        else:

            section_text = raw_value

        if isinstance(section_text, str) and section_text.strip():

            normalized[role_name] = section_text.strip()

    return normalized





def run_strategy_alignment(manager, bundle: dict[str, Any]) -> dict[str, Any]:

    base_path = Path(__file__).resolve().parents[2]

    outputs_dir = Path(__file__).resolve().parents[1] / "outputs"

    outputs_dir.mkdir(parents=True, exist_ok=True)



    team = str(bundle.get("team") or "team")

    turn = int(bundle.get("turn") or 0)

    team_name = team.replace(" ", "_").lower()



    role_specs: list[tuple[str, Path]] = [

        (AgentRole.CAPTAIN.value, base_path / "captain" / "strategy.md"),

        (AgentRole.FIRST_MATE.value, base_path / "first_mate" / "strategy.md"),

        (AgentRole.ENGINEER.value, base_path / "engineer" / "strategy.md"),

    ]

    active_roles = set(bundle.get("roles", {}))

    role_specs = [

        (role_name, strategy_path)

        for role_name, strategy_path in role_specs

        if role_name in active_roles

    ]



    if not role_specs:

        return {"updated": False, "reason": "no_active_roles"}



    role_contexts: list[str] = []

    role_paths: dict[str, Path] = {}



    for role_name, strategy_path in role_specs:

        role_slug = role_name.lower()

        context_path = Path(__file__).resolve().parents[1] / "contexts" / f"{role_slug}_{team_name}.md"

        if not context_path.exists():

            return {"updated": False, "reason": "missing_context", "role": role_name}



        context_text = context_path.read_text(encoding="utf-8")

        role_contexts.append(

            "\n".join([

                f"## {role_name}",

                "### Context",

                context_text,

            ])

        )

        role_paths[role_name] = strategy_path



    prompt = _load_strategy_alignment_prompt()

    combined_context = "\n\n".join([

        f"# Team: {team}",

        f"# Turn: {turn}",

        *role_contexts,

    ])



    model_name = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"

    result = call_agent_activity_with_context(

        model=model_name,

        prompt=prompt,

        context=combined_context,

        role="MANAGER",

        api_key=_select_api_key(manager),

        temperature=0.6,

        max_output_tokens=2048,

        timeout_seconds=60.0,

    )



    updated_sections = _parse_strategy_alignment_payload(getattr(result, "text", "") or "")

    if not updated_sections:

        return {"updated": False, "reason": "empty_or_invalid_model_output"}



    output_path = outputs_dir / f"strategy_alignment_{team_name}_turn_{turn}.json"

    output_path.write_text(json.dumps(updated_sections, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")



    results: dict[str, Any] = {}

    any_updated = False

    for role_name, strategy_path in role_paths.items():

        current_strategy = strategy_path.read_text(encoding="utf-8") if strategy_path.exists() else ""

        updated_section = updated_sections.get(role_name)

        if not isinstance(updated_section, str) or not updated_section.strip():

            results[role_name] = {"updated": False, "reason": "missing_role_output"}

            continue



        updated_strategy = _upsert_strategy_follow_section(current_strategy, updated_section)

        strategy_path.write_text(updated_strategy, encoding="utf-8")

        results[role_name] = {

            "updated": True,

            "strategy_path": str(strategy_path),

            "output_path": str(output_path),

        }

        any_updated = True



    return {

        "updated": any_updated,

        "output_path": str(output_path),

        "roles": results,

    }





def run_discussion_call(manager, bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:

    base_path = Path(__file__).resolve().parents[2]

    role_specs: list[tuple[str, Path]] = [

        ("CAPTAIN", base_path / "captain" / "prompts" / "2_discussion.md"),

        ("FIRST_MATE", base_path / "first_mate" / "prompts" / "2_system_selection.md"),

        ("ENGINEER", base_path / "engineer" / "prompts" / "2_selection.md"),

    ]

    roles_to_run = [

        (role_name, prompt_path)

        for role_name, prompt_path in role_specs

        if role_name in bundle.get("roles", {}) and prompt_path.exists()

    ]



    if not roles_to_run:

        return {}



    outputs_dir = Path(__file__).resolve().parents[1] / "outputs"

    outputs_dir.mkdir(parents=True, exist_ok=True)

    team = str(bundle.get("team") or "team")

    turn = int(bundle.get("turn") or 0)



    results: dict[str, dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=len(roles_to_run)) as executor:

        futures = {

            executor.submit(_run_turn_start_role, manager, role_name, prompt_path, team, turn, outputs_dir): role_name

            for role_name, prompt_path in roles_to_run

        }

        for future in as_completed(futures):

            role_name = futures[future]

            results[role_name] = future.result()

    return results





def _upsert_strategy_follow_section(strategy_text: str, updated_section: str) -> str:

    marker = "## Strategy to follow:"

    cleaned_section = updated_section.strip()

    if not cleaned_section:

        return strategy_text



    marker_match = re.search(r"^## Strategy to follow:\s*$", strategy_text, flags=re.MULTILINE)

    if marker_match:

        prefix = strategy_text[:marker_match.start()].rstrip()

    else:

        prefix = strategy_text.rstrip()



    parts = [part for part in (prefix, marker, cleaned_section) if part]

    return "\n\n".join(parts).rstrip() + "\n"





INDIVIDUAL_MEMORY_SUMMARY_THRESHOLD_CHARS = 2000

INDIVIDUAL_MEMORY_SUMMARY_THRESHOLD_LINES = 100

MASTER_MEMORY_SUMMARY_THRESHOLD_CHARS = INDIVIDUAL_MEMORY_SUMMARY_THRESHOLD_CHARS * 2

MASTER_MEMORY_SUMMARY_THRESHOLD_LINES = INDIVIDUAL_MEMORY_SUMMARY_THRESHOLD_LINES * 2





def _memory_needs_summary(content: str, *, char_limit: int, line_limit: int) -> bool:

    line_count = content.count("\n") + (1 if content else 0)

    return len(content) >= char_limit or line_count >= line_limit





def _load_memory_summary_prompt() -> str:

    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "4_memory_summary.md"

    return prompt_path.read_text(encoding="utf-8")





def _strip_code_fences(text: str) -> str:

    cleaned = text.strip()

    if cleaned.startswith("```"):

        cleaned = re.sub(r"^```(?:md|markdown)?\s*", "", cleaned)

        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    return cleaned







def update_memory(manager, context_report: dict[str, Any], discussion_update: int) -> None:

    outputs_dir = Path(__file__).resolve().parents[1] / "outputs"

    if not outputs_dir.exists():

        return



    output_files = sorted(

        path for path in outputs_dir.iterdir() if path.is_file() and path.suffix.lower() == ".md"

    )

    if not output_files:

        return



    for output_file in output_files:

        output_text = output_file.read_text(encoding="utf-8")

        turn_label = _turn_from_output_filename(output_file.name)



        master_update = _extract_section(output_text, "Master Memory Update")



        if master_update:

            role = _role_from_output_filename(output_file.name)

            role_label = role.name.title().replace("_", " ") if role else "Turn"

            newturn_label = turn_label

            if discussion_update > 0:

                newturn_label = f"{turn_label} Discussion Update {discussion_update}"

            master_path = Path(__file__).resolve().parents[2] / "common" / "master_memory.md"

            existing_master = master_path.read_text(encoding="utf-8") if master_path.exists() else ""

            master_block = f"## {role_label} Turn {newturn_label}\n\n{master_update.strip()}"

            separator = "\n\n" if existing_master and not existing_master.endswith("\n\n") else ""

            master_path.write_text(existing_master + separator + master_block + "\n", encoding="utf-8")



        role_update = _extract_section(output_text, "Memory Update")

        role = _role_from_output_filename(output_file.name)

        if role and role_update:

            memory_path = Path(__file__).resolve().parents[2] / role.name.lower() / "memory.md"

            current_memory = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""

            reasoning_append = _build_reasoning_append(role, turn_label, role_update, discussion_update)

            if reasoning_append:

                separator = "\n\n" if current_memory and not current_memory.endswith("\n\n") else ""

                memory_path.write_text(current_memory + separator + reasoning_append + "\n", encoding="utf-8")



    for output_file in output_files:

        try:

            output_file.unlink()

        except FileNotFoundError:

            continue



    for child in sorted(outputs_dir.iterdir(), key=lambda path: len(path.parts), reverse=True):

        if child.is_dir():

            shutil.rmtree(child, ignore_errors=True)





def summarize_memory(manager, state: GameState | None = None) -> dict[str, Any]:

    base_path = Path(__file__).resolve().parents[2]

    team = str(getattr(manager, "team", "team") or "team")

    turn = int(getattr(manager, "_turn_id", getattr(state, "turn", 0)) or 0)



    memory_specs: list[tuple[str, Path]] = [

        ("MASTER_MEMORY", base_path / "common" / "master_memory.md"),

        ("CAPTAIN_MEMORY", base_path / "captain" / "memory.md"),

        ("FIRST_MATE_MEMORY", base_path / "first_mate" / "memory.md"),

        ("ENGINEER_MEMORY", base_path / "engineer" / "memory.md"),

    ]



    if not any(

        _memory_needs_summary(

            path.read_text(encoding="utf-8") if path.exists() else "",

            char_limit=(MASTER_MEMORY_SUMMARY_THRESHOLD_CHARS if label == "MASTER_MEMORY" else INDIVIDUAL_MEMORY_SUMMARY_THRESHOLD_CHARS),

            line_limit=(MASTER_MEMORY_SUMMARY_THRESHOLD_LINES if label == "MASTER_MEMORY" else INDIVIDUAL_MEMORY_SUMMARY_THRESHOLD_LINES),

        )

        for label, path in memory_specs

    ):

        return {"summarized": False, "reason": "below_threshold"}



    prompt = _load_memory_summary_prompt()

    outputs_dir = Path(__file__).resolve().parents[1] / "outputs"

    outputs_dir.mkdir(parents=True, exist_ok=True)



    model_name = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"

    updated_files: dict[str, str] = {}

    any_summarized = False



    for label, path in memory_specs:

        current_memory = path.read_text(encoding="utf-8") if path.exists() else ""

        if not _memory_needs_summary(

            current_memory,

            char_limit=(MASTER_MEMORY_SUMMARY_THRESHOLD_CHARS if label == "MASTER_MEMORY" else INDIVIDUAL_MEMORY_SUMMARY_THRESHOLD_CHARS),

            line_limit=(MASTER_MEMORY_SUMMARY_THRESHOLD_LINES if label == "MASTER_MEMORY" else INDIVIDUAL_MEMORY_SUMMARY_THRESHOLD_LINES),

        ):

            continue



        result = call_agent_activity_with_context(

            model=model_name,

            prompt=prompt,

            context="\n".join([

                f"# Team: {team}",

                f"# Turn: {turn}",

                f"# Memory Type: {label}",

                current_memory,

            ]),

            role="MANAGER",

            api_key=_select_api_key(manager),

            temperature=0.4,

            max_output_tokens=1500,

            timeout_seconds=60.0,

        )



        summarized_text = _strip_code_fences(getattr(result, "text", "") or "")

        if not summarized_text:

            continue



        path.write_text(summarized_text.rstrip() + "\n", encoding="utf-8")

        summary_path = outputs_dir / f"memory_summary_{label.lower()}_{team.replace(' ', '_').lower()}_turn_{turn}.md"

        summary_path.write_text(summarized_text, encoding="utf-8")

        updated_files[label] = str(path)

        any_summarized = True



    if not any_summarized:

        return {"summarized": False, "reason": "empty_or_invalid_model_output"}



    return {

        "summarized": True,

        "sections": updated_files,

    }





sumarize_memory = summarize_memory





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





# ─── Inter-agent communications (Q&A) ────────────────────────────────────────



# Section header in discussion outputs that marks a question directed at another role.

# Example: "## Question to ENGINEER" inside captain_blue_turn_3.md

_QUESTION_HEADER_RE = re.compile(

    r"^## Question to ([A-Z_]+)\s*$([\s\S]*?)(?=^##\s+|\Z)",

    re.MULTILINE,

)



# Header that the answer LLM is asked to produce, identifying which asker the

# block is for.  Example: "### To CAPTAIN".

_ANSWER_BLOCK_RE = re.compile(

    r"^### To ([A-Z_]+)\s*$([\s\S]*?)(?=^###\s+|\Z)",

    re.MULTILINE,

)



_KNOWN_ROLE_NAMES = {role.name for role in AgentRole}





def _asker_from_output_filename(file_name: str, team_slug: str) -> str | None:

    """Infer the asker role name from an output filename like 'captain_blue_turn_3.md'."""

    suffix = f"_{team_slug}_turn_"

    if suffix not in file_name:

        return None

    candidate = file_name.split(suffix, 1)[0].upper()

    return candidate if candidate in _KNOWN_ROLE_NAMES else None





def extract_communications(team: str, turn: int) -> dict[str, list[tuple[str, str]]]:

    """Scan discussion outputs for outbound questions, group by recipient, write per-receiver files.



    Must run BEFORE ``update_memory`` because that helper deletes the outputs/

    directory contents at the end of its execution.



    Returns a mapping ``{recipient_name: [(asker_name, question_body), ...]}``.

    Also writes ``src/agents/manager/communications/to_<receiver>_<team>_turn_<N>.md``

    containing one ``## From <ASKER>`` block per incoming question.

    """

    base = Path(__file__).resolve().parents[1]

    outputs_dir = base / "outputs"

    comms_dir = base / "communications"



    team_slug = str(team or "team").replace(" ", "_").lower()

    by_recipient: dict[str, list[tuple[str, str]]] = {}



    if not outputs_dir.exists():

        return by_recipient



    for output_file in sorted(outputs_dir.iterdir()):

        if not output_file.is_file() or output_file.suffix.lower() != ".md":

            continue

        asker = _asker_from_output_filename(output_file.name, team_slug)

        if not asker:

            continue

        try:

            text = output_file.read_text(encoding="utf-8")

        except OSError:

            continue

        for match in _QUESTION_HEADER_RE.finditer(text):

            recipient = match.group(1).strip().upper()

            body = match.group(2).strip()

            if not body or recipient == asker or recipient not in _KNOWN_ROLE_NAMES:

                continue

            by_recipient.setdefault(recipient, []).append((asker, body))



    if not by_recipient:

        return by_recipient



    comms_dir.mkdir(parents=True, exist_ok=True)

    for recipient, items in by_recipient.items():

        recipient_slug = recipient.lower()

        file_path = comms_dir / f"to_{recipient_slug}_{team_slug}_turn_{turn}.md"

        parts = [f"# Questions for {recipient} (Team: {team}, Turn: {turn})", ""]

        for asker, body in items:

            parts.extend([f"## From {asker}", body, ""])

        file_path.write_text("\n".join(parts), encoding="utf-8")



    return by_recipient





def _read_role_file(role_name: str, filename: str) -> str:

    """Read ``src/agents/<role>/<filename>`` if it exists, else return empty string."""

    path = Path(__file__).resolve().parents[2] / role_name.lower() / filename

    if not path.exists():

        return ""

    try:

        return path.read_text(encoding="utf-8")

    except OSError:

        return ""





def _render_answer_context(

    recipient: str,

    team: str,

    turn: int,

    questions_for_recipient: list[tuple[str, str]],

) -> str:

    """Render the per-recipient context block for the answer LLM call.



    Uses the same structure as ``build_turn_start_context_bundle`` writes for

    each role, but replaces the ``# Play Context`` section with the

    consolidated questions directed at this recipient. The role's freshly

    updated memory is included so the recipient can ground its answer in its

    accumulated turn-over-turn knowledge.

    """

    question_parts: list[str] = []

    for asker, body in questions_for_recipient:

        question_parts.extend([f"## From {asker}", body, ""])

    questions_section = "\n".join(question_parts).rstrip()



    context_md = read_role_memory(recipient)

    strategy_md = _read_role_file(recipient, "strategy.md")

    memory_md = _read_role_file(recipient, "memory.md")

    master_memory_md = read_master_memory()

    common_context_md = read_common_context()



    parts = [

        f"# Turn Context for {recipient} (team: {team}, turn: {turn})",

        "",

        "# Context",

        context_md,

        "",

        "# Strategy",

        strategy_md,

        "",

        "# Memory",

        memory_md,

        "",

        "# Master Memory",

        master_memory_md,

        "",

        "# Common Context",

        common_context_md,

        "",

        "# Questions to Answer",

        questions_section,

        "",

    ]

    return "\n".join(parts)





def _answer_one_recipient(

    manager,

    recipient: str,

    context_text: str,

    model_name: str,

) -> tuple[str, str]:

    """Run a single LLM answer call for one recipient.  Returns (recipient, answer_text)."""

    prompt = (

        f"You are the {recipient}. Above this prompt you have your role's Context, "

        f"Strategy, Memory, Master Memory, Common Context, and a final "

        f"'# Questions to Answer' section containing questions your teammates "

        f"directed at you this turn.\n\n"

        f"Answer each question concisely, grounded in your role's accumulated "

        f"knowledge from the sections above. Produce one section per asker, in this "

        f"exact format and using uppercase role names (CAPTAIN, FIRST_MATE, "

        f"ENGINEER, RADIO_OPERATOR):\n\n"

        f"### To <ASKER_ROLE>\n"

        f"Q: <restate the question briefly>\n"

        f"A: <your concise answer>\n\n"

        f"Do not include any text outside these sections."

    )

    result = call_agent_activity_with_context(

        model=model_name,

        prompt=prompt,

        context=context_text,

        role=recipient,

        api_key=_select_api_key(manager),

        temperature=0.6,

        max_output_tokens=512,

        timeout_seconds=45.0,

    )

    return recipient, (getattr(result, "text", "") or "")





def answer_communications(

    manager,

    by_recipient: dict[str, list[tuple[str, str]]],

    team: str,

    turn: int,

) -> dict[str, str]:

    """Fire a parallel LLM call per recipient, append each answer to the asker's memory.



    For every recipient with incoming questions:

      * assemble a bundle-style context for that recipient — its own Context,

        Strategy, Memory, Master Memory, and Common Context — with the

        consolidated questions replacing the usual ``# Play Context`` section

      * prompt the LLM to produce ``### To <ASKER>`` blocks (Q:/A:)

      * for each parsed block, append to ``src/agents/<asker>/memory.md`` as

        ``### Answer from <RECIPIENT> (Turn N)`` followed by Q:/A:



    Returns ``{recipient: raw_answer_text}`` for inspection/testing.

    """

    answers: dict[str, str] = {}

    if not by_recipient:

        return answers



    base_role_dirs = Path(__file__).resolve().parents[2]

    model_name = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"



    # Build (recipient, assembled_context) pairs — context built from bundle-style data

    jobs: list[tuple[str, str]] = []

    for recipient, items in by_recipient.items():

        if not items:

            continue

        context_text = _render_answer_context(recipient, team, turn, items)

        jobs.append((recipient, context_text))



    if not jobs:

        return answers



    # Parallel LLM calls — one per receiver

    with ThreadPoolExecutor(max_workers=len(jobs)) as executor:

        futures = {

            executor.submit(_answer_one_recipient, manager, recipient, ctx, model_name): recipient

            for recipient, ctx in jobs

        }

        for future in as_completed(futures):

            recipient = futures[future]

            try:

                _, answer_text = future.result()

            except Exception:

                continue

            answers[recipient] = answer_text



    # Parse answers and append to the askers' memory files

    for recipient, answer_text in answers.items():

        for match in _ANSWER_BLOCK_RE.finditer(answer_text):

            asker = match.group(1).strip().upper()

            body = match.group(2).strip()

            if not body or asker not in _KNOWN_ROLE_NAMES:

                continue

            memory_path = base_role_dirs / asker.lower() / "memory.md"

            if not memory_path.parent.exists():

                continue

            try:

                existing = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""

            except OSError:

                existing = ""

            append_block = f"### Answer from {recipient} (Turn {turn})\n{body}"

            separator = "\n\n" if existing and not existing.endswith("\n\n") else ""

            memory_path.write_text(existing + separator + append_block + "\n", encoding="utf-8")



    return answers



def run_captain_finalization_call(

    manager,

    possible_actions: list[dict[str, Any]],

    resolved_context_report: dict[str, Any],

    extra_context: str | None = None,

) -> dict[str, Any]:

    

    

    base_path = Path(__file__).resolve().parents[2]

    prompt_path = base_path / "manager" / "prompts" / "5_finalization.md"



    prompt = prompt_path.read_text(encoding="utf-8").strip()



    # Resolve team / turn from manager state

    team: str = str(getattr(manager, "team", "team") or "team")

    turn: int = int(getattr(manager, "_turn_id", 0) or 0)

    team_name = team.replace(" ", "_").lower()

    capitanpath = Path(__file__).resolve().parents[2] / "captain" / "memory.md"

    current_memory = capitanpath.read_text(encoding="utf-8")


    if extra_context:

        capitanpath.write_text(current_memory + "\n" + extra_context + "\n", encoding="utf-8")

    bundle = build_turn_start_context_bundle(manager, resolved_context_report)



    context_path = (

        Path(__file__).resolve().parents[1] / "contexts" / f"captain_{team_name}.md"

    )

    base_context = (

        context_path.read_text(encoding="utf-8") if context_path.exists() else ""

    )

    possible_block = (

        json.dumps(possible_actions, indent=2, ensure_ascii=False)

        if possible_actions

        else "[]"

    )

    full_context = base_context

    full_context = "\n".join([full_context, "", possible_block, ""])





    model_name = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"

    result = call_agent_activity_with_context(

        model=model_name,

        prompt=prompt,

        context=full_context,

        role="CAPTAIN",

        api_key=_select_api_key(manager),

        temperature=0.4,

        max_output_tokens=512,

        timeout_seconds=45.0,

    )

    output_text: str = getattr(result, "text", "") or ""



    print(f"[manager_helpers] captain finalization output path=captain_{team_name}_turn_{turn}.md\n{output_text}")



    outputs_dir = Path(__file__).resolve().parents[1] / "outputs"

    outputs_dir.mkdir(parents=True, exist_ok=True)

    output_path = outputs_dir / f"captain_{team_name}_turn_{turn}.md"

    output_path.write_text(output_text, encoding="utf-8")



    raw_section = _extract_section(output_text, "Chosen Action").strip()

    if not raw_section: return {}



    cleaned = raw_section

    if cleaned.startswith("```"):

        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)

        cleaned = re.sub(r"\s*```$", "", cleaned).strip()



    start = cleaned.find("{")

    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:

        return {}

    cleaned = cleaned[start : end + 1]



    try:

        action = json.loads(cleaned)

    except json.JSONDecodeError:

        print("[manager_helpers] finalization parse failed: invalid JSON")

        return {}



    if not isinstance(action, dict):

        print("[manager_helpers] finalization parse failed: top-level not object")

        return {}



    raw_actions = action.get("actions")

    if raw_actions is None:

        raw_actions = [action]

    if not isinstance(raw_actions, list) or not raw_actions:

        print("[manager_helpers] finalization parse failed: actions missing or empty")

        return {}



    normalized_actions: list[dict[str, Any]] = []

    for raw_action in raw_actions:

        if not isinstance(raw_action, dict) or not isinstance(raw_action.get("type"), str):

            print("[manager_helpers] finalization parse failed: action missing type")

            return {}

        if not isinstance(raw_action.get("payload"), dict):

            raw_action["payload"] = {}

        normalized_actions.append(raw_action)



    print(f"[manager_helpers] finalization parsed actions={normalized_actions}")

    return {"actions": normalized_actions}


# ─── Radio Operator helpers ──────────────────────────────────────────────────
# Sector grid constants (mirroring captain_sonar.config)
_RO_SECTOR_ROWS = 2
_RO_SECTOR_COLS = 3
def _ro_sector_for_position(x: int, y: int, map_width: int, map_height: int) -> int:
    # Return the 1-indexed sector number for grid position (x, y).
    row = min(_RO_SECTOR_ROWS - 1, (y * _RO_SECTOR_ROWS) // max(1, map_height))
    col = min(_RO_SECTOR_COLS - 1, (x * _RO_SECTOR_COLS) // max(1, map_width))
    return row * _RO_SECTOR_COLS + col + 1


def _ro_compute_best_false_sector(own_sector: int | None, sector_masses: dict) -> int | None:
    # Return the highest-mass enemy sector that is not our actual sector (maximally plausible lie).
    if own_sector is None:
        return None
    for sector, _ in sorted(sector_masses.items(), key=lambda kv: kv[1], reverse=True):
        if sector != own_sector:
            return sector
    for candidate in range(1, 7):
        if candidate != own_sector:
            return candidate
    return None


def run_radio_operator_phase(manager, team_view: dict[str, Any]) -> list[dict[str, Any]]:
    # Compute Radio Operator intel for the current turn using only deterministic logic.
    # All values come from the BeliefTracker snapshot already in team_view.
    # Returns [{"recipient": role_name, "text": str, "metadata": dict}, ...]
    radio: dict = team_view.get("radio_operator") or {}
    most_likely_pos: dict | None = radio.get("most_likely_position")
    most_likely_sector: int | None = radio.get("most_likely_sector")
    confidence: float = float(radio.get("confidence") or 0.0)
    sector_masses: dict = radio.get("sector_probability_masses") or {}
    possible_positions: list = radio.get("possible_current_positions") or []
    heard_moves: list = radio.get("heard_moves") or []

    conf_label = "HIGH" if confidence >= 0.7 else "MEDIUM" if confidence >= 0.4 else "LOW"
    pos_str = (
        f"({most_likely_pos['x']},{most_likely_pos['y']})"
        if isinstance(most_likely_pos, dict) else "unknown"
    )
    sector_str = str(most_likely_sector) if most_likely_sector is not None else "unknown"
    move_summary = ",".join(heard_moves[-6:]) if heard_moves else "none"
    narrowed = len(possible_positions)

    best_sector = max(sector_masses, key=lambda s: sector_masses[s]) if sector_masses else None
    if best_sector is not None:
        recommended_sensor = "drone"
        sensor_detail = f"sector {best_sector}"
    else:
        recommended_sensor = "sonar"
        sensor_detail = "no sector locked yet"

    captain_text = (
        f"Enemy ~{pos_str} sector {sector_str} "
        f"[conf {conf_label} {confidence:.0%}]. "
        f"Last moves: {move_summary}. "
        f"Search space: {narrowed} cell(s). "
        f"Best sensor: {recommended_sensor} {sensor_detail}."
    )
    first_mate_text = (
        f"Charge {recommended_sensor} ({sensor_detail}). "
        f"Enemy confidence {conf_label}."
    )

    return [
        {
            "recipient": "CAPTAIN",
            "text": captain_text,
            "metadata": {
                "most_likely_position": most_likely_pos,
                "most_likely_sector": most_likely_sector,
                "confidence": confidence,
                "possible_count": narrowed,
                "recommended_sensor": recommended_sensor,
                "best_sector": best_sector,
            },
        },
        {
            "recipient": "FIRST_MATE",
            "text": first_mate_text,
            "metadata": {
                "recommended_sensor": recommended_sensor,
                "best_sector": best_sector,
            },
        },
    ]


def _response_to_sonar(manager, context_report: dict[str, Any]) -> dict[str, Any]:
    # Generate the agent sonar response: one true piece (computed by the game
    # engine from our actual position) + one false piece (we choose type + value).
    # The false_type MUST differ from what the attacker queried (true_type).
    # When the attacker's belief heatmap is provided we lie with the most
    # plausible position the attacker still believes we could be at.
    # Returns {"false_type": str, "false_value": int|str}.
    team_view: dict = context_report.get("team_view") or {}
    own_sub: dict = team_view.get("own_submarine") or {}
    map_info: dict = team_view.get("map") or {}
    turn: int = int(team_view.get("turn") or 0)
    attacker_belief: list | None = context_report.get("attacker_belief")

    own_x = int(own_sub.get("x") or 0)
    own_y = int(own_sub.get("y") or 0)
    map_w = int(map_info.get("width") or 15)
    map_h = int(map_info.get("height") or 15)

    # Determine what the attacker queried — mirrors the game engine's own default.
    sonar_action = context_report.get("sonar_action")
    true_type: str = ["row", "col", "sector"][turn % 3]
    if sonar_action is not None:
        payload_type = (getattr(sonar_action, "payload", None) or {}).get("true_type")
        if payload_type in ("row", "col", "sector"):
            true_type = payload_type

    # false_type must differ from true_type; prefer "sector" as most ambiguous.
    available_false_types = [t for t in ("sector", "row", "col") if t != true_type]
    false_type: str = available_false_types[0]

    # --- Find the best cell to lie about ---
    # If we have the attacker's belief heatmap, pick the highest-probability
    # cell that is NOT our actual position.  That cell is still plausible to
    # the attacker, making the lie hard to detect.
    false_x, false_y = own_x, own_y  # fallback: same position (overridden below)
    if isinstance(attacker_belief, list) and attacker_belief:
        best_prob = -1.0
        for cy, row in enumerate(attacker_belief):
            if not isinstance(row, list):
                continue
            for cx, prob in enumerate(row):
                if (cx, cy) == (own_x, own_y):
                    continue  # skip our actual position
                p = float(prob)
                if p > best_prob:
                    best_prob = p
                    false_x, false_y = cx, cy

    # Derive false_value from the chosen cell for the chosen false_type.
    false_sector = _ro_sector_for_position(false_x, false_y, map_w, map_h)
    false_row_str = chr(ord("A") + false_y)
    false_col_int = false_x + 1  # 1-indexed

    # Our actual values for a safety-check below.
    own_sector = _ro_sector_for_position(own_x, own_y, map_w, map_h)
    own_row_str = chr(ord("A") + own_y)
    own_col_int = own_x + 1

    if false_type == "sector":
        false_value: int | str = false_sector
        # Ensure it genuinely differs; fall back to offset if needed.
        if false_value == own_sector:
            false_value = (own_sector % (_RO_SECTOR_ROWS * _RO_SECTOR_COLS)) + 1
    elif false_type == "row":
        false_value = false_row_str
        if false_value == own_row_str:
            false_value = chr(ord("A") + (own_y + 1) % map_h)
    else:  # col
        false_value = false_col_int
        if false_value == own_col_int:
            false_value = (own_col_int % map_w) + 1

    print(
        f"[radio_operator] sonar response: true_type={true_type} "
        f"false_type={false_type} false_value={false_value} "
        f"(own pos=({own_x},{own_y}) false pos=({false_x},{false_y}))"
    )
    return {"false_type": false_type, "false_value": false_value}



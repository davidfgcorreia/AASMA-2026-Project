from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable, TYPE_CHECKING

from captain_sonar.api import get_team_view
from captain_sonar.game_state import GameState

from agents.base import AgentRole
from agents.common.gemini import GeminiResponse, call_gemini, load_env_file

if TYPE_CHECKING:
    from agents.manager import TeamAgentManager


def read_role_memory(role: AgentRole | str, base_path: str | Path | None = None) -> str:
    """Read a role context, prompt, or memory markdown file if present."""
    # Roles are stored in lowercase directories (e.g., 'captain'), prefer role.name.lower().
    if isinstance(role, AgentRole):
        resolved_role = role.name.lower()
    else:
        resolved_role = str(role).lower()
    root = Path(base_path) if base_path is not None else Path(__file__).resolve().parent.parent
    context_path = root / resolved_role / "context.md"
    if context_path.exists():
        return context_path.read_text(encoding="utf-8")
    prompt_path = root / resolved_role / "prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    memory_path = root / resolved_role / "memory.md"
    if memory_path.exists():
        return memory_path.read_text(encoding="utf-8")
    return ""


def read_master_memory(base_path: str | Path | None = None) -> str:
    """Read the shared team memory file."""
    root = Path(base_path) if base_path is not None else Path(__file__).resolve().parent
    memory_path = root / "master_memory.md"
    if not memory_path.exists():
        return ""
    return memory_path.read_text(encoding="utf-8")


def read_turn_actions(base_path: str | Path | None = None) -> str:
    """Read the shared turn-actions ledger."""
    root = Path(base_path) if base_path is not None else Path(__file__).resolve().parent
    ledger_path = root / "turn_actions.md"
    if not ledger_path.exists():
        return ""
    return ledger_path.read_text(encoding="utf-8")


def read_common_context(base_path: str | Path | None = None) -> str:
    """Read the shared game-rules context file."""
    root = Path(base_path) if base_path is not None else Path(__file__).resolve().parent
    context_path = root / "context.md"
    if not context_path.exists():
        return ""
    return context_path.read_text(encoding="utf-8")


def write_master_memory(content: str, base_path: str | Path | None = None) -> Path:
    """Overwrite the shared team memory file."""
    root = Path(base_path) if base_path is not None else Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    memory_path = root / "master_memory.md"
    memory_path.write_text(content, encoding="utf-8")
    return memory_path


def write_turn_actions(content: str, base_path: str | Path | None = None) -> Path:
    """Overwrite the shared turn-actions ledger."""
    root = Path(base_path) if base_path is not None else Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    ledger_path = root / "turn_actions.md"
    ledger_path.write_text(content, encoding="utf-8")
    return ledger_path


def update_turn_actions(section: str, content: str, base_path: str | Path | None = None) -> str:
    """Update or append a section in the shared turn-actions ledger."""
    ledger_text = read_turn_actions(base_path)
    section_header = f"## {section}"
    lines = ledger_text.splitlines()
    updated: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if line.strip() == section_header:
            updated.append(line)
            updated.append("")
            updated.extend(content.strip().splitlines())
            index += 1
            while index < len(lines) and not lines[index].startswith("## "):
                index += 1
            continue

        updated.append(line)
        index += 1

    if section_header not in ledger_text:
        if updated and updated[-1] != "":
            updated.append("")
        updated.append(section_header)
        updated.append("")
        updated.extend(content.strip().splitlines())

    new_text = "\n".join(updated).rstrip() + "\n"
    write_turn_actions(new_text, base_path)
    return new_text


def update_master_memory(section: str, content: str, base_path: str | Path | None = None) -> str:
    """Update or append a section in the shared team memory file."""
    memory_text = read_master_memory(base_path)
    section_header = f"## {section}"
    updated = memory_text.splitlines()
    if updated and updated[-1] != "":
        updated.append("")
    updated.append(section_header)
    updated.append("")
    updated.extend(content.strip().splitlines())

    new_text = "\n".join(updated).rstrip() + "\n"
    write_master_memory(new_text, base_path)
    return new_text


def build_activity_context(
    *,
    team_view: dict[str, Any],
    role: AgentRole | str,
    message_history: Iterable[dict[str, Any]] | None = None,
    role_memory: str | None = None,
    master_memory: str | None = None,
    common_context: str | None = None,
) -> str:
    """Build the shared context passed to Gemini for a role activity call."""
    resolved_role = role.value if isinstance(role, AgentRole) else str(role)
    lines = [
        f"role={resolved_role}",
        f"team={team_view.get('team')}",
        f"turn={team_view.get('turn')}",
        f"active_roles={team_view.get('active_roles', [])}",
    ]
    if role_memory:
        lines.append("role_memory:")
        lines.append(role_memory.strip())
    if common_context:
        lines.append("common_context:")
        lines.append(common_context.strip())
    if master_memory:
        lines.append("master_memory:")
        lines.append(master_memory.strip())
    if message_history:
        lines.append("inbox:")
        for message in message_history:
            sender = message.get("sender")
            text = message.get("text")
            lines.append(f"- {sender}: {text}")
    lines.append("team_view:")
    lines.append(_stringify(team_view))
    return "\n".join(lines)


def build_activity_prompt(goal: str, constraints: Iterable[str] | None = None) -> str:
    """Build the direct task prompt for Gemini."""
    lines = [goal.strip()]
    if constraints:
        lines.append("constraints:")
        for constraint in constraints:
            lines.append(f"- {constraint}")
    return "\n".join(lines)


def call_agent_activity(
    *,
    model: str,
    prompt: str,
    team_view: dict[str, Any],
    role: AgentRole | str,
    api_key: str | None = None,
    role_memory: str | None = None,
    message_history: Iterable[dict[str, Any]] | None = None,
    system_instruction: str | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    safety_settings: list[dict[str, Any]] | None = None,
    extra_generation_config: dict[str, Any] | None = None,
    timeout_seconds: float | None = None,
    master_memory: str | None = None,
) -> GeminiResponse:
    """Call Gemini for a single agent activity step."""
    load_env_file()
    context = build_activity_context(
        team_view=team_view,
        role=role,
        message_history=message_history,
        role_memory=role_memory or read_role_memory(role),
        common_context=read_common_context(),
        master_memory=master_memory or read_master_memory(),
    )
    return call_gemini(
        model=model,
        api_key=api_key,
        context=context,
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        top_p=top_p,
        top_k=top_k,
        safety_settings=safety_settings,
        extra_generation_config=extra_generation_config,
        timeout_seconds=timeout_seconds if timeout_seconds is not None else 60.0,
    )

def call_agent_activity_with_context(
    *,
    model: str,
    prompt: str,
    context: str,
    role: AgentRole | str,
    api_key: str | None = None,
    system_instruction: str | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    safety_settings: list[dict[str, Any]] | None = None,
    extra_generation_config: dict[str, Any] | None = None,
    timeout_seconds: float | None = None,
) -> GeminiResponse:
    """Call Gemini using a pre-built context string (no context assembly).

    This helper is for callers that already have a complete context string
    and do not want the function to assemble it from files.
    """
    load_env_file()
    return call_gemini(
        model=model,
        api_key=api_key,
        context=context,
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        top_p=top_p,
        top_k=top_k,
        safety_settings=safety_settings,
        extra_generation_config=extra_generation_config,
        timeout_seconds=timeout_seconds if timeout_seconds is not None else 60.0,
    )


def send_inter_agent_message(
    manager: TeamAgentManager,
    sender: AgentRole,
    recipient: AgentRole | None,
    text: str,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Route a message through the manager with a single helper call."""
    from agents.manager.pipeline_helpers.manager_api import send_message as manager_send_message
    return manager_send_message(manager, sender, recipient, text, metadata)


def broadcast_team_message(
    manager: TeamAgentManager,
    sender: AgentRole,
    text: str,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Broadcast a message to the active team roles."""
    from agents.manager.pipeline_helpers.manager_api import broadcast as manager_broadcast
    return manager_broadcast(manager, sender, text, metadata)


def build_team_activity_payload(
    state: GameState,
    team: str,
    role: AgentRole | str,
    *,
    turn_id: int | None = None,
) -> dict[str, Any]:
    """Convenience wrapper for team-specific agent inputs."""
    team_view = get_team_view(state, team)
    if turn_id is not None:
        team_view["turn_id"] = turn_id
    team_view["role"] = role.value if isinstance(role, AgentRole) else str(role)
    return team_view


def _stringify(value: Any) -> str:
    if is_dataclass(value):
        return _stringify(asdict(value))
    if isinstance(value, dict):
        return "{" + ", ".join(f"{key}: {_stringify(item)}" for key, item in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(_stringify(item) for item in value) + "]"
    if isinstance(value, tuple):
        return "(" + ", ".join(_stringify(item) for item in value) + ")"
    return repr(value)


def action_signature(action: dict[str, Any]) -> str:
    """Create a stable signature for a turn action proposal."""
    return json.dumps(action, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
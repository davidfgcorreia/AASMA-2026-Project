"""Starting prompt bootstrapper for TeamAgentManager.

Loads base role prompts from the role directories and overlays strategy
directives to produce a concrete starting prompt for each active role.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from .models import TeamOperatingMode


def _read_role_prompt_file(role_name: str) -> str | None:
    base = Path(__file__).resolve().parents[1]
    role_prompt = base / role_name / "prompt.md"
    if not role_prompt.exists():
        return None
    return role_prompt.read_text(encoding="utf-8")


def bootstrap_prompts(team: str, roles: list[str], strategy_profile: dict[str, Any], mode: TeamOperatingMode) -> dict[str, str]:
    prompts: dict[str, str] = {}
    directives = strategy_profile.get("directives", {}) if strategy_profile else {}
    for role in roles:
        base_text = _read_role_prompt_file(role) or f"# {role.title()} Role\nYou are {role} for team {team}."
        strategy_note = directives.get(role, "")
        overlay = f"\n\n# Strategy Directive\n{strategy_note}\n" if strategy_note else ""
        # Mode-aware adaptation: annotate captain role when human-controlled
        if mode == TeamOperatingMode.THREE_AGENT and role == "captain":
            overlay += "\nNote: captain is human-controlled in this mode. Coordinate with human.\n"
        prompts[role] = base_text + overlay
    return prompts

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from ..base import AgentBase, AgentRole
from agents.common.functions import call_agent_activity
from captain_sonar.possible_actions import possible_actions_for_role


AGENT_DIR = Path(__file__).resolve().parent
SYSTEM_PRIORITY = ("torpedo", "sonar", "drone", "silence", "mine", "scenario")


def _read_text(*parts: str) -> str:
    path = AGENT_DIR.joinpath(*parts)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _preferred_system(team_view: dict[str, object]) -> str:
    ready = team_view.get("system_utilization", {}).get("ready", {})
    if isinstance(ready, dict):
        for candidate in SYSTEM_PRIORITY:
            if not ready.get(candidate, False):
                return candidate
    return "torpedo"


def _build_load_action(system: str, team_view: dict[str, object]) -> dict[str, object]:
    possible_actions = possible_actions_for_role("first_mate", team_view)
    return {
        "role": AgentRole.FIRST_MATE.value,
        "first_step": {"type": "CHARGE", "payload": {"system": system}},
        "second_step": {"type": "ACTIVATE", "payload": {"system": system}},
        "full_action": None,
        "possible_actions": possible_actions,
    }


@dataclass
class FirstMateAgent(AgentBase):
    """First mate role agent placeholder."""

    def __init__(self, team: str) -> None:
        super().__init__(team=team, role=AgentRole.FIRST_MATE)

    def act(self, deadline_ms: int) -> dict[str, object]:
        raise NotImplementedError("FirstMateAgent logic is not implemented yet.")

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        return _build_load_action(_preferred_system(team_view), team_view)


@dataclass(init=False)
class ModelFirstMateAgent(FirstMateAgent):
    """Model-driven first mate agent that selects the next system to load.

    The agent uses two prompt stages: first it locks onto the role strategy,
    then it chooses a single system to charge next. If the model response
    cannot be parsed, the agent falls back to the deterministic selector.
    """

    def __init__(self, team: str) -> None:
        super().__init__(team=team)

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        ready = team_view.get("system_utilization", {}).get("ready", {})
        candidate_systems = [system for system in SYSTEM_PRIORITY if isinstance(ready, dict) and not ready.get(system, False)]
        if not candidate_systems:
            candidate_systems = ["torpedo"]

        strategy_lock = _read_text("strategy.md")
        phase_1 = _read_text("prompts", "1_strategy_lock.md")

        # Agent-local files
        agent_memory = _read_text("memory.md")
        agent_context = _read_text("context.md")

        # Play context lives in the common agent folder
        play_ctx_path = AGENT_DIR.parent.joinpath("common", "play_context.md")
        play_context = ""
        try:
            if play_ctx_path.exists():
                play_context = play_ctx_path.read_text(encoding="utf-8").strip()
        except Exception:
            play_context = ""

        # Build role_memory in the requested order: strategy, memory, context, play
        parts: list[str] = []
        if strategy_lock:
            parts.append("--- STRATEGY ---\n" + strategy_lock)
        if agent_memory:
            parts.append("--- AGENT MEMORY ---\n" + agent_memory)
        if agent_context:
            parts.append("--- AGENT CONTEXT ---\n" + agent_context)
        if play_context:
            parts.append("--- PLAY CONTEXT ---\n" + play_context)
        role_memory_combined = "\n\n".join(parts) if parts else None

        # For now use only the first-phase prompt as the direct task prompt
        prompt = phase_1

        model = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"

        try:
            response = call_agent_activity(
                model=model,
                prompt=prompt,
                team_view=team_view,
                role=self.role,
                role_memory=role_memory_combined,
                max_output_tokens=256,
            )
            parsed = json.loads(response.text.strip())
            selected_system = None
            if isinstance(parsed, dict):
                raw_system = parsed.get("system") or parsed.get("load_system")
                if isinstance(raw_system, str):
                    selected_system = raw_system.strip().lower()
            if selected_system not in candidate_systems:
                raise ValueError("model selected an invalid system")
        except Exception:
            selected_system = _preferred_system(team_view)

        return _build_load_action(selected_system, team_view)

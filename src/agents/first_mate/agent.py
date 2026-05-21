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


def _system_is_ready(system: str, team_view: dict[str, object]) -> bool:
    ready = team_view.get("system_utilization", {}).get("ready", {})
    return bool(isinstance(ready, dict) and ready.get(system, False))


def _build_load_action(system: str, team_view: dict[str, object]) -> dict[str, object]:
    possible_actions = possible_actions_for_role("first_mate", team_view)
    second_step = (
        {"type": "ACTIVATE", "payload": {"system": system}}
        if _system_is_ready(system, team_view)
        else None
    )
    return {
        "role": AgentRole.FIRST_MATE.value,
        "first_step": {"type": "CHARGE", "payload": {"system": system}},
        "second_step": second_step,
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
        phase_1_prompt = _read_text("prompts", "1_strategy_lock.md")
        phase_2_prompt = _read_text("prompts", "2_system_selection.md")

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

        model = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"
        inbox = team_view.get("inbox") or []

        selected_system = None
        reasoning = ""
        try:
            # Phase 1: get prose reasoning
            phase_1_response = call_agent_activity(
                model=model,
                prompt=phase_1_prompt,
                team_view=team_view,
                role=self.role,
                role_memory=role_memory_combined,
                message_history=inbox,
                max_output_tokens=256,
            )
            reasoning = phase_1_response.text.strip()

            # Phase 2: feed phase 1 reasoning as context, get JSON decision
            candidates_line = "candidates: " + ", ".join(candidate_systems)
            phase_2_extra = f"--- PHASE 1 REASONING ---\n{reasoning}\n\n{candidates_line}"
            phase_2_role_memory = (role_memory_combined + "\n\n" + phase_2_extra) if role_memory_combined else phase_2_extra

            phase_2_response = call_agent_activity(
                model=model,
                prompt=phase_2_prompt,
                team_view=team_view,
                role=self.role,
                role_memory=phase_2_role_memory,
                message_history=inbox,
                max_output_tokens=64,
            )

            # Strip markdown code fences if the model wrapped the JSON
            text = phase_2_response.text.strip()
            if text.startswith("```"):
                text = "\n".join(
                    line for line in text.splitlines() if not line.startswith("```")
                ).strip()

            parsed = json.loads(text)
            if isinstance(parsed, dict):
                raw_system = parsed.get("system") or parsed.get("load_system")
                if isinstance(raw_system, str):
                    selected_system = raw_system.strip().lower()
            if selected_system not in candidate_systems:
                raise ValueError(f"model selected an invalid system: {selected_system!r}")
        except Exception:
            selected_system = _preferred_system(team_view)

        return {
            "role": self.role.value,
            "type": "END_TURN",
            "payload": {},
            "reasoning": reasoning,
            "messages": [
                {
                    "recipient": "captain",
                    "text": f"Charge {selected_system} next.",
                    "metadata": {"recommended_system": selected_system},
                }
            ],
        }

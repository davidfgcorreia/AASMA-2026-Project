from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from ..base import AgentBase, AgentRole
from agents.common.functions import call_agent_activity
from captain_sonar.possible_actions import possible_actions_for_role
from captain_sonar.engineer_layout import engineer_button_spec_by_id


ENGINEER_DIR = Path(__file__).resolve().parent

# Safety ranking: lower index = safer to cross
_SAFETY_ORDER = ("green", "yellow", "red", "radioactive")


def _read_engineer_file(*parts: str) -> str:
    path = ENGINEER_DIR.joinpath(*parts)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _extract_json_block(text: str) -> str:
    """Extract the last JSON object from text, handling markdown code fences."""
    matches = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text)
    if matches:
        return matches[-1].strip()
    start = text.rfind("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text.strip()


def _safety_rank(function_type: str) -> int:
    try:
        return _SAFETY_ORDER.index(function_type)
    except ValueError:
        return len(_SAFETY_ORDER)


def _heuristic_button(team_view: dict) -> tuple[str, str]:
    """Return (direction, button_id) for the safest available button heuristically."""
    board = team_view.get("engineer_board", {})
    buttons_by_dir = board.get("buttons_by_direction", {}) if isinstance(board, dict) else {}
    best_dir = "N"
    best_id = None
    best_rank = len(_SAFETY_ORDER) + 1

    for direction, buttons in buttons_by_dir.items():
        if not isinstance(buttons, list):
            continue
        for btn in buttons:
            if not isinstance(btn, dict) or btn.get("crossed", False):
                continue
            rank = _safety_rank(btn.get("function_type", "radioactive"))
            if rank < best_rank:
                best_rank = rank
                best_dir = direction
                best_id = btn.get("button_id")

    return best_dir, best_id


def _resolve_breakdown_choice(button_id: str) -> dict | None:
    spec = engineer_button_spec_by_id(button_id)
    if spec is None:
        return None
    return {
        "button_id": spec.button_id,
        "direction": spec.direction,
        "slot": spec.slot_index,
        "slot_index": spec.slot_index,
        "circuit_part": spec.circuit_part,
        "function_type": spec.function_type,
    }


@dataclass
class EngineerAgent(AgentBase):
    """Engineer role agent — heuristic fallback."""

    def __init__(self, team: str) -> None:
        super().__init__(team=team, role=AgentRole.ENGINEER)

    def act(self, deadline_ms: int) -> dict[str, object]:
        raise NotImplementedError("EngineerAgent logic is not implemented yet.")

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        direction, button_id = _heuristic_button(team_view)
        payload: dict[str, object] = {"direction": direction}
        if button_id:
            bd = _resolve_breakdown_choice(button_id)
            if bd:
                payload["breakdown_choice"] = bd
        return {
            "role": self.role.value,
            "type": "MOVE",
            "payload": payload,
            "reasoning": "heuristic: safest available button",
        }


@dataclass(init=False)
class ModelEngineerAgent(EngineerAgent):
    """Model-driven engineer agent using a 2-phase LLM pipeline.

    Phase 1 — board analysis: the model reviews all available buttons per
               direction, ranks them by safety, and flags warnings (prose).
    Phase 2 — selection: the model outputs per-direction recommendations
               and a surface recommendation flag as JSON.

    The proposal includes a message to the Captain with all recommendations
    so the Captain can pick the correct button for whichever direction it chooses.
    """

    def __init__(self, team: str) -> None:
        super().__init__(team=team)

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        strategy = _read_engineer_file("strategy.md")
        memory = _read_engineer_file("memory.md")
        context = _read_engineer_file("context.md")
        phase_1_prompt = _read_engineer_file("prompts", "1_board_analysis.md")
        phase_2_prompt = _read_engineer_file("prompts", "2_selection.md")

        parts: list[str] = []
        if strategy:
            parts.append("--- STRATEGY ---\n" + strategy)
        if memory:
            parts.append("--- MEMORY ---\n" + memory)
        if context:
            parts.append("--- CONTEXT ---\n" + context)
        role_memory_base = "\n\n".join(parts) if parts else None

        model = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"
        inbox = team_view.get("inbox") or []

        recommendations: dict[str, str] = {}
        repair_recommended = False
        analysis = ""

        try:
            # Phase 1: board analysis (prose)
            p1 = call_agent_activity(
                model=model,
                prompt=phase_1_prompt,
                team_view=team_view,
                role=self.role,
                role_memory=role_memory_base,
                message_history=inbox,
                max_output_tokens=512,
            )
            analysis = p1.text.strip()

            # Phase 2: per-direction selection JSON
            p2_extra = f"--- PHASE 1 ANALYSIS ---\n{analysis}"
            p2_memory = (role_memory_base + "\n\n" + p2_extra) if role_memory_base else p2_extra
            p2 = call_agent_activity(
                model=model,
                prompt=phase_2_prompt,
                team_view=team_view,
                role=self.role,
                role_memory=p2_memory,
                message_history=inbox,
                max_output_tokens=128,
            )

            json_text = _extract_json_block(p2.text.strip())
            parsed = json.loads(json_text)

            raw_recs = parsed.get("recommendations", {})
            if isinstance(raw_recs, dict):
                for d, bid in raw_recs.items():
                    if isinstance(d, str) and isinstance(bid, str):
                        recommendations[d.upper()] = bid

            # accept either legacy `repair_recommended` or newer `surface_recommended`
            repair_recommended = bool(parsed.get("repair_recommended", False) or parsed.get("surface_recommended", False))

        except Exception:
            pass  # fall through to heuristic

        # If SURFACE is recommended, propose surfacing
        if repair_recommended:
            return {
                "role": self.role.value,
                "type": "SURFACE",
                "payload": {},
                "reasoning": analysis,
            }

        # Build recommendation message for the Captain.
        # The Engineer does not propose a MOVE — the Captain is the sole
        # action proposer.  Recommendations are forwarded as a message so
        # the Captain can pick the right button for whichever direction it
        # chooses (effective in multi-iteration mode).
        if recommendations:
            best_dir, best_id = _heuristic_button(team_view)
            for d, bid in recommendations.items():
                spec = engineer_button_spec_by_id(bid)
                if spec is not None:
                    rank = _safety_rank(spec.function_type)
                    current_rank = _safety_rank(
                        (engineer_button_spec_by_id(best_id) or spec).function_type
                    ) if best_id else len(_SAFETY_ORDER)
                    if rank < current_rank:
                        best_dir = d
                        best_id = bid
            rec_lines = ", ".join(f"{d}→{bid}" for d, bid in sorted(recommendations.items()))
            message_text = f"Engineer board recommendations: {rec_lines}"
        else:
            best_dir, best_id = _heuristic_button(team_view)
            message_text = f"Engineer fallback: {best_dir}→{best_id}"

        return {
            "role": self.role.value,
            "type": "END_TURN",
            "payload": {},
            "reasoning": analysis,
            "messages": [
                {
                    "recipient": "captain",
                    "text": message_text,
                    "metadata": {"recommendations": recommendations},
                }
            ],
        }

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from ..base import AgentBase, AgentRole
from agents.common.functions import call_agent_activity
from captain_sonar.possible_actions import possible_actions_for_role


CAPTAIN_DIR = Path(__file__).resolve().parent


def _read_captain_file(*parts: str) -> str:
    path = CAPTAIN_DIR.joinpath(*parts)
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


_MOVE_DELTAS: dict[str, tuple[int, int]] = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
_SYSTEM_PRIORITY = ("torpedo", "sonar", "drone", "silence", "mine")
_BUTTON_SAFETY = ("green", "yellow", "red", "radioactive")


def _valid_directions(team_view: dict) -> set[str]:
    """Return legal move directions — excludes islands AND already-visited cells."""
    possible = possible_actions_for_role("captain", team_view)
    dirs: set[str] = set()
    for action in possible:
        if action.get("action_kind") == "MOVE":
            dirs = {str(d.get("direction", "")) for d in action.get("directions", [])}
            break

    # possible_actions filters islands/bounds but NOT visited cells — filter those here
    own_sub = team_view.get("own_submarine") or {}
    own_routes = team_view.get("own_routes") or []
    visited = {(int(r["x"]), int(r["y"])) for r in own_routes if isinstance(r, dict)}
    x, y = int(own_sub.get("x", 0)), int(own_sub.get("y", 0))

    return {
        d for d in dirs
        if d not in _MOVE_DELTAS
        or (x + _MOVE_DELTAS[d][0], y + _MOVE_DELTAS[d][1]) not in visited
    }


def _fallback_direction(team_view: dict) -> str:
    """Return the first legal move direction (respecting visited cells), or SURFACE."""
    valid = _valid_directions(team_view)
    return next(iter(valid)) if valid else "SURFACE"


def _fallback_system(team_view: dict) -> str | None:
    """Return the next system to charge based on readiness, or None."""
    ready = (team_view.get("system_utilization") or {}).get("ready") or {}
    for sys in _SYSTEM_PRIORITY:
        if not ready.get(sys, False):
            return sys
    return None


def _fallback_button(direction: str, team_view: dict) -> str | None:
    """Return the safest uncrossed engineer button for the given direction."""
    board = team_view.get("engineer_board") or {}
    buttons_by_dir = board.get("buttons_by_direction") or {} if isinstance(board, dict) else {}
    best_id: str | None = None
    best_rank = len(_BUTTON_SAFETY) + 1
    for btn in buttons_by_dir.get(direction, []):
        if not isinstance(btn, dict) or btn.get("crossed", False):
            continue
        try:
            rank = _BUTTON_SAFETY.index(btn.get("function_type", "radioactive"))
        except ValueError:
            rank = len(_BUTTON_SAFETY)
        if rank < best_rank:
            best_rank = rank
            best_id = btn.get("button_id")
    return best_id


@dataclass
class CaptainAgent(AgentBase):
    """Captain role agent placeholder."""

    def __init__(self, team: str) -> None:
        super().__init__(team=team, role=AgentRole.CAPTAIN)

    def act(self, deadline_ms: int) -> dict[str, object]:
        raise NotImplementedError("CaptainAgent logic is not implemented yet.")

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        candidate_actions = possible_actions_for_role(self.role.value, team_view)
        chosen_action = candidate_actions[0] if candidate_actions else {"type": "MOVE", "payload": {"direction": "N"}}
        system_utilization = team_view.get("system_utilization")
        preferred_system = "torpedo"
        if isinstance(system_utilization, dict):
            preferred_system = str(system_utilization.get("preferred_system", preferred_system))
        first_step = chosen_action
        second_step = {
            "type": "SYSTEM",
            "payload": {
                "system": preferred_system,
            },
        }
        return {
            "role": self.role.value,
            "first_step": first_step,
            "second_step": second_step,
            "full_action": chosen_action,
            "possible_actions": candidate_actions,
        }


@dataclass(init=False)
class ModelCaptainAgent(CaptainAgent):
    """Model-driven captain agent using a 3-phase LLM pipeline.

    Phase 1 — analysis: the model reasons about the current game state
               and proposes a direction and system (prose).
    Phase 2 — discussion: the model acts as a consensus facilitator,
               reviewing its own analysis and refining the decision (prose).
    Phase 3 — action: the model outputs a final JSON action that the
               adapter can execute directly.
    """

    def __init__(self, team: str) -> None:
        super().__init__(team=team)

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        # Load all context/prompt files
        strategy = _read_captain_file("strategy.md")
        memory = _read_captain_file("memory.md")
        context = _read_captain_file("context.md")
        action_format = _read_captain_file("action_format.md")
        play_context = _read_captain_file("..", "common", "play_context.md")
        system_instruction = _read_captain_file("system_instruction.md") or None

        phase_1_prompt = _read_captain_file("prompts", "1_analysis.md")
        phase_2_prompt = _read_captain_file("prompts", "2_discussion.md")
        phase_3_prompt = _read_captain_file("prompts", "3_action.md")

        # Build base role memory block
        parts: list[str] = []
        if strategy:
            parts.append("--- STRATEGY ---\n" + strategy)
        if memory:
            parts.append("--- MEMORY ---\n" + memory)
        if context:
            parts.append("--- CONTEXT ---\n" + context)
        if play_context:
            parts.append("--- PLAY CONTEXT ---\n" + play_context)
        if action_format:
            parts.append("--- ACTION FORMAT ---\n" + action_format)

        inbox = team_view.get("inbox") or []
        
        first_mate_suggestion = None
        engineer_suggestions = {}
        radio_operator_suggestion = None

        for msg in inbox:
            sender = msg.get("sender")
            metadata = msg.get("metadata") or {}

            if sender == "first_mate":
                first_mate_suggestion = metadata.get("recommended_system") or first_mate_suggestion
            elif sender == "engineer":
                recs = metadata.get("recommendations") or {}
                if isinstance(recs, dict):
                    engineer_suggestions.update(recs)
            elif sender == "radio_operator":
                radio_operator_suggestion = metadata.get("most_likely_sector") or radio_operator_suggestion
        
        discussion_parts = []
        if first_mate_suggestion:
            discussion_parts.append(f"- **First Mate's Recommended System to Charge**: {first_mate_suggestion}")
        if engineer_suggestions:
            btn_strings = [f"{d} -> {b}" for d, b in sorted(engineer_suggestions.items())]
            discussion_parts.append(f"- **Engineer's Recommended Breakdown Buttons by Direction**:\n  " + "\n  ".join(btn_strings))
        if radio_operator_suggestion:
            discussion_parts.append(f"- **Radio Operator's Estimated Enemy Sector**: Sector {radio_operator_suggestion}")
 
        if discussion_parts:
            crew_discussion_str = "--- CREW DISCUSSION & RECOMMENDATIONS ---\n" + "\n".join(discussion_parts)
            parts.append(crew_discussion_str)
        
        role_memory_base = "\n\n".join(parts) if parts else None

        model = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"

        # Defaults used if any phase fails
        direction = _fallback_direction(team_view)
        load_system: str | None = None
        engineer_button_id: str | None = None
        reasoning = ""

        try:
            # Phase 1: state analysis (prose)
            p1 = call_agent_activity(
                model=model,
                prompt=phase_1_prompt,
                team_view=team_view,
                role=self.role,
                role_memory=role_memory_base,
                message_history=inbox,
                system_instruction=system_instruction,
                max_output_tokens=512,
            )
            analysis = p1.text.strip()

            # Phase 2: discussion and consensus (prose)
            p2_extra = f"--- PHASE 1 ANALYSIS ---\n{analysis}"
            p2_memory = (role_memory_base + "\n\n" + p2_extra) if role_memory_base else p2_extra
            p2 = call_agent_activity(
                model=model,
                prompt=phase_2_prompt,
                team_view=team_view,
                role=self.role,
                role_memory=p2_memory,
                message_history=inbox,
                system_instruction=system_instruction,
                max_output_tokens=512,
            )
            discussion = p2.text.strip()
            reasoning = discussion

            # Phase 3: final action JSON
            p3_extra = (
                f"--- PHASE 1 ANALYSIS ---\n{analysis}\n\n"
                f"--- PHASE 2 DISCUSSION ---\n{discussion}"
            )
            p3_memory = (role_memory_base + "\n\n" + p3_extra) if role_memory_base else p3_extra
            p3 = call_agent_activity(
                model=model,
                prompt=phase_3_prompt,
                team_view=team_view,
                role=self.role,
                role_memory=p3_memory,
                message_history=inbox,
                system_instruction=system_instruction,
                max_output_tokens=256,
            )

            json_text = _extract_json_block(p3.text.strip())
            parsed = json.loads(json_text)

            if isinstance(parsed, dict):
                raw_dir = str(parsed.get("direction", direction)).upper()

                if raw_dir == "SURFACE":
                    direction = raw_dir
                elif raw_dir in ("N", "S", "E", "W"):
                    valid = _valid_directions(team_view)
                    direction = raw_dir if raw_dir in valid else _fallback_direction(team_view)

                load_system = parsed.get("load_system") or None
                engineer_button_id = parsed.get("engineer_button_id") or None

        except Exception:
            pass  # keep fallback values

        # ── Step 1: Hard safety — lock direction before anything else ──────────
        # Must happen first so fallbacks use the *final* direction.
        if direction not in ("SURFACE",):
            valid = _valid_directions(team_view)
            if not valid:
                direction = "SURFACE"
            elif direction not in valid:
                direction = _fallback_direction(team_view)

        # If direction is SURFACE, clear per-move fields immediately.
        if direction == "SURFACE":
            load_system = None
            engineer_button_id = None
        else:
            if load_system:
                load_system=str(load_system).lower().strip()
                if load_system not in _SYSTEM_PRIORITY:
                    load_system = None
            # Discard engineer_button_id if its direction prefix doesn't match.
            if engineer_button_id: 
                engineer_button_id = str(engineer_button_id).strip()
                if not engineer_button_id.upper().startswith(direction + "-"):
                    engineer_button_id = None

        # ── Step 2: Fallback for load_system ─────────────────────────────────
        if not load_system and direction != "SURFACE":
            for msg in inbox:
                if msg.get("sender") == "first_mate":
                    load_system = (msg.get("metadata") or {}).get("recommended_system")
                    if load_system:
                        break
            if not load_system:
                load_system = _fallback_system(team_view)

        # ── Step 3: Fallback for engineer_button_id ───────────────────────────
        if not engineer_button_id and direction not in ("SURFACE",):
            for msg in inbox:
                if msg.get("sender") == "engineer":
                    recs = (msg.get("metadata") or {}).get("recommendations") or {}
                    engineer_button_id = recs.get(direction)
                    if engineer_button_id:
                        break
            if not engineer_button_id:
                engineer_button_id = _fallback_button(direction, team_view)

        # Build the adapter-compatible intent
        action_type = "SURFACE" if direction == "SURFACE" else "MOVE"
        payload: dict[str, object] = {}
        if direction != "SURFACE":
            payload["direction"] = direction
        if load_system:
            payload["charge"] = load_system
        if engineer_button_id:
            from captain_sonar.engineer_layout import engineer_button_spec_by_id
            spec = engineer_button_spec_by_id(engineer_button_id)
            if spec is not None:
                payload["breakdown_choice"] = {
                    "button_id": spec.button_id,
                    "direction": spec.direction,
                    "slot": spec.slot_index,
                    "slot_index": spec.slot_index,
                    "circuit_part": spec.circuit_part,
                    "function_type": spec.function_type,
                }

        return {
            "role": self.role.value,
            "type": action_type,
            "payload": payload,
            "reasoning": reasoning,
        }

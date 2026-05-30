from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from ..base import AgentBase, AgentRole
from agents.common.functions import call_agent_activity


RADIO_OP_DIR = Path(__file__).resolve().parent

# Sector grid constants mirroring captain_sonar.config
_SECTOR_ROWS = 2
_SECTOR_COLS = 3


def _read_ro_file(*parts: str) -> str:
    path = RADIO_OP_DIR.joinpath(*parts)
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


def _sector_for_position(x: int, y: int, map_width: int, map_height: int) -> int:
    """Compute the 1-indexed sector number for grid position (x, y)."""
    row = min(_SECTOR_ROWS - 1, (y * _SECTOR_ROWS) // max(1, map_height))
    col = min(_SECTOR_COLS - 1, (x * _SECTOR_COLS) // max(1, map_width))
    return row * _SECTOR_COLS + col + 1


# ── Lie detection threshold ────────────────────────────────────────────────────
# If the piece labeled "true" by the enemy has less than this fraction of the
# combined belief mass (true_mass / (true_mass + false_mass)), we flag a lie.
_LIE_MASS_THRESHOLD = 0.25


def _compute_constraint_mass(
    info: dict,
    belief: list,
    map_height: int,
    map_width: int,
) -> float:
    """Return the total belief probability mass that satisfies a sonar info constraint."""
    if not isinstance(info, dict):
        return 0.0
    itype = info.get("type")
    value = info.get("value")
    total = 0.0
    for y in range(map_height):
        if y >= len(belief):
            break
        for x in range(map_width):
            row = belief[y]
            if not isinstance(row, list) or x >= len(row):
                continue
            p = float(row[x])
            if p <= 0.0:
                continue
            if itype == "sector" and isinstance(value, int):
                if _sector_for_position(x, y, map_width, map_height) == value:
                    total += p
            elif itype == "row" and isinstance(value, str) and value:
                if chr(ord("A") + y) == value[0].upper():
                    total += p
            elif itype == "col" and isinstance(value, int):
                if (x + 1) == value:
                    total += p
    return total


def _detect_sonar_lie(
    events: list,
    own_team: str,
    belief: list,
    map_height: int,
    map_width: int,
) -> dict:
    """Determine whether the enemy lied in their most recent sonar response.

    Checks: if the piece the enemy labeled as ``true_info`` has very low
    probability mass in our current belief map (built from heard moves, drones,
    and surface events) compared to the ``false_info`` piece, they probably
    swapped the labels to mislead us.

    Returns a dict with keys:
        enemy_lied (bool), confidence (float 0-1),
        likely_actual_sector (int|None), reasoning (str)
    """
    _no_lie = {
        "enemy_lied": False,
        "confidence": 0.0,
        "likely_actual_sector": None,
        "reasoning": "no sonar events",
    }

    # Find the most recent sonar event where our team queried
    sonar_event: dict | None = None
    for event in reversed(events if isinstance(events, list) else []):
        if isinstance(event, dict) and event.get("type") == "sonar" and event.get("actor") == own_team:
            sonar_event = event
            break

    if sonar_event is None:
        return _no_lie

    true_info = sonar_event.get("true_info") or sonar_event.get("info_1")
    false_info = sonar_event.get("false_info") or sonar_event.get("info_2")

    if not isinstance(true_info, dict) or not isinstance(false_info, dict):
        return {**_no_lie, "reasoning": "sonar event missing info pieces"}

    true_mass = _compute_constraint_mass(true_info, belief, map_height, map_width)
    false_mass = _compute_constraint_mass(false_info, belief, map_height, map_width)
    combined = true_mass + false_mass

    if combined <= 0.0:
        return {**_no_lie, "reasoning": "belief map empty — cannot assess"}

    true_ratio = true_mass / combined

    if true_ratio < _LIE_MASS_THRESHOLD:
        # The "true" piece has very low mass → enemy likely swapped labels
        actual_sector: int | None = None
        if isinstance(false_info.get("type"), str) and false_info.get("type") == "sector":
            v = false_info.get("value")
            if isinstance(v, int):
                actual_sector = v

        confidence = round(min(1.0, 1.0 - true_ratio), 2)
        return {
            "enemy_lied": True,
            "confidence": confidence,
            "likely_actual_sector": actual_sector,
            "reasoning": (
                f"labeled true_info {true_info} covers only {true_ratio:.0%} of "
                f"belief mass vs false_info {false_info} at {(false_mass/combined):.0%}; "
                f"labels likely swapped"
            ),
        }

    return {
        **_no_lie,
        "reasoning": f"true_info {true_info} covers {true_ratio:.0%} of belief mass — consistent",
    }


def _compute_best_false_sector(own_sector: int | None, sector_masses: dict) -> int | None:
    """Pick the best false sector to claim when the enemy queries our sonar.

    Strategy: return the sector with the HIGHEST enemy-belief probability mass
    that is not our actual sector.  This is maximally plausible to the enemy
    while being wrong.  Falls back to the first sector != own_sector.
    """
    if own_sector is None:
        return None
    # Sort by mass descending, take first entry that isn't our sector
    for sector, _ in sorted(sector_masses.items(), key=lambda kv: kv[1], reverse=True):
        if sector != own_sector:
            return sector
    # Fallback: any other sector
    for candidate in range(1, 7):
        if candidate != own_sector:
            return candidate
    return None


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.7:
        return "HIGH"
    if confidence >= 0.4:
        return "MEDIUM"
    return "LOW"


def _best_drone_sector(sector_masses: dict) -> int | None:
    """Return the sector with the highest probability mass."""
    if not sector_masses:
        return None
    return max(sector_masses, key=lambda s: sector_masses[s])


def _format_pos(pos: dict | None) -> str:
    if pos is None:
        return "unknown"
    return f"({pos['x']},{pos['y']})"


@dataclass
class RadioOperatorAgent(AgentBase):
    """Radio operator role agent — heuristic intel reporter.

    Does not propose a game-engine action (END_TURN is a safe no-op that will
    be omitted by voting).  All value is delivered through messages to the
    Captain and First Mate, which the iteration orchestrator dispatches before
    voting occurs.
    """

    def __init__(self, team: str) -> None:
        super().__init__(team=team, role=AgentRole.RADIO_OPERATOR)

    def act(self, deadline_ms: int) -> dict[str, object]:
        raise NotImplementedError("RadioOperatorAgent.act() is not implemented.")

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        radio: dict = team_view.get("radio_operator") or {}

        most_likely_pos: dict | None = radio.get("most_likely_position")
        most_likely_sector: int | None = radio.get("most_likely_sector")
        confidence: float = float(radio.get("confidence") or 0.0)
        sector_masses: dict = radio.get("sector_probability_masses") or {}
        possible_positions: list = radio.get("possible_current_positions") or []
        heard_moves: list = radio.get("heard_moves") or []

        conf_label = _confidence_label(confidence)
        pos_str = _format_pos(most_likely_pos)
        sector_str = str(most_likely_sector) if most_likely_sector is not None else "unknown"
        move_tail = heard_moves[-6:] if heard_moves else []
        move_summary = ",".join(move_tail) if move_tail else "none"

        # Recommend sensor: drone if we have a sector target, else sonar
        best_sector = _best_drone_sector(sector_masses)
        if best_sector is not None:
            recommended_sensor = "drone"
            sensor_detail = f"sector {best_sector}"
        else:
            recommended_sensor = "sonar"
            sensor_detail = "no sector locked yet"

        # Captain message: full intel summary
        narrowed = len(possible_positions)
        captain_text = (
            f"Enemy ~{pos_str} sector {sector_str} "
            f"[conf {conf_label} {confidence:.0%}]. "
            f"Last moves: {move_summary}. "
            f"Search space: {narrowed} cell(s). "
            f"Best sensor: {recommended_sensor} {sensor_detail}."
        )

        # First Mate message: sensor charge recommendation only
        first_mate_text = (
            f"Charge {recommended_sensor} ({sensor_detail}). "
            f"Enemy confidence {conf_label}."
        )

        reasoning = (
            f"Enemy {pos_str} sector {sector_str} conf {conf_label} "
            f"({narrowed} possible cells, {len(heard_moves)} moves heard)."
        )

        return {
            "role": self.role.value,
            "type": "END_TURN",
            "payload": {},
            "reasoning": reasoning,
            "messages": [
                {
                    "recipient": "captain",
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
                    "recipient": "first_mate",
                    "text": first_mate_text,
                    "metadata": {
                        "recommended_sensor": recommended_sensor,
                        "best_sector": best_sector,
                    },
                },
            ],
        }


@dataclass(init=False)
class ModelRadioOperatorAgent(RadioOperatorAgent):
    """Model-driven Radio Operator agent using a 2-phase LLM pipeline.

    Phase 1 — analysis: the model reviews the belief state, heard-move
               trajectory, and all sonar events to assess whether the enemy
               is lying in their sonar responses and to recommend a false
               sonar sector for our own deceptive responses (prose).

    Phase 2 — decision: the model outputs a JSON object containing the lie
               assessment, recommended false sector, sensor recommendation,
               and best enemy position estimate.

    The proposal includes:
    - A message to the Captain with enemy intel + lie detection assessment.
    - A message to the First Mate with sensor charge recommendation.
    """

    def __init__(self, team: str) -> None:
        super().__init__(team=team)

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        # ── Shared data extraction ────────────────────────────────────────────
        radio: dict = team_view.get("radio_operator") or {}
        most_likely_pos: dict | None = radio.get("most_likely_position")
        most_likely_sector: int | None = radio.get("most_likely_sector")
        confidence: float = float(radio.get("confidence") or 0.0)
        sector_masses: dict = radio.get("sector_probability_masses") or {}
        possible_positions: list = radio.get("possible_current_positions") or []
        heard_moves: list = radio.get("heard_moves") or []
        belief: list = radio.get("belief") or []

        own_sub: dict = team_view.get("own_submarine") or {}
        map_info: dict = team_view.get("map") or {}
        own_x = int(own_sub.get("x") or 0)
        own_y = int(own_sub.get("y") or 0)
        map_w = int(map_info.get("width") or 15)
        map_h = int(map_info.get("height") or 10)
        events: list = team_view.get("events") or []
        own_team: str = str(team_view.get("team") or "")

        # ── Deterministic computations (no LLM needed) ───────────────────────

        # Lie detection: compare sonar true_info mass against belief map
        lie_assessment = _detect_sonar_lie(events, own_team, belief, map_h, map_w)

        # False sector recommendation: pick the most plausible enemy sector
        # that is NOT our actual sector
        own_sector = _sector_for_position(own_x, own_y, map_w, map_h)
        recommended_lie_sector: int | None = _compute_best_false_sector(own_sector, sector_masses)

        # Sensor heuristic
        conf_label = _confidence_label(confidence)
        pos_str = _format_pos(most_likely_pos)
        sector_str = str(most_likely_sector) if most_likely_sector is not None else "unknown"
        move_tail = heard_moves[-6:] if heard_moves else []
        move_summary = ",".join(move_tail) if move_tail else "none"
        narrowed = len(possible_positions)

        best_sector = _best_drone_sector(sector_masses)
        if best_sector is not None:
            recommended_sensor = "drone"
            sensor_detail = f"sector {best_sector}"
        else:
            recommended_sensor = "sonar"
            sensor_detail = "no sector locked yet"

        # ── LLM phase: tactical reasoning + sensor recommendation ─────────────
        strategy = _read_ro_file("strategy.md")
        memory = _read_ro_file("memory.md")
        context = _read_ro_file("context.md")
        system_instruction = _read_ro_file("system_instruction.md") or None
        phase_1_prompt = _read_ro_file("prompts", "1_analysis.md")
        phase_2_prompt = _read_ro_file("prompts", "2_action.md")

        parts: list[str] = []
        if strategy:
            parts.append("--- STRATEGY ---\n" + strategy)
        if memory:
            parts.append("--- MEMORY ---\n" + memory)
        if context:
            parts.append("--- CONTEXT ---\n" + context)
        # Inject pre-computed lie result so the LLM has it available as context
        lie_summary = (
            f"--- LIE DETECTION (pre-computed) ---\n"
            f"enemy_lied={lie_assessment['enemy_lied']}  "
            f"confidence={lie_assessment['confidence']:.2f}  "
            f"likely_actual_sector={lie_assessment.get('likely_actual_sector')}\n"
            f"reasoning: {lie_assessment['reasoning']}\n"
            f"recommended_lie_sector={recommended_lie_sector}"
        )
        parts.append(lie_summary)
        role_memory_base = "\n\n".join(parts) if parts else None

        model = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"
        inbox = team_view.get("inbox") or []
        analysis = ""

        try:
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
        except Exception:
            pass

        try:
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
                max_output_tokens=256,
            )
            json_text = _extract_json_block(p2.text.strip())
            parsed = json.loads(json_text)

            if isinstance(parsed, dict):
                # LLM may refine the sensor recommendation
                raw_sensor = str(parsed.get("recommended_sensor") or recommended_sensor).lower()
                if raw_sensor in ("sonar", "drone", "none"):
                    recommended_sensor = raw_sensor
                    if recommended_sensor == "none":
                        sensor_detail = "none needed"
                    elif raw_sensor == "sonar":
                        target = (parsed.get("sonar_recommendation") or {}).get("target_sector") or best_sector
                        sensor_detail = f"sector {target}"
                    else:
                        sensor_detail = f"sector {parsed.get('best_sector') or best_sector}"

                raw_sector = parsed.get("most_likely_sector")
                if isinstance(raw_sector, int):
                    most_likely_sector = raw_sector
                    sector_str = str(most_likely_sector)

                raw_pos = parsed.get("most_likely_position")
                if isinstance(raw_pos, dict):
                    most_likely_pos = raw_pos
                    pos_str = _format_pos(most_likely_pos)

                raw_best = parsed.get("best_sector")
                if isinstance(raw_best, int):
                    best_sector = raw_best

        except Exception:
            pass

        # ── Build messages ───────────────────────────────────────────────────
        lie_flag = ""
        if lie_assessment["enemy_lied"]:
            lie_conf = lie_assessment["confidence"]
            likely_sec = lie_assessment.get("likely_actual_sector")
            lie_flag = (
                f" !! LIE DETECTED (conf {lie_conf:.0%})"
                + (f", likely in sector {likely_sec}" if likely_sec else "")
                + "."
            )

        captain_text = (
            f"Enemy ~{pos_str} sector {sector_str} "
            f"[conf {conf_label} {confidence:.0%}]. "
            f"Last moves: {move_summary}. "
            f"Search space: {narrowed} cell(s). "
            f"Best sensor: {recommended_sensor} {sensor_detail}."
            f"{lie_flag}"
        )
        if recommended_lie_sector:
            captain_text += f" If queried by enemy sonar, claim false sector {recommended_lie_sector}."

        first_mate_text = (
            f"Charge {recommended_sensor} ({sensor_detail}). "
            f"Enemy confidence {conf_label}."
        )

        reasoning = (
            f"Enemy {pos_str} sector {sector_str} conf {conf_label} "
            f"({narrowed} possible cells, {len(heard_moves)} moves heard)."
            + (" Lie detected." if lie_assessment["enemy_lied"] else "")
        )

        return {
            "role": self.role.value,
            "type": "END_TURN",
            "payload": {},
            "reasoning": reasoning,
            "messages": [
                {
                    "recipient": "captain",
                    "text": captain_text,
                    "metadata": {
                        "most_likely_position": most_likely_pos,
                        "most_likely_sector": most_likely_sector,
                        "confidence": confidence,
                        "possible_count": narrowed,
                        "recommended_sensor": recommended_sensor,
                        "best_sector": best_sector,
                        "lie_assessment": lie_assessment,
                        "recommended_lie_sector": recommended_lie_sector,
                    },
                },
                {
                    "recipient": "first_mate",
                    "text": first_mate_text,
                    "metadata": {
                        "recommended_sensor": recommended_sensor,
                        "best_sector": best_sector,
                    },
                },
            ],
        }

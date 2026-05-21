from __future__ import annotations

from dataclasses import dataclass

from ..base import AgentBase, AgentRole


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

from __future__ import annotations

import json
import math
import os
import time
from typing import Any, Dict

from .belief_tracker import BeliefTracker
from .config import GAUGE_MAX_DEFAULT, SYSTEM_SYMBOLS_MAP
from .engineer_layout import ENGINEER_BUTTON_SPECS, engineer_button_spec_by_id
from .game_state import BreakdownState, GameState

DAMAGE_WEIGHT = 5.0
BELIEF_SECTOR_WEIGHT = 15.0
ENEMY_BELIEF_PENALTY_WEIGHT = 12.0
BELIEF_SCORE_CAP = 10.0

NOT_CIRCUIT_PENALTY = -3.0
CIRCUIT_CLEAR_BONUS = 4.0
CIRCUIT_PROGRESS_BONUS = 2.0
CIRCUIT_OTHER_PENALTY = -1.0

SYSTEM_LOAD_BONUS = 1.0
SYSTEM_LOAD_READY_BONUS = 2.0

TORPEDO_MINE_MAX_DAMAGE_BONUS = 5.0
TORPEDO_MINE_DAMAGE_BONUS = 3.0
TORPEDO_MINE_MISS_PENALTY = -2.0

DRONE_BASE_BONUS = 1.0
DRONE_HIT_BONUS = 3.0
DRONE_MISS_PENALTY = -1.0

SILENCE_BONUS = 2.0
SONAR_BONUS = 2.0


def evaluate_turn(
    state: GameState,
    belief_blue: BeliefTracker,
    belief_red: BeliefTracker,
    previous: dict[str, Any] | None,
    *,
    log_path: str = "logs/game_results.jsonl",
) -> dict[str, Any]:
    teams = list(state.subs.keys())
    belief_by_team = {
        "BLUE": belief_blue,
        "RED": belief_red,
    }

    team_scores: dict[str, dict[str, Any]] = {}
    for team in teams:
        enemy = _enemy_of(teams, team)
        own_damage = state.subs[team].damage
        enemy_damage = state.subs[enemy].damage if enemy else 0

        belief_tracker = belief_by_team.get(team)
        belief_stats = _belief_stats(belief_tracker) if belief_tracker else _blank_belief_stats()

        enemy_belief = belief_by_team.get(enemy) if enemy else None
        enemy_belief_stats = _belief_stats(enemy_belief) if enemy_belief else _blank_belief_stats()

        breakdown = state.breakdowns.get(team)
        crossed_buttons = _crossed_button_count(breakdown)

        previous_team = (previous or {}).get("teams", {}).get(team, {})
        previous_components = previous_team.get("components", {})
        previous_breakdowns = (previous or {}).get("breakdowns", {}).get(team, {})
        previous_gauges = (previous or {}).get("gauges", {}).get(team, {})

        belief_score = _clamp(
            belief_stats["max_sector_probability"] * BELIEF_SECTOR_WEIGHT
            - enemy_belief_stats["max_sector_probability"] * ENEMY_BELIEF_PENALTY_WEIGHT,
            -BELIEF_SCORE_CAP,
            BELIEF_SCORE_CAP,
        )

        engineer_score = _engineer_score(
            breakdown,
            previous_breakdowns,
            state.events,
            team,
        )

        system_load_score = _system_load_score(
            state,
            team,
            previous_gauges,
            breakdown,
        )

        activation_score = _activation_score(state.events, team, enemy)

        score = (
            (enemy_damage - own_damage) * DAMAGE_WEIGHT
            + belief_score
            + engineer_score
            + system_load_score
            + activation_score
        )

        components = {
            "enemy_damage": enemy_damage,
            "own_damage": own_damage,
            "belief_max_sector_probability": belief_stats["max_sector_probability"],
            "belief_entropy": belief_stats["entropy"],
            "enemy_belief_max_sector_probability": enemy_belief_stats["max_sector_probability"],
            "belief_score": belief_score,
            "engineer_score": engineer_score,
            "system_load_score": system_load_score,
            "activation_score": activation_score,
            "crossed_buttons": crossed_buttons,
        }

        previous_score = previous_team.get("score")

        deltas = {
            "score": _delta(score, previous_score),
            "enemy_damage": _delta(components["enemy_damage"], previous_components.get("enemy_damage")),
            "own_damage": _delta(components["own_damage"], previous_components.get("own_damage")),
            "belief_max_sector_probability": _delta(
                components["belief_max_sector_probability"],
                previous_components.get("belief_max_sector_probability"),
            ),
            "belief_entropy": _delta(
                components["belief_entropy"],
                previous_components.get("belief_entropy"),
            ),
            "enemy_belief_max_sector_probability": _delta(
                components["enemy_belief_max_sector_probability"],
                previous_components.get("enemy_belief_max_sector_probability"),
            ),
            "belief_score": _delta(components["belief_score"], previous_components.get("belief_score")),
            "engineer_score": _delta(components["engineer_score"], previous_components.get("engineer_score")),
            "system_load_score": _delta(components["system_load_score"], previous_components.get("system_load_score")),
            "activation_score": _delta(components["activation_score"], previous_components.get("activation_score")),
            "crossed_buttons": _delta(components["crossed_buttons"], previous_components.get("crossed_buttons")),
        }

        team_scores[team] = {
            "score": score,
            "components": components,
            "deltas": deltas,
        }

    leader = _determine_leader(team_scores)

    result = {
        "turn": state.turn,
        "timestamp": time.time(),
        "teams": team_scores,
        "leader": leader,
        "breakdowns": _breakdown_snapshot(state),
        "gauges": _gauges_snapshot(state),
    }

    _write_log_entry(log_path, result)
    return result


def _enemy_of(teams: list[str], team: str) -> str | None:
    for candidate in teams:
        if candidate != team:
            return candidate
    return None


def _crossed_button_count(breakdown: BreakdownState | None) -> int:
    if not breakdown:
        return 0
    return sum(len(buttons) for buttons in breakdown.crossed_by_direction.values())


def _belief_stats(belief_tracker: BeliefTracker) -> dict[str, float]:
    heatmap = belief_tracker.heatmap()
    max_prob = 0.0
    entropy = 0.0
    for row in heatmap:
        for value in row:
            try:
                p = float(value)
            except (TypeError, ValueError):
                continue
            if p > max_prob:
                max_prob = p
            if p > 0.0:
                entropy -= p * math.log(p)
    sector_masses = belief_tracker.sector_masses()
    max_sector = max(sector_masses.values()) if sector_masses else 0.0
    return {
        "max_probability": max_prob,
        "max_sector_probability": max_sector,
        "entropy": entropy,
    }


def _blank_belief_stats() -> dict[str, float]:
    return {"max_probability": 0.0, "max_sector_probability": 0.0, "entropy": 0.0}


def _determine_leader(team_scores: dict[str, dict[str, Any]]) -> str | None:
    if not team_scores:
        return None
    sorted_scores = sorted(team_scores.items(), key=lambda item: item[1]["score"], reverse=True)
    if len(sorted_scores) < 2:
        return sorted_scores[0][0]
    if sorted_scores[0][1]["score"] == sorted_scores[1][1]["score"]:
        return None
    return sorted_scores[0][0]


def _delta(current: float, previous: float | None) -> float | None:
    if previous is None:
        return None
    return current - previous


def _clamp(value: float, low: float, high: float) -> float:
    if value < low:
        return low
    if value > high:
        return high
    return value


def _breakdown_snapshot(state: GameState) -> dict[str, dict[str, list[str]]]:
    snapshot: dict[str, dict[str, list[str]]] = {}
    for team, breakdown in state.breakdowns.items():
        if not breakdown:
            snapshot[team] = {"W": [], "N": [], "S": [], "E": []}
            continue
        snapshot[team] = {
            direction: sorted(list(buttons))
            for direction, buttons in breakdown.crossed_by_direction.items()
        }
    return snapshot


def _gauges_snapshot(state: GameState) -> dict[str, dict[str, int]]:
    return {team: dict(gauges) for team, gauges in state.gauges.items()}


def _system_has_breakdown(breakdown: BreakdownState | None, system: str) -> bool:
    if not breakdown:
        return False
    color = SYSTEM_SYMBOLS_MAP.get(system)
    if color is None:
        return False
    for crossed in breakdown.crossed_by_direction.values():
        for button_id in crossed:
            spec = engineer_button_spec_by_id(button_id)
            if spec and spec.function_type == color:
                return True
    return False


def _engineer_score(
    breakdown: BreakdownState | None,
    previous_breakdowns: dict[str, list[str]],
    events: list[dict[str, Any]],
    team: str,
) -> float:
    score = 0.0
    if not breakdown:
        return score

    previous_crossed = _crossed_from_snapshot(previous_breakdowns)
    current_crossed = set().union(*breakdown.crossed_by_direction.values())
    newly_crossed = current_crossed - previous_crossed

    previous_counts = _circuit_part_counts(previous_crossed)

    for button_id in newly_crossed:
        spec = engineer_button_spec_by_id(button_id)
        if spec is None:
            continue
        if spec.circuit_part == "not":
            score += NOT_CIRCUIT_PENALTY
            continue
        prior_count = previous_counts.get(spec.circuit_part, 0)
        if prior_count >= 2:
            score += CIRCUIT_PROGRESS_BONUS
        else:
            score += CIRCUIT_OTHER_PENALTY

    for event in events:
        if event.get("type") != "circuit_self_repair" or event.get("actor") != team:
            continue
        circuits = event.get("circuits")
        if isinstance(circuits, list):
            score += CIRCUIT_CLEAR_BONUS * len(circuits)

    return score


def _crossed_from_snapshot(snapshot: dict[str, list[str]]) -> set[str]:
    if not snapshot:
        return set()
    crossed: set[str] = set()
    for buttons in snapshot.values():
        if isinstance(buttons, list):
            crossed.update(buttons)
    return crossed


def _circuit_part_counts(buttons: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for button_id in buttons:
        spec = engineer_button_spec_by_id(button_id)
        if spec is None:
            continue
        if spec.circuit_part in ("top", "central", "down"):
            counts[spec.circuit_part] = counts.get(spec.circuit_part, 0) + 1
    return counts


def _system_load_score(
    state: GameState,
    team: str,
    previous_gauges: dict[str, int],
    breakdown: BreakdownState | None,
) -> float:
    score = 0.0
    gauges = state.gauges.get(team, {})
    for system, current in gauges.items():
        previous = previous_gauges.get(system)
        if previous is None:
            continue
        if current <= previous:
            continue
        if _system_has_breakdown(breakdown, system):
            continue
        if current >= GAUGE_MAX_DEFAULT:
            score += SYSTEM_LOAD_READY_BONUS
        else:
            score += SYSTEM_LOAD_BONUS
    return score


def _activation_score(events: list[dict[str, Any]], team: str, enemy: str | None) -> float:
    score = 0.0
    for event in events:
        etype = event.get("type")
        actor = event.get("actor")
        if actor != team:
            continue
        if etype == "silence":
            score += SILENCE_BONUS
        elif etype == "sonar":
            score += SONAR_BONUS
        elif etype == "drone":
            response = event.get("response")
            score += DRONE_BASE_BONUS
            if response is True:
                score += DRONE_HIT_BONUS
            elif response is False:
                score += DRONE_MISS_PENALTY

    for event in events:
        if event.get("type") != "explosion":
            continue
        if event.get("owner") != team:
            continue
        if event.get("source") not in {"torpedo", "mine"}:
            continue
        hits = event.get("hits", [])
        enemy_damage = None
        if isinstance(hits, list) and enemy:
            for hit in hits:
                if isinstance(hit, dict) and hit.get("team") == enemy:
                    enemy_damage = hit.get("damage")
                    break
        if enemy_damage == 2:
            score += TORPEDO_MINE_MAX_DAMAGE_BONUS
        elif enemy_damage == 1:
            score += TORPEDO_MINE_DAMAGE_BONUS
        else:
            score += TORPEDO_MINE_MISS_PENALTY

    return score


def _write_log_entry(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")

"""Simple strategy selector for TeamAgentManager.

This module implements a lightweight, deterministic strategy selector used
to choose an initial strategy profile and per-role directives based on the
team, map features and operating mode. The selector is intentionally
small and easily testable; it is meant to be replaced or extended with a
more sophisticated planner if needed.
"""

from __future__ import annotations

from typing import Any
from captain_sonar.map_loader import MapData
from .models import TeamOperatingMode


def select_strategy(team: str, map_data: MapData, mode: TeamOperatingMode, override: str | None = None) -> dict[str, Any]:
    """Return a simple strategy profile dict.

    The profile contains an `id` string and a `directives` mapping from
    role name to a short directive string.
    """
    if override:
        profile_id = str(override)
    else:
        area = map_data.width * map_data.height
        if area <= 16:
            profile_id = "stealth"
        elif area <= 36:
            profile_id = "aggressive"
        else:
            profile_id = "balanced"

    base_directives = {
        "captain": "preserve options; prefer safe moves",
        "first_mate": "keep torpedo/sonar ready",
        "engineer": "minimize breakdown risk",
        "radio_operator": "narrow enemy belief quickly",
    }

    if profile_id == "stealth":
        overlay = {
            "captain": "prioritize silence and concealment",
            "first_mate": "favor silence and mine readiness",
            "engineer": "choose safer buttons",
            "radio_operator": "deprioritize aggressive targeting",
        }
    elif profile_id == "aggressive":
        overlay = {
            "captain": "seek torpedo opportunities",
            "first_mate": "charge offensive systems",
            "engineer": "accept higher breakdown risk for power",
            "radio_operator": "focus on precise targeting info",
        }
    else:
        overlay = {}

    directives = {role: (overlay.get(role, base_directives.get(role, ""))) for role in base_directives}

    # Adapt directives for THREE_AGENT mode where captain may be human
    if mode == TeamOperatingMode.THREE_AGENT:
        directives["captain"] = "human_controlled: coordinate when asked"

    return {"id": profile_id, "team": team, "directives": directives}

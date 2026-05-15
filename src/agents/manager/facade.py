"""Runtime facade composing TeamAgentManager and the API adapter.

This module provides a lightweight integration surface for external game
loops that want to advance the team manager through a single turn step and
obtain the resulting execution record and state snapshot.
"""

from __future__ import annotations

from typing import Any
from captain_sonar.game_state import GameState

from .manager import TeamAgentManager


class TeamRuntimeFacade:
    """Compose a manager for use by an external game loop.

    Example usage:
        facade = TeamRuntimeFacade(manager)
        report = facade.step(state, max_iterations=2)

    The returned dict matches the manager `run_turn_cycle` return value.
    """

    def __init__(self, manager: TeamAgentManager) -> None:
        self.manager = manager

    def step(self, state: GameState, deadline_ms: int | None = None, max_iterations: int = 1) -> dict[str, Any]:
        return self.manager.run_turn_cycle(state, deadline_ms=deadline_ms, max_iterations=max_iterations)

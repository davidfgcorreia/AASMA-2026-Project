from __future__ import annotations

from pathlib import Path
from typing import Mapping

from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import load_map

from ..captain.agent import CaptainAgent, ModelCaptainAgent
from ..engineer.agent import EngineerAgent, ModelEngineerAgent
from ..first_mate.agent import FirstMateAgent, ModelFirstMateAgent
from ..radio_operator.agent import RadioOperatorAgent
from .manager import TeamAgentManager
from .models import AgentManagerConfig


def build_team_agent_manager(
    team: str,
    *,
    config: AgentManagerConfig | None = None,
    use_model_agents: bool = False,
) -> TeamAgentManager:
    """Create a manager pre-wired with the default four role agents."""
    manager = TeamAgentManager(team, config=config)

    captain = ModelCaptainAgent(team) if use_model_agents else CaptainAgent(team)
    first_mate = ModelFirstMateAgent(team) if use_model_agents else FirstMateAgent(team)

    engineer = ModelEngineerAgent(team) if use_model_agents else EngineerAgent(team)

    manager.register_agent(captain, active=True)
    manager.register_agent(first_mate, active=True)
    manager.register_agent(engineer, active=True)
    manager.register_agent(RadioOperatorAgent(team), active=True)
    return manager


def build_game_state(map_path: str | Path, starts: Mapping[str, tuple[int, int]]) -> GameState:
    """Create a game state from map path and initial submarine coordinates."""
    map_data = load_map(str(map_path))
    subs = {
        team: SubmarineState(x=int(position[0]), y=int(position[1]))
        for team, position in starts.items()
    }
    return GameState(map_data=map_data, subs=subs)


def start_team_turn(
    manager: TeamAgentManager,
    state: GameState,
    *,
    max_iterations: int = 1,
    deadline_ms: int | None = None,
) -> dict[str, object]:
    """Run one manager proposal/execution cycle for the current turn."""
    return manager.run_turn_cycle(state, max_iterations=max_iterations, deadline_ms=deadline_ms)


__all__ = [
    "build_team_agent_manager",
    "build_game_state",
    "start_team_turn",
]

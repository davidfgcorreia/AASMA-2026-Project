from __future__ import annotations

from dataclasses import dataclass

from agents.base import AgentBase, AgentRole
from agents.manager import AgentManagerConfig, TeamAgentManager
from agents.manager.iteration_orchestrator import run_iteration_cycle
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import MapData


@dataclass
class MockAgent(AgentBase):
    next_proposal: dict | None = None

    def __init__(self, team: str, role: AgentRole, next_proposal: dict | None = None) -> None:
        super().__init__(team=team, role=role)
        self.next_proposal = next_proposal or {"type": "MOVE", "payload": {"direction": "N"}}

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        return dict(self.next_proposal)

    def act(self, deadline_ms: int) -> dict[str, object]:
        return dict(self.next_proposal or {})


def _build_state() -> GameState:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    return GameState(
        map_data=map_data,
        subs={"BLUE": SubmarineState(x=1, y=1), "RED": SubmarineState(x=2, y=2)},
    )


def test_run_iteration_cycle_collects_proposals() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig())
    manager.register_agent(MockAgent("BLUE", AgentRole.CAPTAIN), active=True)
    manager.register_agent(MockAgent("BLUE", AgentRole.ENGINEER), active=True)

    state = _build_state()

    # prepare manager turn context
    manager.begin_turn(state)
    manager.observe(state)

    iterations = run_iteration_cycle(manager, state, max_iterations=1)

    assert len(iterations) >= 1
    first = iterations[0]
    assert isinstance(first["proposals"], dict)
    assert "captain" in first["proposals"] and "engineer" in first["proposals"]
    # manager should have recorded proposals in its internal ledger structures
    assert manager._turn_action_proposals


def test_run_iteration_cycle_delivers_messages() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig())
    manager.register_agent(MockAgent("BLUE", AgentRole.FIRST_MATE), active=True)
    manager.register_agent(MockAgent("BLUE", AgentRole.ENGINEER), active=True)

    # FIRST_MATE will send a message to ENGINEER
    fm_prop = {"type": "MOVE", "payload": {}, "messages": [{"recipient": "engineer", "text": "TestMsg", "metadata": {}}]}
    manager._agents[AgentRole.FIRST_MATE].next_proposal = fm_prop

    state = _build_state()
    manager.begin_turn(state)
    manager.observe(state)

    iterations = run_iteration_cycle(manager, state, max_iterations=1)
    first = iterations[0]
    engineer_inbox = first["inbox"].get("engineer", [])
    assert any(m.get("text") == "TestMsg" for m in engineer_inbox)

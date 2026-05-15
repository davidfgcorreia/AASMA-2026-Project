from __future__ import annotations

from dataclasses import dataclass

from agents.base import AgentBase, AgentRole
from agents.manager import AgentManagerConfig, TeamAgentManager
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


def test_run_turn_cycle_collects_iteration_and_resolves() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig())
    manager.register_agent(MockAgent("BLUE", AgentRole.CAPTAIN), active=True)
    # FIRST_MATE will send a message to ENGINEER as part of its proposal
    fm_proposal = {"type": "MOVE", "payload": {"direction": "E"}, "messages": [{"recipient": "engineer", "text": "Align to bearing 3", "metadata": {"urgency": 1}}]}
    manager.register_agent(MockAgent("BLUE", AgentRole.FIRST_MATE, next_proposal=fm_proposal), active=True)
    manager.register_agent(MockAgent("BLUE", AgentRole.ENGINEER), active=True)

    state = _build_state()

    manager.activate_agents(state, roles=[AgentRole.CAPTAIN, AgentRole.FIRST_MATE, AgentRole.ENGINEER], duration_ms=10)

    report = manager.run_turn_cycle(state, max_iterations=1)

    assert "iterations" in report and len(report["iterations"]) >= 1
    assert "accepted" in report
    assert all(isinstance(it["proposals"], dict) for it in report["iterations"])

    # Ensure the message from FIRST_MATE reached ENGINEER's inbox in the iteration snapshot
    first_it = report["iterations"][0]
    engineer_inbox = first_it["inbox"].get("engineer", [])
    assert any(msg.get("text") == "Align to bearing 3" for msg in engineer_inbox)

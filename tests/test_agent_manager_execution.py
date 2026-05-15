from __future__ import annotations

from agents.base import AgentBase, AgentRole
from agents.manager import AgentManagerConfig, TeamAgentManager
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import MapData


class ProposalAgent(AgentBase):
    def __init__(self, team: str, role: AgentRole, proposal: dict[str, object]) -> None:
        super().__init__(team=team, role=role)
        self.proposal = proposal

    def propose_action(self, team_view: dict[str, object]) -> dict[str, object]:
        return dict(self.proposal)

    def act(self, deadline_ms: int) -> dict[str, object]:
        return dict(self.proposal)


def _build_state() -> GameState:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    return GameState(
        map_data=map_data,
        subs={"BLUE": SubmarineState(x=1, y=1), "RED": SubmarineState(x=2, y=2)},
    )


def test_execute_turn_actions_collapses_consensus_to_one_team_action() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig())
    manager.register_agent(ProposalAgent("BLUE", AgentRole.CAPTAIN, {"type": "MOVE", "payload": {"direction": "N"}}), active=True)
    manager.register_agent(ProposalAgent("BLUE", AgentRole.FIRST_MATE, {"type": "MOVE", "payload": {"direction": "N"}}), active=True)

    state = _build_state()
    manager.activate_agents(state, roles=[AgentRole.CAPTAIN, AgentRole.FIRST_MATE], duration_ms=10)

    execution = manager.execute_turn_actions(
        state,
        [
            {"role": "captain", "turn_id": 0, "type": "MOVE", "payload": {"direction": "N"}},
            {"role": "first_mate", "turn_id": 0, "type": "MOVE", "payload": {"direction": "N"}},
        ],
    )

    assert execution["success"] is True
    assert execution["turn_id"] == 0
    assert len(execution["accepted_intents"]) == 2
    assert len(execution["executed_actions"]) == 1
    assert execution["executed_actions"][0]["actor"] == "BLUE"
    assert state.subs["BLUE"].x == 1
    assert state.subs["BLUE"].y == 0
    assert state.turn == 1


def test_execute_turn_actions_rejects_invalid_intent_before_execution() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig())
    manager.register_agent(ProposalAgent("BLUE", AgentRole.CAPTAIN, {"type": "MOVE", "payload": {"direction": "N"}}), active=True)

    state = _build_state()
    manager.activate_agents(state, roles=[AgentRole.CAPTAIN], duration_ms=10)

    execution = manager.execute_turn_actions(
        state,
        [
            {"role": "captain", "turn_id": 99, "type": "MOVE", "payload": {"direction": "N"}},
        ],
    )

    assert execution["success"] is False
    assert execution["executed_actions"] == []
    assert execution["rejected_intents"]
    assert any("turn_id" in error for error in execution["rejected_intents"][0]["errors"])
    assert state.subs["BLUE"].x == 1
    assert state.subs["BLUE"].y == 1


def test_run_turn_cycle_includes_execution_report() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig())
    manager.register_agent(ProposalAgent("BLUE", AgentRole.CAPTAIN, {"type": "MOVE", "payload": {"direction": "N"}}), active=True)
    manager.register_agent(ProposalAgent("BLUE", AgentRole.FIRST_MATE, {"type": "MOVE", "payload": {"direction": "N"}}), active=True)

    state = _build_state()
    manager.activate_agents(state, roles=[AgentRole.CAPTAIN, AgentRole.FIRST_MATE], duration_ms=10)

    report = manager.run_turn_cycle(state, max_iterations=1)

    assert "execution" in report
    assert report["execution"]["success"] is True
    assert report["execution"]["executed_actions"]

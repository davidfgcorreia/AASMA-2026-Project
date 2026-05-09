from __future__ import annotations

from dataclasses import dataclass

from agents.base import AgentBase, AgentRole
from agents.manager import AgentManagerConfig, TeamAgentManager
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import MapData


@dataclass
class DummyAgent(AgentBase):
    next_action: dict[str, object] | None = None

    def __init__(self, team: str, role: AgentRole, next_action: dict[str, object] | None = None) -> None:
        super().__init__(team=team, role=role)
        self.next_action = next_action or {"role": role.value, "action": "noop"}

    def act(self, deadline_ms: int) -> dict[str, object]:
        return dict(self.next_action or {})


def _build_state() -> GameState:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    return GameState(
        map_data=map_data,
        subs={"BLUE": SubmarineState(x=1, y=1), "RED": SubmarineState(x=2, y=2)},
    )


def test_manager_observes_and_collects_active_roles() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig(max_messages_per_turn=2, max_messages_per_pair_per_turn=1))
    manager.register_agent(DummyAgent("BLUE", AgentRole.CAPTAIN), active=True)
    manager.register_agent(DummyAgent("BLUE", AgentRole.FIRST_MATE), active=True)
    manager.register_agent(DummyAgent("BLUE", AgentRole.ENGINEER), active=False)
    manager.register_agent(DummyAgent("BLUE", AgentRole.RADIO_OPERATOR), active=True)

    state = _build_state()
    manager.observe(state)

    captain_view = manager.agents[AgentRole.CAPTAIN].last_observation
    engineer_view = manager.role_view(AgentRole.ENGINEER)

    assert captain_view["role"] == "captain"
    assert captain_view["team"] == "BLUE"
    assert engineer_view["engineer_board"] is not None
    assert "radio_operator" in manager.role_view(AgentRole.RADIO_OPERATOR)

    actions = manager.collect_actions(deadline_ms=100)
    assert set(actions) == {AgentRole.CAPTAIN, AgentRole.FIRST_MATE, AgentRole.RADIO_OPERATOR}


def test_manager_enforces_message_limits() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig(max_messages_per_turn=1, max_messages_per_pair_per_turn=1))
    manager.register_agent(DummyAgent("BLUE", AgentRole.CAPTAIN), active=True)
    manager.register_agent(DummyAgent("BLUE", AgentRole.FIRST_MATE), active=True)

    state = _build_state()
    manager.observe(state)

    first = manager.send_message(AgentRole.CAPTAIN, AgentRole.FIRST_MATE, "status")
    second = manager.send_message(AgentRole.CAPTAIN, AgentRole.FIRST_MATE, "blocked")

    assert first is True
    assert second is False
    assert len(manager.read_inbox(AgentRole.FIRST_MATE)) == 1
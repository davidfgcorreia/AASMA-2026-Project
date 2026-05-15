from __future__ import annotations

from dataclasses import dataclass

import pytest

from agents.base import AgentBase, AgentRole
from agents.manager import AgentManagerConfig, TeamAgentManager, TeamOperatingMode
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import MapData


@dataclass
class DummyAgent(AgentBase):
    def __init__(self, team: str, role: AgentRole) -> None:
        super().__init__(team=team, role=role)

    def act(self, deadline_ms: int) -> dict[str, object]:
        return {"role": self.role.value, "type": "MOVE", "payload": {"direction": "N"}}


def _build_state() -> GameState:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    return GameState(
        map_data=map_data,
        subs={"BLUE": SubmarineState(x=1, y=1), "RED": SubmarineState(x=2, y=2)},
    )


def test_activate_agents_and_choose_turn_actions() -> None:
    manager = TeamAgentManager("BLUE", config=AgentManagerConfig(activation_duration_ms=1))
    manager.register_agent(DummyAgent("BLUE", AgentRole.CAPTAIN), active=False)
    manager.register_agent(DummyAgent("BLUE", AgentRole.FIRST_MATE), active=False)
    state = _build_state()

    manager.activate_agents(state, roles=[AgentRole.CAPTAIN, AgentRole.FIRST_MATE], duration_ms=10, until_actions_chosen=True)

    assert manager.active_roles == {AgentRole.CAPTAIN, AgentRole.FIRST_MATE}
    assert manager.is_activation_active() is True

    manager.propose_turn_action(AgentRole.CAPTAIN, {"type": "MOVE", "payload": {"direction": "N"}})
    manager.propose_turn_action(AgentRole.FIRST_MATE, {"type": "MOVE", "payload": {"direction": "N"}})

    accepted = manager.choose_turn_actions()

    assert len(accepted) == 2
    assert accepted[0]["type"] == "MOVE"
    assert manager.turn_action_status()["proposals"]


def test_majority_omits_non_consensus_actions() -> None:
    manager = TeamAgentManager("BLUE")
    manager.register_agent(DummyAgent("BLUE", AgentRole.CAPTAIN), active=False)
    manager.register_agent(DummyAgent("BLUE", AgentRole.FIRST_MATE), active=False)
    manager.register_agent(DummyAgent("BLUE", AgentRole.ENGINEER), active=False)
    state = _build_state()
    manager.activate_agents(state, until_actions_chosen=False)

    manager.propose_turn_action(AgentRole.CAPTAIN, {"type": "MOVE", "payload": {"direction": "N"}})
    manager.omit_turn_action(AgentRole.FIRST_MATE)
    manager.omit_turn_action(AgentRole.ENGINEER)

    accepted = manager.choose_turn_actions()

    assert accepted == []


def test_full_team_mode_activates_all_registered_roles() -> None:
    manager = TeamAgentManager(
        "BLUE",
        config=AgentManagerConfig(operating_mode=TeamOperatingMode.FULL_TEAM),
    )
    manager.register_agent(DummyAgent("BLUE", AgentRole.CAPTAIN), active=False)
    manager.register_agent(DummyAgent("BLUE", AgentRole.FIRST_MATE), active=False)
    manager.register_agent(DummyAgent("BLUE", AgentRole.ENGINEER), active=False)
    manager.register_agent(DummyAgent("BLUE", AgentRole.RADIO_OPERATOR), active=False)
    state = _build_state()

    manager.activate_agents(state)

    assert manager.active_roles == {
        AgentRole.CAPTAIN,
        AgentRole.FIRST_MATE,
        AgentRole.ENGINEER,
        AgentRole.RADIO_OPERATOR,
    }


def test_three_agent_mode_disables_configured_role() -> None:
    manager = TeamAgentManager(
        "BLUE",
        config=AgentManagerConfig(
            operating_mode=TeamOperatingMode.THREE_AGENT,
        ),
    )
    manager.register_agent(DummyAgent("BLUE", AgentRole.FIRST_MATE), active=False)
    manager.register_agent(DummyAgent("BLUE", AgentRole.ENGINEER), active=False)
    manager.register_agent(DummyAgent("BLUE", AgentRole.RADIO_OPERATOR), active=False)
    state = _build_state()

    manager.activate_agents(state, roles=[AgentRole.FIRST_MATE])

    assert manager.active_roles == {
        AgentRole.FIRST_MATE,
        AgentRole.ENGINEER,
        AgentRole.RADIO_OPERATOR,
    }
    assert AgentRole.CAPTAIN not in manager.active_roles


def test_three_agent_mode_rejects_non_captain_human_role() -> None:
    with pytest.raises(ValueError, match="human role"):
        TeamAgentManager(
            "BLUE",
            config=AgentManagerConfig(
                operating_mode=TeamOperatingMode.THREE_AGENT,
                human_role=AgentRole.ENGINEER,
            ),
        )
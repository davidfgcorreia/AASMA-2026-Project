from __future__ import annotations

from typing import Any, List, Mapping, Optional, TypedDict

import pygame
from agents.manager import TeamAgentManager

from .actions import Action, ActionType, order_actions
from .api import get_team_view
from .possible_actions import possible_actions_for_role
from .config import DEFAULT_SEED, FPS
from .event_log import EventLogger
from .game_state import GameState
from .human_controller import HumanController
from .sonar_response_modal import SonarResponseModal
from .renderer import Renderer
from .belief_tracker import BeliefTracker
from .turn_evaluation import evaluate_turn

from agents.manager.pipeline_helpers import manager_api as manager_api

TEAM_HUMAN = "human"
TEAM_AGENT = "agent"


class _AgentActionCache(TypedDict):
    turn: Optional[int]
    actions: Optional[list[Action | None]]


class GameLoop:
    def __init__(
        self,
        state: GameState,
        renderer: Renderer,
        logger: EventLogger | None = None,
        seed: int = DEFAULT_SEED,
        map_name: str = "unknown",
        team_play_types: Mapping[str, str] | None = None,
        agent_managers: Mapping[str, TeamAgentManager] | None = None,
    ) -> None:
        self.state = state
        self.renderer = renderer
        self.logger = logger
        self.clock = pygame.time.Clock()
        normalized_play_types = {
            "BLUE": TEAM_HUMAN,
            "RED": TEAM_HUMAN,
        }
        if team_play_types:
            for team in ("BLUE", "RED"):
                value = team_play_types.get(team, TEAM_HUMAN)
                normalized_play_types[team] = str(value).strip().lower()

        self.team_play_types = normalized_play_types
        self.agent_managers = dict(agent_managers or {})
        self.human_blue = HumanController("BLUE") if not self._is_agent_team("BLUE") else None
        self.human_red = HumanController("RED") if not self._is_agent_team("RED") else None
        # Two separate belief trackers: one for each team's belief about opponent
        self.belief_blue = BeliefTracker(state.map_data, own_team="BLUE")  # Blue's belief about Red
        self.belief_red = BeliefTracker(state.map_data, own_team="RED")    # Red's belief about Blue
        self.sonar_modal = SonarResponseModal(state)
        self._last_turn_start_logged: tuple[int, str] | None = None
        self._last_turn_evaluation: dict[str, Any] | None = None
        if self.logger:
            subs = {team: {"x": sub.x, "y": sub.y} for team, sub in state.subs.items()}
            self.logger.log_header({"map": map_name, "seed": seed, "teams": list(state.subs.keys()), "subs": subs})

    def _record_turn(self, actions: list[Action], acting_team: str) -> None:
        if not self.logger:
            return
        self.logger.log_turn(self.state.turn, actions, self.state.events)

    def _log_turn_start(self, team: str, phase: str) -> None:
        if not self.logger or phase != "move" or self.state.skip_turns.get(team, 0) > 0:
            return
        key = (self.state.turn, team)
        if self._last_turn_start_logged == key:
            return
        team_view = get_team_view(self.state, team)
        self.logger.log_team_view(self.state.turn, team, team_view)
        self.logger.log_turn_start(self.state.turn, team, phase)
        team_view = get_team_view(self.state, team)
        possible_actions = possible_actions_for_role("captain", team_view)
        self.logger.log_possible_actions(self.state.turn, team, phase, "captain", possible_actions)
        self._last_turn_start_logged = key

    def run(self) -> None:
        running = True
        active_team = "BLUE"  # Start with BLUE team
        phase_by_team = {"BLUE": "move", "RED": "move"}
        cached_agent_actions: dict[str, _AgentActionCache] = {
            "BLUE": {"turn": None, "actions": None},
            "RED": {"turn": None, "actions": None},
        }
        while running:
            active_controller = self.human_blue if active_team == "BLUE" else self.human_red
            active_phase = phase_by_team.get(active_team, "move")
            self._log_turn_start(active_team, active_phase)


            # zona do sonar integrar com os agents para pedir respostar e analizar resposta 


            # nao esquecer que o pedido de resposate é dado depois de um ativar sonar  e que a reposta é mostrada a quem pedio o sonar no inicio da sua ronda seguinte

            # render das respostas na faze seguinte 

            if self.sonar_modal.active:
                waiting_team = self.sonar_modal.waiting_team
                if waiting_team is None:
                    continue
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    else:
                        committed_action = self.sonar_modal.handle_event(event)
                        if committed_action is not None:
                            attacker_team = committed_action.actor
                            self._apply_actions([committed_action], advance_turn=True)
                            self._record_turn([committed_action], attacker_team)
                            phase_by_team[attacker_team] = "move"
                            active_team = self._other_team(attacker_team)
                            break

                if not self.sonar_modal.active:
                    continue

                modal_controller = self.human_blue if waiting_team == "BLUE" else self.human_red
                ui_state = modal_controller.ui_state() if modal_controller else {}
                ui_state["active_team"] = waiting_team
                ui_state["turn_phase"] = "sonar_response"
                active_belief = self.belief_blue if waiting_team == "BLUE" else self.belief_red
                cursor = ui_state.get("cursor")
                if isinstance(cursor, (list, tuple)) and len(cursor) >= 2:
                    ui_state["belief_prob"] = active_belief.probability_at(cursor[0], cursor[1])
                ui_state["belief_heatmap"] = active_belief.heatmap()
                ui_state["belief_best_sector"] = active_belief.most_likely_sector()
                ui_state["belief_best_cell"] = active_belief.most_likely_cell()

                self.renderer.draw(self.state, ui_state)
                self.sonar_modal.render(self.renderer)
                pygame.display.flip()
                self.clock.tick(FPS)
                continue



            if self._is_agent_team(active_team) and not self.state.game_over:
                acting_team = active_team
                if self.state.skip_turns.get(active_team, 0) > 0:
                    self._apply_actions([], advance_turn=True)
                    self.state.skip_turns[active_team] = max(0, self.state.skip_turns.get(active_team, 0) - 1)
                    phase_by_team[active_team] = "move"
                    cached_agent_actions[active_team] = {"turn": None, "actions": None}
                    if self.state.skip_turns.get(active_team, 0) > 0:
                        active_team = "RED" if active_team == "BLUE" else "BLUE"
                    continue
                cached = cached_agent_actions.get(active_team, {"turn": None, "actions": None})
                actions_by_phase: Optional[list[Action | None]] = None
                if active_phase == "move":
                    actions_by_phase = self._choose_agent_actions(active_team)
                    cached_agent_actions[active_team] = {"turn": self.state.turn, "actions": actions_by_phase}
                else:
                    cached_turn = cached.get("turn")
                    cached_actions = cached.get("actions")
                    if cached_turn == self.state.turn and cached_actions is not None:
                        actions_by_phase = cached_actions
                    else:
                        actions_by_phase = self._choose_agent_actions(active_team)
                        cached_agent_actions[active_team] = {"turn": self.state.turn, "actions": actions_by_phase}
                move_action = actions_by_phase[0] if actions_by_phase else None
                system_action = actions_by_phase[1] if len(actions_by_phase) > 1 else None
                sonar_action = system_action if system_action and system_action.type == ActionType.SONAR else None
                if active_phase == "move":
                    move_actions = [move_action] if move_action is not None else []
                    advance_turn = bool(move_action and move_action.type == ActionType.SURFACE)
                    self._apply_actions(move_actions, advance_turn=advance_turn)
                    self._record_turn(move_actions, active_team)
                    if advance_turn:
                        phase_by_team[active_team] = "move"
                        active_team = "RED" if active_team == "BLUE" else "BLUE"
                        cached_agent_actions[acting_team] = {"turn": None, "actions": None}
                    else:
                        phase_by_team[active_team] = "system"
                else:
                    if sonar_action is not None:
                        defending_team = self._other_team(active_team)
                        if self._is_agent_team(defending_team):
                            # Agent-vs-agent sonar: ask the defending manager for
                            # its false_type / false_value before applying.
                            def_manager = self.agent_managers.get(defending_team)
                            if def_manager is not None:
                                # Pass the attacker's belief about the defending team
                                # so the agent can lie with a plausible position.
                                attacker_belief = (
                                    self.belief_blue if defending_team == "RED"
                                    else self.belief_red
                                ).heatmap()
                                response = manager_api.get_sonar_response(
                                    def_manager, sonar_action, self.state,
                                    attacker_belief=attacker_belief,
                                )
                                sonar_action.payload.update(response)
                            self._apply_actions([sonar_action], advance_turn=True)
                            self._record_turn([sonar_action], active_team)
                        else:
                            # Defending team is human: show the UI modal.
                            self.sonar_modal.start(sonar_action, defending_team)
                    else:
                        system_actions = [system_action] if system_action is not None else []
                        self._apply_actions(system_actions, advance_turn=True)
                        self._record_turn(system_actions, active_team)
                    phase_by_team[active_team] = "move"
                    active_team = "RED" if active_team == "BLUE" else "BLUE"
                    cached_agent_actions[acting_team] = {"turn": None, "actions": None}
                continue
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif active_controller:
                    active_controller.handle_event(event, self.state.map_data, self.state)
            
            if active_controller:
                active_controller.update_cursor(pygame.mouse.get_pos(), self.state.map_data)
            
            # Auto-advance surfaced teams without waiting for input.
            if not self.state.game_over and self.state.skip_turns.get(active_team, 0) > 0:
                self._apply_actions([], advance_turn=True)
                self._record_turn([], active_team)
                if active_controller is not None:
                    active_controller.reset_turn()
                self.state.skip_turns[active_team] = max(0, self.state.skip_turns.get(active_team, 0) - 1)
                phase_by_team[active_team] = "move"
                if self.state.skip_turns.get(active_team, 0) > 0:
                    active_team = "RED" if active_team == "BLUE" else "BLUE"

            # Resolve the active team's current phase when confirmed.
            elif active_controller and active_controller.confirmed and not self.state.game_over:
                phase_handled = False
                if active_phase == "move":
                    if self._is_valid_move_phase_queue(active_controller.queue):
                        actions = order_actions(list(active_controller.queue))
                        advance_turn = bool(actions and actions[0].type == ActionType.SURFACE)
                        self._apply_actions(actions, advance_turn=advance_turn)
                        self._record_turn(actions, active_team)
                        active_controller.reset_turn()
                        # Surfacing ends the whole turn — skip system phase.
                        if advance_turn:
                            phase_by_team[active_team] = "move"
                            active_team = "RED" if active_team == "BLUE" else "BLUE"
                        else:
                            phase_by_team[active_team] = "system"
                        phase_handled = True
                else:
                    if self._is_valid_system_phase_queue(active_controller.queue):
                        actions = order_actions(list(active_controller.queue))
                        sonar_action = next((action for action in actions if action.type == ActionType.SONAR), None)
                        if (
                            sonar_action is not None
                            and self._can_start_sonar_response(active_team)
                            and not self._is_agent_team(self._other_team(active_team))
                        ):
                            self.sonar_modal.start(sonar_action, self._other_team(active_team))
                            active_controller.reset_turn()
                            phase_by_team[active_team] = "move"
                            phase_handled = True
                        elif (
                            sonar_action is not None
                            and self._can_start_sonar_response(active_team)
                            and self._is_agent_team(self._other_team(active_team))
                        ):
                            # Human fires sonar, defending team is an agent:
                            # ask the defending manager for its false_type / false_value.
                            defending_team = self._other_team(active_team)
                            def_manager = self.agent_managers.get(defending_team)
                            if def_manager is not None:
                                attacker_belief = (
                                    self.belief_blue if defending_team == "RED"
                                    else self.belief_red
                                ).heatmap()
                                response = manager_api.get_sonar_response(
                                    def_manager, sonar_action, self.state,
                                    attacker_belief=attacker_belief,
                                )
                                sonar_action.payload.update(response)
                            self._apply_actions([sonar_action], advance_turn=True)
                            self._record_turn([sonar_action], active_team)
                            active_controller.reset_turn()
                            phase_by_team[active_team] = "move"
                            active_team = self._other_team(active_team)
                            phase_handled = True
                        elif sonar_action is not None and not self._can_start_sonar_response(active_team):
                            active_controller.confirmed = False
                        else:
                            self._apply_actions(actions, advance_turn=True)
                            self._record_turn(actions, active_team)
                            active_controller.reset_turn()
                            phase_by_team[active_team] = "move"
                            active_team = "RED" if active_team == "BLUE" else "BLUE"
                            phase_handled = True

                if not phase_handled:
                    active_controller.confirmed = False
            
            # Get UI state from active team
            ui_state = active_controller.ui_state() if active_controller else {}
            ui_state["active_team"] = active_team
            ui_state["turn_phase"] = phase_by_team.get(active_team, "move")
            ui_state["team"] = active_team
            
            # Use the correct belief tracker for the active team
            active_belief = self.belief_blue if active_team == "BLUE" else self.belief_red
            
            cursor = ui_state.get("cursor")
            if isinstance(cursor, (list, tuple)) and len(cursor) >= 2:
                ui_state["belief_prob"] = active_belief.probability_at(cursor[0], cursor[1])

            ui_state["belief_heatmap"] = active_belief.heatmap()
            ui_state["belief_best_sector"] = active_belief.most_likely_sector()
            ui_state["belief_best_cell"] = active_belief.most_likely_cell()
            
            self.renderer.draw(self.state, ui_state)
            
            # Draw sonar response menu if active
            self.sonar_modal.render(self.renderer)
            
            pygame.display.flip()
            self.clock.tick(FPS)

    def _is_agent_team(self, team: str) -> bool:
        return self.team_play_types.get(team, TEAM_HUMAN) == TEAM_AGENT

    def _other_team(self, team: str) -> str:
        return "RED" if team == "BLUE" else "BLUE"

    def _choose_agent_actions(self, team: str) -> list[Action | None]:
        manager = self.agent_managers.get(team)
        if manager is None:
            return [None, None]
        try:
            actions = manager_api.collect_actions(manager, self.state)
            return self._split_actions_by_phase(actions)
        except NotImplementedError:
            return [None, None]

    def _split_actions_by_phase(self, actions: list[Action]) -> list[Action | None]:
        move_action = next(
            (action for action in actions if action.type in (ActionType.MOVE, ActionType.SURFACE)),
            None,
        )
        system_action = next(
            (
                action
                for action in actions
                if action.type
                in (
                    ActionType.SILENCE,
                    ActionType.TORPEDO,
                    ActionType.SONAR,
                    ActionType.DRONE,
                    ActionType.MINE,
                    ActionType.TRIGGER_MINE,
                )
            ),
            None,
        )
        return [move_action, system_action]

    def _apply_actions(self, actions: list[Action], *, advance_turn: bool) -> None:
        self.state.apply_actions(order_actions(actions), increment_turn=advance_turn)
        self.belief_blue.update(self.state.events)
        self.belief_red.update(self.state.events)
        if advance_turn:
            self._last_turn_evaluation = evaluate_turn(
                self.state,
                self.belief_blue,
                self.belief_red,
                self._last_turn_evaluation,
                log_path="logs/game_results.jsonl",
            )

    def _is_valid_move_phase_queue(self, queue: List[Action]) -> bool:
        if len(queue) != 1:
            return False
        return queue[0].type in (ActionType.MOVE, ActionType.SURFACE)

    def _is_valid_system_phase_queue(self, queue: List[Action]) -> bool:
        if len(queue) > 1:
            return False
        if not queue:
            return True
        return queue[0].type in (
            ActionType.SILENCE,
            ActionType.TORPEDO,
            ActionType.SONAR,
            ActionType.DRONE,
            ActionType.MINE,
            ActionType.TRIGGER_MINE,
        )

    def _can_start_sonar_response(self, team: str) -> bool:
        if not self.state.system_ready(team, "sonar"):
            return False
        if self.state.last_action_system.get(team, False):
            return False
        return not self.state._system_has_breakdown(team, "sonar")






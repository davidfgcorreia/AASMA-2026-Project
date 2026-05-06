from __future__ import annotations

import random
from typing import List

import pygame

from .actions import Action, ActionType, order_actions
from .ai_placeholders import choose_actions
from .config import DEFAULT_SEED, FPS
from .event_log import EventLogger
from .game_state import GameState
from .human_controller import HumanController
from .renderer import Renderer
from .belief_tracker import BeliefTracker


class GameLoop:
    def __init__(
        self,
        state: GameState,
        renderer: Renderer,
        logger: EventLogger | None = None,
        seed: int = DEFAULT_SEED,
        map_name: str = "unknown",
        two_human_teams: bool = True,
    ) -> None:
        self.state = state
        self.renderer = renderer
        self.logger = logger
        self.clock = pygame.time.Clock()
        self.human_blue = HumanController(team="BLUE")
        self.human_red = HumanController(team="RED") if two_human_teams else None
        self.two_human_teams = two_human_teams
        self.rng = random.Random(seed)
        # Two separate belief trackers: one for each team's belief about opponent
        self.belief_blue = BeliefTracker(state.map_data, own_team="BLUE")  # Blue's belief about Red
        self.belief_red = BeliefTracker(state.map_data, own_team="RED")    # Red's belief about Blue
        if self.logger:
            subs = {team: {"x": sub.x, "y": sub.y} for team, sub in state.subs.items()}
            self.logger.log_header({"map": map_name, "seed": seed, "teams": list(state.subs.keys()), "subs": subs})

    def run(self) -> None:
        running = True
        active_team = "BLUE"  # Start with BLUE team
        phase_by_team = {"BLUE": "move", "RED": "move"}
        while running:
            active_controller = self.human_blue if active_team == "BLUE" else self.human_red
            active_phase = phase_by_team.get(active_team, "move")

            if not self.two_human_teams and active_team == "RED" and not self.state.game_over:
                actions = order_actions(choose_actions("RED", self.rng, self.state))
                self.state.apply_actions(actions)
                self.belief_blue.update(self.state.events)
                self.belief_red.update(self.state.events)
                if self.logger:
                    self.logger.log_turn(self.state.turn, actions, self.state.events)
                active_team = "BLUE"
                phase_by_team["RED"] = "move"
                continue
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif active_controller:
                    active_controller.handle_event(event, self.state.map_data)
            
            if active_controller:
                active_controller.update_cursor(pygame.mouse.get_pos(), self.state.map_data)
            
            # Resolve the active team's current phase when confirmed.
            if active_controller and active_controller.confirmed and not self.state.game_over:
                phase_handled = False
                if active_phase == "move":
                    if self._is_valid_move_phase_queue(active_controller.queue):
                        actions = order_actions(list(active_controller.queue))
                        self.state.apply_actions(actions)
                        self.belief_blue.update(self.state.events)
                        self.belief_red.update(self.state.events)
                        if self.logger:
                            self.logger.log_turn(self.state.turn, actions, self.state.events)
                        active_controller.reset_turn()
                        phase_by_team[active_team] = "system"
                        phase_handled = True
                else:
                    if self._is_valid_system_phase_queue(active_controller.queue):
                        actions = order_actions(list(active_controller.queue))
                        self.state.apply_actions(actions)
                        self.belief_blue.update(self.state.events)
                        self.belief_red.update(self.state.events)
                        if self.logger:
                            self.logger.log_turn(self.state.turn, actions, self.state.events)
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
            
            # Use the correct belief tracker for the active team
            active_belief = self.belief_blue if active_team == "BLUE" else self.belief_red
            
            cursor = ui_state.get("cursor")
            if cursor is not None:
                ui_state["belief_prob"] = active_belief.probability_at(cursor[0], cursor[1])

            ui_state["belief_heatmap"] = active_belief.heatmap()
            ui_state["belief_best_sector"] = active_belief.most_likely_sector()
            ui_state["belief_best_cell"] = active_belief.most_likely_cell()
            
            self.renderer.draw(self.state, ui_state)
            pygame.display.flip()
            self.clock.tick(FPS)

    def _collect_actions(self) -> List[Action]:
        actions = list(self.human_blue.queue)
        if self.human_red:
            # Two human teams
            actions.extend(self.human_red.queue)
        else:
            # RED is AI
            actions.extend(choose_actions("RED", self.rng, self.state))
        return actions

    def _is_valid_move_phase_queue(self, queue: List[Action]) -> bool:
        if len(queue) != 1:
            return False
        return queue[0].type in (ActionType.MOVE, ActionType.SILENCE)

    def _is_valid_system_phase_queue(self, queue: List[Action]) -> bool:
        if len(queue) > 1:
            return False
        if not queue:
            return True
        return queue[0].type in (
            ActionType.TORPEDO,
            ActionType.SONAR,
            ActionType.DRONE,
            ActionType.MINE,
            ActionType.TRIGGER_MINE,
            ActionType.REPAIR,
            ActionType.SURFACE,
        )

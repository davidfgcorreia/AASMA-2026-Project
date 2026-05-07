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
        self.belief = BeliefTracker(state.map_data)
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
                if self.state.skip_turns.get("RED", 0) > 0:
                    self.state.apply_actions([])
                    self.belief.update(self.state.events)
                    self.state.skip_turns["RED"] = max(0, self.state.skip_turns.get("RED", 0) - 1)
                    phase_by_team["RED"] = "move"
                    if self.state.skip_turns.get("RED", 0) > 0:
                        active_team = "BLUE"
                    continue
                actions = order_actions(choose_actions("RED", self.rng, self.state, active_phase))
                self.state.apply_actions(actions)
                self.belief.update(self.state.events)
                if self.logger:
                    self.logger.log_turn(self.state.turn, actions, self.state.events)
                if active_phase == "move":
                    if self._team_just_surfaced("RED"):
                        phase_by_team["RED"] = "move"
                        active_team = "BLUE"
                    else:
                        phase_by_team["RED"] = "system"
                else:
                    phase_by_team["RED"] = "move"
                    active_team = "BLUE"
                continue
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif active_controller:
                    active_controller.handle_event(event, self.state.map_data)
            
            if active_controller:
                active_controller.update_cursor(pygame.mouse.get_pos(), self.state.map_data)
            
            # Auto-advance surfaced teams without waiting for input.
            if not self.state.game_over and self.state.skip_turns.get(active_team, 0) > 0:
                self.state.apply_actions([])
                self.belief.update(self.state.events)
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
                        self.state.apply_actions(actions)
                        self.belief.update(self.state.events)
                        if self.logger:
                            self.logger.log_turn(self.state.turn, actions, self.state.events)
                        active_controller.reset_turn()
                        # Surfacing ends the whole turn — skip system phase.
                        if self._team_just_surfaced(active_team):
                            phase_by_team[active_team] = "move"
                            active_team = "RED" if active_team == "BLUE" else "BLUE"
                        else:
                            phase_by_team[active_team] = "system"
                        phase_handled = True
                else:
                    if self._is_valid_system_phase_queue(active_controller.queue):
                        actions = order_actions(list(active_controller.queue))
                        self.state.apply_actions(actions)
                        self.belief.update(self.state.events)
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
            
            cursor = ui_state.get("cursor")
            if cursor is not None:
                ui_state["belief_prob"] = self.belief.probability_at(cursor[0], cursor[1])
            
            self.renderer.draw(self.state, ui_state)
            pygame.display.flip()
            self.clock.tick(FPS)

    def _team_just_surfaced(self, team: str) -> bool:
        return any(e.get("type") == "surface" and e.get("actor") == team for e in self.state.events)

    def _is_valid_move_phase_queue(self, queue: List[Action]) -> bool:
        if len(queue) != 1:
            return False
        return queue[0].type in (ActionType.MOVE, ActionType.SILENCE, ActionType.SURFACE)

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
        )

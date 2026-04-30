from __future__ import annotations

import random
from typing import List

import pygame

from .actions import Action, order_actions
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
    ) -> None:
        self.state = state
        self.renderer = renderer
        self.logger = logger
        self.clock = pygame.time.Clock()
        self.human = HumanController(team="BLUE")
        self.rng = random.Random(seed)
        self.belief = BeliefTracker(state.map_data)
        if self.logger:
            subs = {team: {"x": sub.x, "y": sub.y} for team, sub in state.subs.items()}
            self.logger.log_header({"map": map_name, "seed": seed, "teams": list(state.subs.keys()), "subs": subs})

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.human.handle_event(event, self.state.map_data)
            self.human.update_cursor(pygame.mouse.get_pos(), self.state.map_data)
            if self.human.confirmed and not self.state.game_over:
                actions = order_actions(self._collect_actions())
                self.state.apply_actions(actions)
                self.belief.update(self.state.events)
                if self.logger:
                    self.logger.log_turn(self.state.turn, actions, self.state.events)
                self.human.reset_turn()
            ui_state = self.human.ui_state()
            cursor = ui_state.get("cursor")
            if cursor is not None:
                ui_state["belief_prob"] = self.belief.probability_at(cursor[0], cursor[1])
            self.renderer.draw(self.state, ui_state)
            pygame.display.flip()
            self.clock.tick(FPS)

    def _collect_actions(self) -> List[Action]:
        actions = list(self.human.queue)
        actions.extend(choose_actions("RED", self.rng, self.state))
        return actions

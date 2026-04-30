from __future__ import annotations

import pygame

from .config import PANEL_WIDTH, TILE_SIZE, WINDOW_PADDING
from .map_loader import MapData


class Renderer:
    def __init__(self, surface: pygame.Surface, map_data: MapData) -> None:
        self.surface = surface
        self.map_data = map_data
        self.font = pygame.font.SysFont("Arial", 18)

    def draw(self, state, ui_state) -> None:
        self.surface.fill((18, 22, 28))
        self._draw_grid(state.map_data)
        self._draw_mines(state)
        self._draw_subs(state)
        self._draw_cursor(ui_state)
        self._draw_panel(state, ui_state)

    def _draw_grid(self, map_data: MapData) -> None:
        for y in range(map_data.height):
            for x in range(map_data.width):
                color = (30, 70, 120)
                if map_data.is_blocked(x, y):
                    color = (25, 40, 50)
                rect = pygame.Rect(
                    WINDOW_PADDING + x * TILE_SIZE,
                    WINDOW_PADDING + y * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(self.surface, color, rect)
                pygame.draw.rect(self.surface, (10, 10, 10), rect, 1)

    def _draw_subs(self, state) -> None:
        colors = {"BLUE": (70, 200, 255), "RED": (240, 80, 80)}
        for team, sub in state.subs.items():
            center = (
                WINDOW_PADDING + sub.x * TILE_SIZE + TILE_SIZE // 2,
                WINDOW_PADDING + sub.y * TILE_SIZE + TILE_SIZE // 2,
            )
            pygame.draw.circle(self.surface, colors.get(team, (200, 200, 200)), center, TILE_SIZE // 3)

    def _draw_mines(self, state) -> None:
        for mine in state.mines:
            rect = pygame.Rect(
                WINDOW_PADDING + mine.x * TILE_SIZE + TILE_SIZE // 4,
                WINDOW_PADDING + mine.y * TILE_SIZE + TILE_SIZE // 4,
                TILE_SIZE // 2,
                TILE_SIZE // 2,
            )
            pygame.draw.rect(self.surface, (180, 180, 60), rect)

    def _draw_cursor(self, ui_state) -> None:
        cursor = ui_state.get("cursor")
        if cursor is None:
            return
        cx, cy = cursor
        rect = pygame.Rect(
            WINDOW_PADDING + cx * TILE_SIZE,
            WINDOW_PADDING + cy * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(self.surface, (250, 250, 120), rect, 2)

    def _draw_panel(self, state, ui_state) -> None:
        panel_x = WINDOW_PADDING * 2 + state.map_data.width * TILE_SIZE
        panel_rect = pygame.Rect(panel_x, WINDOW_PADDING, PANEL_WIDTH, state.map_data.height * TILE_SIZE)
        pygame.draw.rect(self.surface, (24, 30, 38), panel_rect)
        title = self.font.render("Human Controller", True, (230, 230, 230))
        self.surface.blit(title, (panel_x + 12, WINDOW_PADDING + 8))
        self._draw_queue(panel_x + 12, WINDOW_PADDING + 40, ui_state)
        self._draw_status(panel_x + 12, WINDOW_PADDING + 140, state, ui_state)

    def _draw_queue(self, x: int, y: int, ui_state) -> None:
        label = self.font.render("Queued actions:", True, (200, 200, 200))
        self.surface.blit(label, (x, y))
        for idx, action in enumerate(ui_state.get("queue", [])):
            text = self.font.render(f"{idx + 1}. {action}", True, (220, 220, 220))
            self.surface.blit(text, (x, y + 24 + idx * 20))

    def _draw_status(self, x: int, y: int, state, ui_state) -> None:
        active = ui_state.get("active_action") or "None"
        text = self.font.render(f"Active: {active}", True, (210, 210, 210))
        self.surface.blit(text, (x, y))
        turn = self.font.render(f"Turn: {state.turn}", True, (200, 200, 200))
        self.surface.blit(turn, (x, y + 24))
        blue = state.subs.get("BLUE")
        if blue:
            stats = self.font.render(f"Damage {blue.damage}/4", True, (200, 200, 200))
            self.surface.blit(stats, (x, y + 48))
        gauges = state.gauges.get("BLUE", {})
        if gauges:
            line1 = self.font.render(
                f"T{gauges.get('torpedo', 0)}/4 M{gauges.get('mine', 0)}/4", True, (190, 190, 190)
            )
            line2 = self.font.render(
                f"S{gauges.get('sonar', 0)}/4 D{gauges.get('drone', 0)}/4", True, (190, 190, 190)
            )
            line3 = self.font.render(
                f"Sil{gauges.get('silence', 0)}/4 Scn{gauges.get('scenario', 0)}/4",
                True,
                (190, 190, 190),
            )
            self.surface.blit(line1, (x, y + 72))
            self.surface.blit(line2, (x, y + 96))
            self.surface.blit(line3, (x, y + 120))
        choice = ui_state.get("charge_choice")
        if choice:
            choice_text = self.font.render(f"Charge: {choice}", True, (180, 180, 200))
            self.surface.blit(choice_text, (x, y + 144))
        skip = state.skip_turns.get("BLUE", 0)
        if skip > 0:
            skip_text = self.font.render(f"Surfaced: skip {skip} turns", True, (220, 160, 120))
            self.surface.blit(skip_text, (x, y + 168))
        hint = self.font.render("WASD move | F silence | T torpedo", True, (170, 170, 170))
        self.surface.blit(hint, (x, y + 200))
        hint2 = self.font.render("O sonar | V drone | M mine | G trigger", True, (170, 170, 170))
        self.surface.blit(hint2, (x, y + 224))
        hint3 = self.font.render("C surface | R repair | 1-6 charge", True, (170, 170, 170))
        self.surface.blit(hint3, (x, y + 248))
        hint4 = self.font.render("Space/click queue | Enter confirm | Backspace undo", True, (170, 170, 170))
        self.surface.blit(hint4, (x, y + 272))
        belief = ui_state.get("belief_prob")
        if belief is not None:
            prob_text = self.font.render(f"Belief at cursor: {belief:.2f}", True, (180, 180, 200))
            self.surface.blit(prob_text, (x, y + 296))
        if state.game_over:
            winner = state.winner or "None"
            game_over = self.font.render(f"Game Over - Winner: {winner}", True, (240, 180, 90))
            self.surface.blit(game_over, (x, y + 320))

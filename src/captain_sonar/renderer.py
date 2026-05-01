from __future__ import annotations

from pathlib import Path

import pygame

from .config import (
    MAP_BACKGROUND_PATH,
    MAP_MARGIN_X,
    MAP_MARGIN_Y,
    PANEL_WIDTH,
    TILE_SIZE,
    WINDOW_PADDING,
    MAP_INNER_PADDING_RIGHT,
    MAP_INNER_PADDING_BOTTOM,
)
from .map_loader import MapData


class Renderer:
    def __init__(self, surface: pygame.Surface, map_data: MapData, background_path: str | None = MAP_BACKGROUND_PATH) -> None:
        self.surface = surface
        self.map_data = map_data
        self.font = pygame.font.SysFont("Arial", 18)
        self.background: pygame.Surface | None = None
        self.grid_overlay = self._build_grid_overlay()
        if background_path:
            self._load_background(background_path)

    def draw(self, state, ui_state) -> None:
        self.surface.fill((18, 22, 28))
        map_surf = self._compose_map_surface(state, ui_state)
        self.surface.blit(map_surf, (WINDOW_PADDING, WINDOW_PADDING))
        self._draw_panel(state, ui_state)

    def _compose_map_surface(self, state, ui_state) -> pygame.Surface:
        base_w, base_h = self._map_pixel_size()
        surface = pygame.Surface((base_w, base_h), pygame.SRCALPHA)
        # background
        if self.background:
            surface.blit(self.background, (0, 0))
        else:
            rect = pygame.Rect(0, 0, base_w, base_h)
            pygame.draw.rect(surface, (30, 70, 120), rect)
        # grid overlay and elements
        if self.grid_overlay:
            surface.blit(self.grid_overlay, (MAP_MARGIN_X, MAP_MARGIN_Y))
        self._draw_mines_on(surface, state)
        self._draw_subs_on(surface, state)
        self._draw_cursor_on(surface, ui_state)
        return surface

    def _build_grid_overlay(self) -> pygame.Surface:
        width_px = self.map_data.width * TILE_SIZE
        height_px = self.map_data.height * TILE_SIZE
        overlay = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
        line_color = (255, 255, 255, 80)
        for x in range(self.map_data.width + 1):
            xpos = x * TILE_SIZE
            pygame.draw.line(overlay, line_color, (xpos, 0), (xpos, height_px))
        for y in range(self.map_data.height + 1):
            ypos = y * TILE_SIZE
            pygame.draw.line(overlay, line_color, (0, ypos), (width_px, ypos))
        return overlay


    def _load_background(self, background_path: str) -> None:
        path = self._resolve_background_path(background_path)
        try:
            image = pygame.image.load(str(path)).convert_alpha()
        except (FileNotFoundError, pygame.error):
            return
        target_size = self._map_pixel_size()
        if image.get_size() != target_size:
            image = pygame.transform.smoothscale(image, target_size)
        self.background = image

    def _resolve_background_path(self, background_path: str) -> Path:
        path = Path(background_path)
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parents[2] / path

    def _map_origin(self) -> tuple[int, int]:
        return (WINDOW_PADDING + MAP_MARGIN_X, WINDOW_PADDING + MAP_MARGIN_Y)

    def _map_pixel_size(self) -> tuple[int, int]:
        return (
            self.map_data.width * TILE_SIZE + MAP_MARGIN_X + MAP_INNER_PADDING_RIGHT,
            self.map_data.height * TILE_SIZE + MAP_MARGIN_Y + MAP_INNER_PADDING_BOTTOM,
        )

    def _draw_subs(self, state) -> None:
        # legacy: not used; drawing happens on composed surface
        return

    def _draw_subs_on(self, surface: pygame.Surface, state) -> None:
        colors = {"BLUE": (70, 200, 255), "RED": (240, 80, 80)}
        origin_x, origin_y = MAP_MARGIN_X, MAP_MARGIN_Y
        for team, sub in state.subs.items():
            center = (
                origin_x + sub.x * TILE_SIZE + TILE_SIZE // 2,
                origin_y + sub.y * TILE_SIZE + TILE_SIZE // 2,
            )
            pygame.draw.circle(surface, colors.get(team, (200, 200, 200)), center, TILE_SIZE // 3)

    def _draw_mines(self, state) -> None:
        return

    def _draw_mines_on(self, surface: pygame.Surface, state) -> None:
        origin_x, origin_y = MAP_MARGIN_X, MAP_MARGIN_Y
        for mine in state.mines:
            rect = pygame.Rect(
                origin_x + mine.x * TILE_SIZE + TILE_SIZE // 4,
                origin_y + mine.y * TILE_SIZE + TILE_SIZE // 4,
                TILE_SIZE // 2,
                TILE_SIZE // 2,
            )
            pygame.draw.rect(surface, (180, 180, 60), rect)

    def _draw_cursor(self, ui_state) -> None:
        return

    def _draw_cursor_on(self, surface: pygame.Surface, ui_state) -> None:
        cursor = ui_state.get("cursor")
        if cursor is None:
            return
        cx, cy = cursor
        origin_x, origin_y = MAP_MARGIN_X, MAP_MARGIN_Y
        rect = pygame.Rect(
            origin_x + cx * TILE_SIZE,
            origin_y + cy * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(surface, (250, 250, 120), rect, 2)

    def _draw_panel(self, state, ui_state) -> None:
        map_width, map_height = self._map_pixel_size()
        panel_x = WINDOW_PADDING * 2 + map_width
        panel_rect = pygame.Rect(panel_x, WINDOW_PADDING, PANEL_WIDTH, map_height)
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

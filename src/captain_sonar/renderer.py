from __future__ import annotations

from pathlib import Path
from typing import cast

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
from .engineer_layout import ENGINEER_BOARD_HEIGHT, ENGINEER_BOARD_WIDTH, ENGINEER_BUTTON_RADIUS, ENGINEER_IMAGE_WIDTH, engineer_board_geometry
from .map_loader import MapData


class Renderer:
    def __init__(self, surface: pygame.Surface, map_data: MapData, background_path: str | None = MAP_BACKGROUND_PATH) -> None:
        self.surface = surface
        self.map_data = map_data
        self.font = pygame.font.SysFont("Arial", 18)
        self.small_font = pygame.font.SysFont("Arial", 14)
        self.background: pygame.Surface | None = None
        self.engineer_background: pygame.Surface | None = None
        self.grid_overlay = self._build_grid_overlay()
        if background_path:
            self._load_background(background_path)
        self._load_engineer_background()

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

    def _draw_subs_on(self, surface: pygame.Surface, state) -> None:
        colors = {"BLUE": (70, 200, 255), "RED": (240, 80, 80)}
        origin_x, origin_y = MAP_MARGIN_X, MAP_MARGIN_Y
        for team, sub in state.subs.items():
            center = (
                origin_x + sub.x * TILE_SIZE + TILE_SIZE // 2,
                origin_y + sub.y * TILE_SIZE + TILE_SIZE // 2,
            )
            pygame.draw.circle(surface, colors.get(team, (200, 200, 200)), center, TILE_SIZE // 3)

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

    # =========================================================================
    # PANEL DRAWING - ORGANIZED DISPLAY OF GAME STATE
    # =========================================================================

    def _draw_panel(self, state, ui_state) -> None:
        """Draw the right panel with organized game state display."""
        map_width, map_height = self._map_pixel_size()
        panel_x = WINDOW_PADDING * 2 + map_width
        panel_rect = pygame.Rect(panel_x, WINDOW_PADDING, PANEL_WIDTH, map_height)
        pygame.draw.rect(self.surface, (24, 30, 38), panel_rect)
        
        # Title
        active_team = ui_state.get("active_team", "BLUE")
        turn_phase = ui_state.get("turn_phase", "move")
        phase_label = "Move" if turn_phase == "move" else "System"
        if ui_state.get("show_engineer_board"):
            title_text = f"ENGI BOARD ({active_team} - {phase_label} Phase)"
            title_color = (255, 220, 160)
        else:
            title_text = f"GAME STATE - {active_team} {phase_label} Phase"
            title_color = (100, 200, 255) if active_team == "BLUE" else (255, 150, 150)
        title = self.font.render(title_text, True, title_color)
        self.surface.blit(title, (panel_x + 12, WINDOW_PADDING + 8))
        
        # Draw sections with vertical layout
        y_offset = WINDOW_PADDING + 32
        if ui_state.get("show_engineer_board"):
            y_offset = self._draw_engineer_board(panel_x + 12, y_offset, state, ui_state)
        else:
            y_offset = self._draw_game_info(panel_x + 12, y_offset, state)
            y_offset = self._draw_submarines_status(panel_x + 12, y_offset, state)
            y_offset = self._draw_systems_gauges(panel_x + 12, y_offset, state, ui_state)
            y_offset = self._draw_mines_status(panel_x + 12, y_offset, state)
            y_offset = self._draw_surface_status(panel_x + 12, y_offset, state)
            y_offset = self._draw_queue(panel_x + 12, y_offset, ui_state)
        self._draw_controls_hints(panel_x + 12, y_offset, ui_state)

    def _draw_engineer_board(self, x: int, y: int, state, ui_state) -> int:
        """Display the engineer control panel as the provided image with side controls."""
        team = str(ui_state.get("team", "BLUE"))
        breakdown = state.breakdowns.get(team)
        choice = ui_state.get("engineer_choice", {}) if isinstance(ui_state.get("engineer_choice", {}), dict) else {}
        selected_button_id = choice.get("button_id") if isinstance(choice.get("button_id"), str) else None
        allowed_direction = ui_state.get("engineer_direction")
        if not isinstance(allowed_direction, str):
            allowed_direction = None

        geometry = engineer_board_geometry(x, y)
        board_rect = pygame.Rect(*cast(tuple[int, int, int, int], geometry["board_rect"]))
        image_rect = pygame.Rect(*cast(tuple[int, int, int, int], geometry["image_rect"]))
        rows = cast(dict[str, dict[str, object]], geometry["rows"])

        if not breakdown:
            empty = self.font.render("No engineer data available", True, (150, 150, 150))
            self.surface.blit(empty, (x + 12, y + 12))
            return y + ENGINEER_BOARD_HEIGHT + 8

        if self.engineer_background:
            self.surface.blit(self.engineer_background, image_rect.topleft)
        else:
            pygame.draw.rect(self.surface, (12, 48, 78), image_rect, border_radius=12)

        left_panel = pygame.Rect(board_rect.left, board_rect.top, image_rect.left - board_rect.left, board_rect.height)
        pygame.draw.rect(self.surface, (14, 32, 54), left_panel, border_radius=12)

        row_font = pygame.font.SysFont("Arial", 12, bold=True)
        slot_font = pygame.font.SysFont("Arial", 11, bold=True)
        meta_font = pygame.font.SysFont("Arial", 8, bold=True)

        for direction in ("W", "N", "S", "E"):
            row = rows[direction]
            row_specs = cast(list[object], row.get("button_specs", []))
            crossed_ids = breakdown.crossed_by_direction.get(direction, set())
            filled_slots = {
                idx
                for idx, spec in enumerate(row_specs)
                if getattr(spec, "button_id", "") in crossed_ids
            }
            selected_index = next(
                (idx for idx, spec in enumerate(row_specs) if getattr(spec, "button_id", "") == selected_button_id),
                None,
            )
            row_allowed = allowed_direction == direction
            self._draw_engineer_section(
                label=direction,
                subtitle="",
                row=row,
                row_label=direction,
                row_font=row_font,
                slot_font=slot_font,
                meta_font=meta_font,
                filled_slots=filled_slots,
                active=row_allowed or selected_index is not None,
                selected_index=selected_index,
                selected_button_id=selected_button_id,
                highlight_color=(252, 216, 81),
            )


        return y + ENGINEER_BOARD_HEIGHT + 8

    def _draw_engineer_section(
        self,
        label: str,
        subtitle: str,
        row: dict[str, object],
        row_label: str,
        row_font: pygame.font.Font,
        slot_font: pygame.font.Font,
        meta_font: pygame.font.Font,
        filled_slots: set[int],
        active: bool,
        selected_index: int | None,
        selected_button_id: str | None,
        highlight_color: tuple[int, int, int],
    ) -> None:
        label_rect = pygame.Rect(*cast(tuple[int, int, int, int], row["label_rect"]))
        row_y = int(cast(int, row["row_y"]))

        label_surface = row_font.render(row_label, True, (255, 255, 255))
        label_background = highlight_color if active else (74, 88, 98)
        pygame.draw.rect(self.surface, label_background, label_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), label_rect, width=1, border_radius=8)
        label_center = label_surface.get_rect(center=label_rect.center)
        self.surface.blit(label_surface, label_center.topleft)

        self._draw_engineer_row_slots(
            cast(list[tuple[int, int]], row["buttons"]),
            cast(list[object], row.get("button_specs", [])),
            filled_slots,
            active,
            selected_index,
            selected_button_id,
            slot_font,
            meta_font,
        )

    def _draw_engineer_row_slots(
        self,
        slots: list[tuple[int, int]],
        button_specs: list[object],
        filled_slots: set[int],
        active: bool,
        selected_index: int | None,
        selected_button_id: str | None,
        slot_font: pygame.font.Font,
        meta_font: pygame.font.Font,
    ) -> None:
        for slot_index, (slot_x, slot_y) in enumerate(slots):
            filled = slot_index in filled_slots
            spec = button_specs[slot_index] if slot_index < len(button_specs) else None
            is_selected = bool(
                selected_button_id
                and spec is not None
                and getattr(spec, "button_id", "") == selected_button_id
            )

            border_color = (255, 245, 160) if is_selected else ((252, 216, 81) if active and selected_index == slot_index else (92, 118, 132))
            border_width = 4 if is_selected else 2
            pygame.draw.circle(self.surface, border_color, (slot_x, slot_y), ENGINEER_BUTTON_RADIUS + (1 if is_selected else 0), border_width)

            if filled or is_selected or (active and selected_index == slot_index):
                cross_color = (186, 40, 36) if filled else ((255, 230, 120) if is_selected else (238, 207, 75))
                cross_radius = ENGINEER_BUTTON_RADIUS - (1 if is_selected else 3)
                cross_width = 4 if is_selected else 3
                self._draw_cross(slot_x, slot_y, cross_radius, cross_color, cross_width)
                if is_selected and not filled:
                    pygame.draw.circle(self.surface, (255, 245, 160), (slot_x, slot_y), ENGINEER_BUTTON_RADIUS - 6, 0)
            else:
                number_surface = slot_font.render(str(slot_index + 1), True, (54, 84, 96))
                number_rect = number_surface.get_rect(center=(slot_x, slot_y + 1))
                self.surface.blit(number_surface, number_rect.topleft)

    def _draw_cross(self, x: int, y: int, radius: int, color: tuple[int, int, int], width: int) -> None:
        pygame.draw.line(self.surface, color, (x - radius, y - radius), (x + radius, y + radius), width)
        pygame.draw.line(self.surface, color, (x - radius, y + radius), (x + radius, y - radius), width)

    def _draw_slot(self, x: float, y: float, size: int, filled: bool, selected: bool) -> None:
        """Draw a central circuit breakdown slot."""
        # Background circle
        bg_color = (90, 180, 255) if filled else (50, 65, 90)
        pygame.draw.circle(self.surface, bg_color, (int(x), int(y)), size // 2, 0)
        
        # Border
        border_color = (255, 240, 170) if selected else (120, 150, 180)
        border_width = 3 if selected else 2
        pygame.draw.circle(self.surface, border_color, (int(x), int(y)), size // 2, border_width)

    def _draw_reactor_slot(self, x: float, y: float, size: int, filled: bool, selected: bool) -> None:
        """Draw a reactor radiation breakdown slot."""
        # Background circle
        bg_color = (255, 150, 100) if filled else (80, 65, 50)
        pygame.draw.circle(self.surface, bg_color, (int(x), int(y)), size // 2, 0)
        
        # Border
        border_color = (255, 240, 170) if selected else (200, 140, 100)
        border_width = 3 if selected else 2
        pygame.draw.circle(self.surface, border_color, (int(x), int(y)), size // 2, border_width)

    def _bar(self, filled: int, total: int) -> str:
        filled = max(0, min(filled, total))
        return "█" * filled + "░" * (total - filled)

    def _draw_game_info(self, x: int, y: int, state) -> int:
        """Display turn number and game status."""
        sep = self.font.render("-" * 35, True, (100, 100, 100))
        self.surface.blit(sep, (x, y))
        
        turn_text = self.font.render(f"Turn: {state.turn}", True, (200, 255, 200))
        self.surface.blit(turn_text, (x, y + 18))
        
        if state.game_over:
            winner = state.winner or "DRAW"
            game_over = self.font.render(f"GAME OVER - Winner: {winner}", True, (255, 100, 100))
            self.surface.blit(game_over, (x, y + 36))
            return y + 60
        
        return y + 40

    def _draw_submarines_status(self, x: int, y: int, state) -> int:
        """Display status of both submarines."""
        header = self.font.render("SUBMARINES:", True, (150, 255, 150))
        self.surface.blit(header, (x, y))
        y += 20
        
        # Blue team
        blue = state.subs.get("BLUE")
        if blue:
            damage_color = (100, 200, 255) if blue.damage < 4 else (255, 100, 100)
            blue_status = self.font.render(
                f"BLUE: Pos({blue.x},{blue.y}) Dmg {blue.damage}/4",
                True,
                damage_color
            )
            self.surface.blit(blue_status, (x, y))
            y += 18
        
        # Red team
        red = state.subs.get("RED")
        if red:
            damage_color = (255, 150, 150) if red.damage < 4 else (255, 100, 100)
            red_status = self.font.render(
                f"RED: Pos({red.x},{red.y}) Dmg {red.damage}/4",
                True,
                damage_color
            )
            self.surface.blit(red_status, (x, y))
            y += 18
        
        return y + 8

    def _draw_systems_gauges(self, x: int, y: int, state, ui_state) -> int:
        """Display all system gauge status."""
        team = str(ui_state.get("team", "BLUE"))
        turn_phase = str(ui_state.get("turn_phase", "move"))
        charge_choice = str(ui_state.get("charge_choice", ""))
        blink_on = (pygame.time.get_ticks() // 300) % 2 == 0

        team_color = (150, 200, 255) if team == "BLUE" else (255, 170, 170)
        header = self.font.render(f"SYSTEMS ({team}):", True, team_color)
        self.surface.blit(header, (x, y))
        y += 20
        
        gauges = state.gauges.get(team, {})
        if gauges:
            def draw_segment_bar(
                bar_x: int,
                bar_y: int,
                value: int,
                color: tuple[int, int, int],
                selected: bool,
            ) -> None:
                segment_w = 17
                segment_h = 12
                segment_gap = 4
                border_color = (255, 235, 120) if selected and blink_on else (110, 130, 150)
                for idx in range(4):
                    rect_x = bar_x + idx * (segment_w + segment_gap)
                    rect = pygame.Rect(rect_x, bar_y, segment_w, segment_h)
                    pygame.draw.rect(self.surface, (32, 40, 50), rect, border_radius=2)
                    if idx < value:
                        pygame.draw.rect(self.surface, color, rect.inflate(-2, -2), border_radius=2)
                    pygame.draw.rect(self.surface, border_color, rect, 1, border_radius=2)

            def render_line(label: str, key: str, value: int, default_color: tuple[int, int, int]) -> None:
                nonlocal y
                selected = turn_phase == "move" and charge_choice == key
                text_color = (255, 235, 120) if selected and blink_on else default_color
                line = self.font.render(f"{label}:", True, text_color)
                self.surface.blit(line, (x, y))
                draw_segment_bar(x + 92, y + 3, value, default_color, selected)
                y += 20

            # Weapon systems
            torp = gauges.get('torpedo', 0)
            mine = gauges.get('mine', 0)
            render_line("Torpedo", "torpedo", torp, (255, 150, 100))
            render_line("Mine", "mine", mine, (255, 150, 100))
            y += 38
            
            # Detection systems
            sonar = gauges.get('sonar', 0)
            drone = gauges.get('drone', 0)
            render_line("Sonar", "sonar", sonar, (100, 255, 150))
            render_line("Drone", "drone", drone, (100, 255, 150))
            y += 38
            
            # Special systems
            silence = gauges.get('silence', 0)
            scenario = gauges.get('scenario', 0)
            render_line("Silence", "silence", silence, (200, 150, 255))
            render_line("Scenario", "scenario", scenario, (200, 150, 255))
            y += 38

            if turn_phase == "move" and charge_choice in {
                "torpedo",
                "mine",
                "sonar",
                "drone",
                "silence",
                "scenario",
            }:
                info_color = (255, 235, 120) if blink_on else (150, 150, 120)
                info = self.small_font.render("Selected system will charge on move", True, info_color)
                self.surface.blit(info, (x, y - 8))
        
        return y + 4

    def _draw_mines_status(self, x: int, y: int, state) -> int:
        """Display deployed mines information."""
        header = self.font.render("MINES:", True, (200, 180, 100))
        self.surface.blit(header, (x, y))
        y += 20
        
        blue_mines = [m for m in state.mines if m.owner == "BLUE"]
        red_mines = [m for m in state.mines if m.owner == "RED"]
        
        blue_mines_text = self.font.render(f"BLUE: {len(blue_mines)} deployed", True, (100, 200, 255))
        self.surface.blit(blue_mines_text, (x, y))
        y += 16
        
        red_mines_text = self.font.render(f"RED: {len(red_mines)} deployed", True, (255, 150, 150))
        self.surface.blit(red_mines_text, (x, y))
        y += 16
        
        return y + 8

    def _draw_surface_status(self, x: int, y: int, state) -> int:
        """Display surfacing status for both teams."""
        blue_skip = state.skip_turns.get("BLUE", 0)
        red_skip = state.skip_turns.get("RED", 0)
        
        if blue_skip > 0 or red_skip > 0:
            header = self.font.render("SURFACING:", True, (220, 160, 120))
            self.surface.blit(header, (x, y))
            y += 20
            
            if blue_skip > 0:
                blue_skip_text = self.font.render(f"BLUE: {blue_skip} turns remaining", True, (100, 200, 255))
                self.surface.blit(blue_skip_text, (x, y))
                y += 16
            
            if red_skip > 0:
                red_skip_text = self.font.render(f"RED: {red_skip} turns remaining", True, (255, 150, 150))
                self.surface.blit(red_skip_text, (x, y))
                y += 16
            
            return y + 8
        
        return y

    def _draw_queue(self, x: int, y: int, ui_state) -> int:
        """Display queued actions."""
        label = self.font.render("QUEUE:", True, (220, 180, 255))
        self.surface.blit(label, (x, y))
        queue = ui_state.get("queue", [])
        y += 20
        
        if not queue:
            empty = self.font.render("(empty)", True, (150, 150, 150))
            self.surface.blit(empty, (x, y))
            return y + 30
        
        for idx, action in enumerate(queue):
            text = self.font.render(f"{idx + 1}. {action}", True, (200, 200, 220))
            self.surface.blit(text, (x, y + idx * 16))
        
        return y + len(queue) * 16 + 8

    def _draw_controls_hints(self, x: int, y: int, ui_state) -> None:
        """Display control hints at bottom of panel."""
        active_team = ui_state.get("active_team", "BLUE")
        turn_phase = ui_state.get("turn_phase", "move")
        phase_text = "MOVE" if turn_phase == "move" else "SYSTEM"
        team_color = (100, 200, 255) if active_team == "BLUE" else (255, 150, 150)
        header = self.small_font.render(f"ACTIVE: {active_team} | PHASE: {phase_text}", True, team_color)
        self.surface.blit(header, (x, y))
        y += 18
        
        controls_header = self.small_font.render(f"{phase_text} CONTROLS:", True, (180, 180, 180))
        self.surface.blit(controls_header, (x, y))
        y += 16

        if turn_phase == "move":
            hints = [
                "WASD move | F silence",
                "1-6 choose charge to load",
                "P engineer board",
                "Enter confirm move phase",
                "Bkspc undo"
            ]
        else:
            hints = [
                "T torpedo | O sonar",
                "V drone | M mine | G trigger",
                "C surface | R repair",
                "Space/click queue selected system",
                "Enter confirm (or skip with empty queue)",
                "P engineer board",
                "Bkspc undo"
            ]
        
        for hint in hints:
            text = self.small_font.render(hint, True, (140, 140, 140))
            self.surface.blit(text, (x, y))
            y += 14

    def _load_engineer_background(self) -> None:
        path = Path(__file__).resolve().parents[2] / "engy.png"
        try:
            image = pygame.image.load(str(path)).convert_alpha()
        except (FileNotFoundError, pygame.error):
            self.engineer_background = None
            return
        target_size = (ENGINEER_IMAGE_WIDTH, ENGINEER_BOARD_HEIGHT)
        if image.get_size() != target_size:
            image = pygame.transform.smoothscale(image, target_size)
        self.engineer_background = image

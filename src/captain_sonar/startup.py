from __future__ import annotations

from dataclasses import dataclass

import pygame

from .config import TILE_SIZE, WINDOW_PADDING, PANEL_WIDTH
from .game_state import SubmarineState
from .map_loader import MapData


@dataclass
class _PreviewState:
    subs: dict[str, SubmarineState]
    mines: list[object]
    gauges: dict[str, dict[str, int]]
    breakdowns: dict[str, object]
    turn: int = 0
    game_over: bool = False
    winner: str | None = None


def choose_start_positions(
    map_data: MapData,
    start_mode: str | None,
    surface: pygame.Surface,
    renderer,
) -> dict[str, SubmarineState]:
    default = {
        "BLUE": SubmarineState(x=1, y=1),
        "RED": SubmarineState(x=map_data.width - 2, y=map_data.height - 2),
    }
    swapped = {
        "BLUE": SubmarineState(x=map_data.width - 2, y=map_data.height - 2),
        "RED": SubmarineState(x=1, y=1),
    }
    if start_mode == "default":
        return default
    if start_mode == "swap":
        return swapped

    preview_state = _PreviewState(
        subs={},
        mines=[],
        gauges={},
        breakdowns={},
    )
    placing = ["BLUE", "RED"]
    confirmed: dict[str, SubmarineState] = {}
    draft: SubmarineState | None = None
    index = 0
    clock = pygame.time.Clock()
    cursor: tuple[int, int] | None = None

    while True:
        selecting = index < len(placing)
        current_team = placing[index] if selecting else None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return default
            if not selecting:
                continue
            if event.type == pygame.MOUSEMOTION:
                cursor = _cursor_from_mouse(event.pos, map_data, renderer)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                grid_pos = _cursor_from_mouse(event.pos, map_data, renderer)
                if grid_pos is not None:
                    draft = SubmarineState(x=grid_pos[0], y=grid_pos[1])
                    # current_team can be None by static analysis; guard to keep types strict
                    if current_team is not None:
                        preview_state.subs = {current_team: draft}
                    else:
                        preview_state.subs = {}
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if draft is not None and current_team is not None:
                    confirmed[current_team] = draft
                    draft = None
                    preview_state.subs = {}
                    index += 1
                    if index >= len(placing):
                        selecting = False

        if not selecting:
            break

        surface.fill((18, 22, 28))
        # Tell renderer which team is currently placing so it can show that draft sub
        map_surf = renderer._compose_map_surface(preview_state, {"cursor": cursor, "active_team": current_team or "BLUE"})
        surface.blit(map_surf, (WINDOW_PADDING, WINDOW_PADDING))
        font = pygame.font.SysFont("Arial", 20, bold=True)
        sub_font = pygame.font.SysFont("Arial", 14, bold=True)
        # Position instruction box inside the right-side panel (lateral bar)
        map_w, map_h = renderer._map_pixel_size()
        panel_x = WINDOW_PADDING * 2 + map_w
        box_x = panel_x + 12
        box_w = PANEL_WIDTH - 24
        box_h = 64
        box_y = WINDOW_PADDING + 8
        instruction_box = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(surface, (12, 18, 24), instruction_box, border_radius=10)
        pygame.draw.rect(surface, (255, 196, 64), instruction_box, width=2, border_radius=10)
        if current_team is not None and draft is None:
            instruction = f"Click a cell for {current_team}"
            sub_instruction = "Press Enter to confirm after placing the sub"
        else:
            # show a safer label if current_team is None
            label_team = current_team if current_team is not None else "TEAM"
            instruction = f"{label_team} selected"
            sub_instruction = "Enter to confirm/click another change"
        text = font.render(instruction, True, (255, 244, 160))
        sub_text = sub_font.render(sub_instruction, True, (235, 235, 235))
        surface.blit(text, (box_x + 8, box_y + 8))
        surface.blit(sub_text, (box_x + 8, box_y + 34))
        pygame.display.flip()
        clock.tick(30)

    return {team: SubmarineState(x=sub.x, y=sub.y) for team, sub in confirmed.items()}


def _cursor_from_mouse(
    mouse_pos: tuple[int, int],
    map_data: MapData,
    renderer,
) -> tuple[int, int] | None:
    mx, my = mouse_pos
    ox, oy = renderer._map_origin()
    local_x = mx - ox
    local_y = my - oy
    if local_x < 0 or local_y < 0:
        return None
    grid_x = int(local_x // TILE_SIZE)
    grid_y = int(local_y // TILE_SIZE)
    if 0 <= grid_x < map_data.width and 0 <= grid_y < map_data.height:
        return (grid_x, grid_y)
    return None

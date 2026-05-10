from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable, Mapping, Tuple

import pygame

from .config import TILE_SIZE, WINDOW_PADDING, PANEL_WIDTH
from .game_state import SubmarineState
from .map_loader import MapData


GridPos = Tuple[int, int]
StartPositionPicker = Callable[[str, MapData, Mapping[str, SubmarineState]], GridPos | None]
TEAM_HUMAN = "human"
TEAM_AGENT = "agent"


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
    team_picker: StartPositionPicker | None = None,
    play_types_path: str | None = None,
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

    team_play_types = load_team_play_types(play_types_path)
    confirmed: dict[str, SubmarineState] = {}
    for team in ("BLUE", "RED"):
        play_type = team_play_types.get(team, TEAM_HUMAN)
        if play_type == TEAM_AGENT:
            if team_picker is None:
                raise ValueError(f"{team} is configured as agent but no team_picker was provided")
            attempts = 0
            picked = None
            while attempts < 3:
                try:
                    picked = choose_single_team_start_position(map_data, team, confirmed, team_picker)
                    if picked is None:
                        raise ValueError(f"team_picker returned no position for agent team {team}")
                    confirmed[team] = picked
                    break
                except ValueError as e:
                    # show a brief message on the UI to indicate invalid pick
                    if surface is not None and renderer is not None:
                        _flash_message(surface, renderer, str(e))
                    attempts += 1
            if picked is None:
                raise ValueError(f"agent team {team} failed to provide a valid start position")
            continue

        confirmed[team] = choose_human_start_position(map_data, team, surface, renderer)

    return {team: SubmarineState(x=sub.x, y=sub.y) for team, sub in confirmed.items()}





def load_team_play_types(path: str | None) -> dict[str, str]:
    """Load per-team play types from JSON. Defaults both teams to human."""
    defaults = {"BLUE": TEAM_HUMAN, "RED": TEAM_HUMAN}
    if not path:
        return defaults

    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, dict):
        raise ValueError("play types file must be a JSON object")

    parsed = defaults.copy()
    for team in ("BLUE", "RED"):
        value = raw.get(team)
        if value is None:
            value = raw.get(team.lower())
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(f"play type for {team} must be a string")
        normalized = value.strip().lower()
        if normalized not in (TEAM_HUMAN, TEAM_AGENT):
            raise ValueError(f"invalid play type for {team}: {value}")
        parsed[team] = normalized

    return parsed


def choose_human_start_position(
    map_data: MapData,
    team: str,
    surface: pygame.Surface,
    renderer,
) -> SubmarineState:
    """Interactively choose a start position for one team."""
    preview_state = _PreviewState(
        subs={},
        mines=[],
        gauges={},
        breakdowns={},
    )
    draft: SubmarineState | None = None
    cursor: tuple[int, int] | None = None
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise SystemExit()
            if event.type == pygame.MOUSEMOTION:
                cursor = _cursor_from_mouse(event.pos, map_data, renderer)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                grid_pos = _cursor_from_mouse(event.pos, map_data, renderer)
                if grid_pos is not None:
                    draft = SubmarineState(x=grid_pos[0], y=grid_pos[1])
                    preview_state.subs = {team: draft}
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if draft is not None:
                    try:
                        _validate_start_position(map_data, (draft.x, draft.y), team=team)
                        return draft
                    except ValueError as e:
                        # show error on screen and allow retry
                        _flash_message(surface, renderer, str(e))

        surface.fill((18, 22, 28))
        map_surf = renderer._compose_map_surface(preview_state, {"cursor": cursor, "active_team": team})
        surface.blit(map_surf, (WINDOW_PADDING, WINDOW_PADDING))
        font = pygame.font.SysFont("Arial", 20, bold=True)
        sub_font = pygame.font.SysFont("Arial", 14, bold=True)
        map_w, map_h = renderer._map_pixel_size()
        panel_x = WINDOW_PADDING * 2 + map_w
        box_x = panel_x + 12
        box_w = PANEL_WIDTH - 24
        box_h = 64
        box_y = WINDOW_PADDING + 8
        instruction_box = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(surface, (12, 18, 24), instruction_box, border_radius=10)
        pygame.draw.rect(surface, (255, 196, 64), instruction_box, width=2, border_radius=10)
        if draft is None:
            instruction = f"Click a cell for {team}"
            sub_instruction = "Press Enter to confirm after placing the sub"
        else:
            instruction = f"{team} selected"
            sub_instruction = "Press Enter to confirm or click another cell"
        text = font.render(instruction, True, (255, 244, 160))
        sub_text = sub_font.render(sub_instruction, True, (235, 235, 235))
        surface.blit(text, (box_x + 8, box_y + 8))
        surface.blit(sub_text, (box_x + 8, box_y + 34))
        pygame.display.flip()
        clock.tick(30)


def _flash_message(surface: pygame.Surface, renderer, message: str, duration_ms: int = 1600) -> None:
    """Render a centered message box over the map for a short time."""
    # Compose a simple overlay using renderer to show current map state
    try:
        preview_state = _PreviewState(subs={}, mines=[], gauges={}, breakdowns={})
        map_surf = renderer._compose_map_surface(preview_state, {})
        surface.fill((18, 22, 28))
        surface.blit(map_surf, (WINDOW_PADDING, WINDOW_PADDING))
    except Exception:
        surface.fill((18, 22, 28))

    font = pygame.font.SysFont("Arial", 18, bold=True)
    text = font.render(message, True, (255, 100, 100))
    map_w, map_h = renderer._map_pixel_size() if renderer is not None else (400, 300)
    panel_x = WINDOW_PADDING * 2 + map_w
    box_w = PANEL_WIDTH - 24
    box_x = panel_x + 12
    box_y = WINDOW_PADDING + 8
    box_h = 64
    instruction_box = pygame.Rect(box_x, box_y, box_w, box_h)
    pygame.draw.rect(surface, (12, 18, 24), instruction_box, border_radius=10)
    pygame.draw.rect(surface, (255, 196, 64), instruction_box, width=2, border_radius=10)
    surface.blit(text, (box_x + 8, box_y + 18))
    pygame.display.flip()
    pygame.time.delay(duration_ms)


def choose_single_team_start_position(
    map_data: MapData,
    team: str,
    confirmed: Mapping[str, SubmarineState],
    picker: StartPositionPicker,
) -> SubmarineState | None:
    """
    Resolve a single team's start position through an agent picker callback.

    Returns None when the picker declines to choose for the team.
    """
    picked = picker(team, map_data, confirmed)
    if picked is None:
        return None

    _validate_start_position(map_data, picked, team=team)
    if any(sub.x == picked[0] and sub.y == picked[1] for sub in confirmed.values()):
        raise ValueError(f"{team} start position overlaps an already selected tile: {picked}")

    return SubmarineState(x=picked[0], y=picked[1])


def _validate_start_position(map_data: MapData, pos: GridPos, team: str) -> None:
    x, y = pos
    if not map_data.in_bounds(x, y):
        raise ValueError(f"{team} start position out of bounds: {(x, y)}")
    if map_data.is_blocked(x, y):
        raise ValueError(f"{team} start position is blocked: {(x, y)}")


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

from captain_sonar.config import MAP_MARGIN_X, MAP_MARGIN_Y, TILE_SIZE
from captain_sonar.map_loader import MapData
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.renderer import Renderer
from captain_sonar.startup import choose_start_positions

import pygame


def test_choose_start_positions_default_and_swap():
    map_data = MapData(width=6, height=5, tiles=[["."] * 6 for _ in range(5)])

    default_positions = choose_start_positions(map_data, "default", None, None)
    swapped_positions = choose_start_positions(map_data, "swap", None, None)

    assert default_positions["BLUE"].x == 1
    assert default_positions["BLUE"].y == 1
    assert default_positions["RED"].x == 4
    assert default_positions["RED"].y == 3

    assert swapped_positions["BLUE"].x == 4
    assert swapped_positions["BLUE"].y == 3
    assert swapped_positions["RED"].x == 1
    assert swapped_positions["RED"].y == 1


def test_renderer_only_draws_active_team_submarine():
    pygame.init()
    map_data = MapData(width=6, height=5, tiles=[["."] * 6 for _ in range(5)])
    surface = pygame.display.set_mode((800, 600))
    renderer = Renderer(surface, map_data, background_path=None)
    state = GameState(
        map_data=map_data,
        subs={"BLUE": SubmarineState(x=1, y=1), "RED": SubmarineState(x=4, y=3)},
    )

    map_surface = renderer._compose_map_surface(state, {"active_team": "BLUE"})
    tile_center = lambda x, y: (MAP_MARGIN_X + x * TILE_SIZE + TILE_SIZE // 2, MAP_MARGIN_Y + y * TILE_SIZE + TILE_SIZE // 2)

    active_pixel = map_surface.get_at(tile_center(1, 1))
    inactive_pixel = map_surface.get_at(tile_center(4, 3))

    assert active_pixel != inactive_pixel
    assert inactive_pixel[:3] == (30, 70, 120)

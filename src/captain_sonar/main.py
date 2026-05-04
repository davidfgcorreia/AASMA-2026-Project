from __future__ import annotations

import argparse
import os
import random

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
from .event_log import EventLogger
from .game_loop import GameLoop
from .game_state import GameState, SubmarineState
from .map_loader import load_map
from .renderer import Renderer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="assets/maps/default_map.json")
    parser.add_argument("--log", default="logs/game_log.jsonl")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--two-human", action="store_true", default=True, help="Enable two human teams (default)")
    parser.add_argument("--ai-red", action="store_true", help="Use AI for RED team instead")
    parser.add_argument(
        "--start",
        choices=("default", "swap", "interactive"),
        help="Starting positions: default, swap, or interactive prompt",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    # Load map before prompting for starting positions
    map_data = load_map(args.map)

    def choose_start_positions(map_data, start_mode: str | None, surface: "pygame.Surface", renderer):
        # default: BLUE top-left, RED bottom-right
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

        # GUI interactive selection using pygame: click map cells for BLUE then RED.
        # Create a temporary state for rendering only.
        temp_subs = {**default}
        class TempState:
            def __init__(self, subs):
                self.subs = subs
                self.mines = []
                self.gauges = {}
                self.breakdowns = {}
                self.turn = 0
                self.game_over = False
                self.winner = None

        state = TempState(temp_subs)

        placing = ["BLUE", "RED"]
        index = 0
        clock = __import__("pygame").time.Clock()
        selecting = True
        cursor = None
        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit()
                if event.type == pygame.MOUSEMOTION:
                    mx, my = event.pos
                    ox, oy = renderer._map_origin()
                    lx = mx - ox
                    ly = my - oy
                    if lx >= 0 and ly >= 0:
                        gx = int(lx // TILE_SIZE)
                        gy = int(ly // TILE_SIZE)
                        if 0 <= gx < map_data.width and 0 <= gy < map_data.height:
                            cursor = (gx, gy)
                        else:
                            cursor = None
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    ox, oy = renderer._map_origin()
                    lx = mx - ox
                    ly = my - oy
                    if lx >= 0 and ly >= 0:
                        gx = int(lx // TILE_SIZE)
                        gy = int(ly // TILE_SIZE)
                        if 0 <= gx < map_data.width and 0 <= gy < map_data.height:
                            team = placing[index]
                            state.subs[team] = SubmarineState(x=gx, y=gy)
                            index += 1
                            if index >= len(placing):
                                selecting = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return default

            # If selection just finished, exit before rendering instructions
            if not selecting:
                break

            # draw map surface only
            surface.fill((18, 22, 28))
            map_surf = renderer._compose_map_surface(state, {"cursor": cursor})
            surface.blit(map_surf, (WINDOW_PADDING, WINDOW_PADDING))
            # draw instruction text
            font = pygame.font.SysFont("Arial", 18)
            instr = f"Click cell for {placing[index]} (Esc = cancel)"
            txt = font.render(instr, True, (240, 240, 240))
            surface.blit(txt, (10, 10))
            pygame.display.flip()
            clock.tick(30)

        return {team: SubmarineState(x=sub.x, y=sub.y) for team, sub in state.subs.items()}

    pygame.init()
    map_pixel_width = map_data.width * TILE_SIZE + MAP_MARGIN_X + MAP_INNER_PADDING_RIGHT
    map_pixel_height = map_data.height * TILE_SIZE + MAP_MARGIN_Y + MAP_INNER_PADDING_BOTTOM
    width = WINDOW_PADDING * 3 + map_pixel_width + PANEL_WIDTH
    height = WINDOW_PADDING * 2 + map_pixel_height
    surface = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Captain Sonar Prototype")
    renderer = Renderer(surface, map_data, background_path=MAP_BACKGROUND_PATH)
    subs = choose_start_positions(map_data, args.start, surface, renderer)
    state = GameState(map_data=map_data, subs=subs)
    log_dir = os.path.dirname(args.log)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    logger = EventLogger(args.log)
    two_human_teams = not args.ai_red
    loop = GameLoop(state, renderer, logger, seed=args.seed, map_name=args.map, two_human_teams=two_human_teams)
    loop.run()


if __name__ == "__main__":
    main()

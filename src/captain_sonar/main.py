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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    pygame.init()
    map_data = load_map(args.map)
    map_pixel_width = map_data.width * TILE_SIZE + MAP_MARGIN_X + MAP_INNER_PADDING_RIGHT
    map_pixel_height = map_data.height * TILE_SIZE + MAP_MARGIN_Y + MAP_INNER_PADDING_BOTTOM
    width = WINDOW_PADDING * 3 + map_pixel_width + PANEL_WIDTH
    height = WINDOW_PADDING * 2 + map_pixel_height
    surface = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Captain Sonar Prototype")

    subs = {
        "BLUE": SubmarineState(x=1, y=1),
        "RED": SubmarineState(x=map_data.width - 2, y=map_data.height - 2),
    }
    state = GameState(map_data=map_data, subs=subs)
    renderer = Renderer(surface, map_data, background_path=MAP_BACKGROUND_PATH)
    log_dir = os.path.dirname(args.log)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    logger = EventLogger(args.log)
    two_human_teams = not args.ai_red
    loop = GameLoop(state, renderer, logger, seed=args.seed, map_name=args.map, two_human_teams=two_human_teams)
    loop.run()


if __name__ == "__main__":
    main()

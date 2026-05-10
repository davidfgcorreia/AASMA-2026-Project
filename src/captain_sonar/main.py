from __future__ import annotations

import argparse
import os
import random

import pygame

from agents.manager import TeamAgentManager

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
from .game_state import GameState
from .map_loader import load_map
from .renderer import Renderer
from .startup import choose_start_positions, load_team_play_types


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="assets/maps/default_map.json")
    parser.add_argument("--log", default="logs/game_log.jsonl")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument(
        "--play-types",
        default="assets/team_play_types.json",
        help="JSON file describing per-team play types (human/agent)",
    )
    parser.add_argument(
        "--start",
        choices=("default", "swap", "interactive"),
        help="Starting positions: default, swap, or interactive prompt",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    map_data = load_map(args.map)

    pygame.init()
    map_pixel_width = map_data.width * TILE_SIZE + MAP_MARGIN_X + MAP_INNER_PADDING_RIGHT
    map_pixel_height = map_data.height * TILE_SIZE + MAP_MARGIN_Y + MAP_INNER_PADDING_BOTTOM
    width = WINDOW_PADDING * 3 + map_pixel_width + PANEL_WIDTH
    height = WINDOW_PADDING * 2 + map_pixel_height
    surface = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Captain Sonar Prototype")
    renderer = Renderer(surface, map_data, background_path=MAP_BACKGROUND_PATH)
    team_play_types = load_team_play_types(args.play_types)
    agent_managers = {
        team: TeamAgentManager(team)
        for team, play_type in team_play_types.items()
        if play_type == "agent"
    }

    def agent_team_picker(team: str, map_data, confirmed):
        manager = agent_managers.get(team)
        if manager is None:
            return None
        return manager.choose_start_position(map_data, confirmed)

    subs = choose_start_positions(
        map_data,
        args.start,
        surface,
        renderer,
        team_picker=agent_team_picker,
        play_types_path=args.play_types,
    )
    state = GameState(map_data=map_data, subs=subs)
    log_dir = os.path.dirname(args.log)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    logger = EventLogger(args.log)
    loop = GameLoop(
        state,
        renderer,
        logger,
        seed=args.seed,
        map_name=args.map,
        team_play_types=team_play_types,
        agent_managers=agent_managers,
    )
    loop.run()


if __name__ == "__main__":
    main()

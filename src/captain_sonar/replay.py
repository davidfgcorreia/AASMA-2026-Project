from __future__ import annotations

import argparse
import json
import time
from typing import Dict, List

import pygame

from .actions import action_from_dict, order_actions
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
from .game_state import GameState, SubmarineState
from .map_loader import load_map
from .renderer import Renderer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="assets/maps/default_map.json")
    parser.add_argument("--log", default="logs/game_log.jsonl")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--delay", type=float, default=0.75)
    return parser.parse_args()


def load_log(path: str) -> tuple[dict | None, List[dict]]:
    meta = None
    turns: List[dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            if payload.get("type") == "meta":
                meta = payload
                continue
            turns.append(payload)
    return meta, turns


def build_state(map_path: str, meta: dict | None) -> GameState:
    map_data = load_map(map_path)
    if meta and "subs" in meta:
        subs = {
            team: SubmarineState(x=pos["x"], y=pos["y"])
            for team, pos in meta.get("subs", {}).items()
        }
    else:
        subs = {
            "BLUE": SubmarineState(x=1, y=1),
            "RED": SubmarineState(x=map_data.width - 2, y=map_data.height - 2),
        }
    return GameState(map_data=map_data, subs=subs)


def apply_turn(state: GameState, turn: dict) -> None:
    actions = [action_from_dict(item) for item in turn.get("actions", [])]
    ordered = order_actions(actions)
    state.apply_actions(ordered)


def main() -> None:
    args = parse_args()
    meta, turns = load_log(args.log)
    state = build_state(args.map, meta)

    pygame.init()
    map_pixel_width = state.map_data.width * TILE_SIZE + MAP_MARGIN_X + MAP_INNER_PADDING_RIGHT
    map_pixel_height = state.map_data.height * TILE_SIZE + MAP_MARGIN_Y + MAP_INNER_PADDING_BOTTOM
    width = WINDOW_PADDING * 3 + map_pixel_width + PANEL_WIDTH
    height = WINDOW_PADDING * 2 + map_pixel_height
    surface = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Captain Sonar Replay")
    renderer = Renderer(surface, state.map_data, background_path=MAP_BACKGROUND_PATH)

    clock = pygame.time.Clock()
    index = 0
    auto = args.auto
    last_step = time.time()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    auto = False
                    if index < len(turns):
                        apply_turn(state, turns[index])
                        index += 1
                if event.key == pygame.K_a:
                    auto = not auto
        if auto and index < len(turns):
            if time.time() - last_step >= args.delay:
                apply_turn(state, turns[index])
                index += 1
                last_step = time.time()
        renderer.draw(state, {"queue": [], "active_action": None, "cursor": None})
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()

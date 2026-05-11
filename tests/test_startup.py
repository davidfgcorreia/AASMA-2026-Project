from captain_sonar.config import MAP_MARGIN_X, MAP_MARGIN_Y, TILE_SIZE
from captain_sonar.map_loader import MapData
from captain_sonar.game_state import GameState, SubmarineState
import captain_sonar.startup as startup_module
from captain_sonar.renderer import Renderer
from captain_sonar.startup import (
    choose_single_team_start_position,
    choose_start_positions,
    load_team_play_types,
)
import captain_sonar.main as main_module

import json
import pygame
import pytest


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


def test_renderer_only_shows_active_team_mine_count_in_panel():
    pygame.init()
    map_data = MapData(width=6, height=5, tiles=[["."] * 6 for _ in range(5)])
    surface = pygame.Surface((800, 600))
    renderer = Renderer(surface, map_data, background_path=None)

    rendered_texts = []

    class DummyFont:
        def render(self, text, *_args, **_kwargs):
            rendered_texts.append(text)
            return pygame.Surface((1, 1))

    renderer.font = DummyFont()
    state = GameState(
        map_data=map_data,
        subs={"BLUE": SubmarineState(x=1, y=1), "RED": SubmarineState(x=4, y=3)},
    )
    state.mines = [
        type("Mine", (), {"x": 1, "y": 1, "owner": "BLUE"})(),
        type("Mine", (), {"x": 4, "y": 3, "owner": "RED"})(),
    ]

    renderer._draw_mines_status(0, 0, state, {"active_team": "BLUE"})

    assert "BLUE: 1 deployed" in rendered_texts
    assert not any(text.startswith("RED:") for text in rendered_texts)



def test_choose_start_positions_mixed_agent_and_human(monkeypatch, tmp_path):
    map_data = MapData(width=6, height=5, tiles=[["."] * 6 for _ in range(5)])
    surface = None
    renderer = None
    config_path = tmp_path / "play_types.json"
    config_path.write_text(json.dumps({"BLUE": "agent", "RED": "human"}), encoding="utf-8")

    def picker(team, _map_data, _confirmed):
        if team == "BLUE":
            return (1, 1)
        return None

    def human_picker(_map_data, team, _surface, _renderer):
        assert team == "RED"
        return SubmarineState(x=4, y=3)

    monkeypatch.setattr(startup_module, "choose_human_start_position", human_picker)

    picked = choose_start_positions(
        map_data,
        start_mode=None,
        surface=surface,
        renderer=renderer,
        team_picker=picker,
        play_types_path=str(config_path),
    )

    assert picked["BLUE"].x == 1
    assert picked["BLUE"].y == 1
    assert picked["RED"].x == 4
    assert picked["RED"].y == 3


def test_load_team_play_types_from_json(tmp_path):
    config_path = tmp_path / "play_types.json"
    config_path.write_text(json.dumps({"blue": "human", "RED": "agent"}), encoding="utf-8")

    loaded = load_team_play_types(str(config_path))

    assert loaded["BLUE"] == "human"
    assert loaded["RED"] == "agent"


def test_choose_start_positions_uses_play_types_json(monkeypatch, tmp_path):
    pygame.init()
    map_data = MapData(width=6, height=5, tiles=[["."] * 6 for _ in range(5)])
    surface = pygame.display.set_mode((800, 600))
    renderer = Renderer(surface, map_data, background_path=None)
    config_path = tmp_path / "play_types.json"
    config_path.write_text(json.dumps({"BLUE": "agent", "RED": "human"}), encoding="utf-8")

    ox, oy = renderer._map_origin()
    red_click = (ox + 4 * TILE_SIZE + 1, oy + 3 * TILE_SIZE + 1)
    event_batches = [
        [
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": red_click, "button": 1}),
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}),
        ],
    ]

    def fake_event_get():
        if event_batches:
            return event_batches.pop(0)
        return []

    monkeypatch.setattr(pygame.event, "get", fake_event_get)

    calls = []

    def picker(team, _map_data, _confirmed):
        calls.append(team)
        if team == "BLUE":
            return (1, 1)
        return None

    picked = choose_start_positions(
        map_data,
        start_mode=None,
        surface=surface,
        renderer=renderer,
        team_picker=picker,
        play_types_path=str(config_path),
    )

    assert calls == ["BLUE"]
    assert picked["BLUE"].x == 1
    assert picked["BLUE"].y == 1
    assert picked["RED"].x == 4
    assert picked["RED"].y == 3


def test_choose_single_team_start_position_rejects_overlap():
    map_data = MapData(width=6, height=5, tiles=[["."] * 6 for _ in range(5)])
    confirmed = {"BLUE": SubmarineState(x=1, y=1)}

    def picker(_team, _map_data, _confirmed):
        return (1, 1)

    with pytest.raises(ValueError, match="overlaps"):
        choose_single_team_start_position(
            map_data=map_data,
            team="RED",
            confirmed=confirmed,
            picker=picker,
        )


def test_main_forwards_play_types_path(monkeypatch, tmp_path):
    play_types_path = tmp_path / "play_types.json"
    play_types_path.write_text(json.dumps({"BLUE": "human", "RED": "agent"}), encoding="utf-8")

    captured = {}

    def fake_parse_args():
        return type(
            "Args",
            (),
            {
                "map": "assets/maps/default_map.json",
                "log": str(tmp_path / "game_log.jsonl"),
                "seed": 1337,
                "two_human": True,
                "ai_red": False,
                "play_types": str(play_types_path),
                "start": None,
            },
        )()

    class DummyRenderer:
        def __init__(self, *args, **kwargs):
            pass

    class DummyGameLoop:
        def __init__(self, *args, **kwargs):
            captured["game_loop_kwargs"] = kwargs

        def run(self):
            return None

    def fake_choose_start_positions(map_data, start_mode, surface, renderer, team_picker=None, play_types_path=None):
        captured["play_types_path"] = play_types_path
        return {"BLUE": SubmarineState(x=1, y=1), "RED": SubmarineState(x=4, y=3)}

    monkeypatch.setattr(main_module, "parse_args", fake_parse_args)
    monkeypatch.setattr(main_module, "Renderer", DummyRenderer)
    monkeypatch.setattr(main_module, "GameLoop", DummyGameLoop)
    monkeypatch.setattr(main_module, "choose_start_positions", fake_choose_start_positions)
    monkeypatch.setattr(main_module.pygame, "init", lambda: None)
    monkeypatch.setattr(main_module.pygame.display, "set_mode", lambda size: object())
    monkeypatch.setattr(main_module.pygame.display, "set_caption", lambda text: None)

    main_module.main()

    assert captured["play_types_path"] == str(play_types_path)
    assert captured["game_loop_kwargs"]["team_play_types"]["BLUE"] == "human"
    assert captured["game_loop_kwargs"]["team_play_types"]["RED"] == "agent"

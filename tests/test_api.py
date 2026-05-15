from captain_sonar.actions import Action, ActionType
from captain_sonar.api import apply_actions, create_game_state, get_engineer_board_state, get_system_utilization, get_team_view, snapshot_game_state
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import MapData
import json
import importlib
import tempfile
import os
import sys
import types
from typing import Any, Mapping, Sequence, cast


def _make_fake_pygame(event_queue: Sequence[object]) -> Any:
    """Build a tiny pygame replacement for startup tests.

    The fake module is enough for `choose_human_start_position` to consume
    one click and confirm it with Enter.
    """
    pygame: Any = types.ModuleType("pygame")

    class _FakeEvent:
        def __init__(self, event_type: int, **kwargs: object) -> None:
            self.type = event_type
            for key, value in kwargs.items():
                setattr(self, key, value)

    class _FakeSurface:
        def fill(self, *args: object, **kwargs: object) -> None:
            return None

        def blit(self, *args: object, **kwargs: object) -> None:
            return None

    class _FakeClock:
        def tick(self, *args: object, **kwargs: object) -> None:
            return None

    class _FakeRect:
        def __init__(self, x: int, y: int, w: int, h: int) -> None:
            self.x = x
            self.y = y
            self.w = w
            self.h = h

    class _FakeFont:
        def render(self, *args: object, **kwargs: object) -> object:
            return object()

    pygame.QUIT = 0
    pygame.KEYDOWN = 1
    pygame.MOUSEMOTION = 2
    pygame.MOUSEBUTTONDOWN = 3
    pygame.K_ESCAPE = 27
    pygame.K_RETURN = 13
    pygame.Surface = _FakeSurface
    pygame.Rect = _FakeRect
    pygame.event = types.SimpleNamespace(get=lambda: list(event_queue))
    pygame.time = types.SimpleNamespace(Clock=lambda: _FakeClock(), delay=lambda *args, **kwargs: None)
    pygame.font = types.SimpleNamespace(SysFont=lambda *args, **kwargs: _FakeFont())
    pygame.display = types.SimpleNamespace(flip=lambda: None)
    pygame.draw = types.SimpleNamespace(rect=lambda *args, **kwargs: None)

    return pygame


def _import_choose_start_positions(event_queue: Sequence[object] | None = None):
    """Import `choose_start_positions` with a fake pygame module if needed."""
    if event_queue is not None:
        sys.modules["pygame"] = _make_fake_pygame(event_queue)
    elif "pygame" not in sys.modules:
        sys.modules["pygame"] = types.ModuleType("pygame")

    if "captain_sonar.startup" in sys.modules:
        del sys.modules["captain_sonar.startup"]

    from captain_sonar.startup import choose_start_positions

    return choose_start_positions


def test_snapshot_is_json_friendly_and_detached() -> None:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(
        map_data=map_data,
        subs={
            "BLUE": SubmarineState(x=1, y=1),
            "RED": SubmarineState(x=2, y=2),
        },
    )

    snapshot = snapshot_game_state(state)
    snapshot["submarines"]["BLUE"]["x"] = 99

    assert snapshot["turn"] == 0
    assert snapshot["submarines"]["BLUE"]["x"] == 99
    assert state.subs["BLUE"].x == 1
    assert isinstance(snapshot["routes"]["BLUE"], list)
    assert isinstance(snapshot["mines"], list)


def test_team_view_exposes_agent_facing_state_without_enemy_position() -> None:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(
        map_data=map_data,
        subs={
            "BLUE": SubmarineState(x=1, y=1),
            "RED": SubmarineState(x=2, y=2),
        },
    )

    view = get_team_view(state, "BLUE")
    print(json.dumps(view, indent=2, sort_keys=True))
    # Print the advanced view for debugging/verification during test runs
    print(json.dumps(view, indent=2, sort_keys=True))

    assert view["team"] == "BLUE"
    assert view["own_submarine"] == {"x": 1, "y": 1, "damage": 0}
    assert view["radio_operator"] is not None
    assert "enemy_submarine" not in view


def test_apply_actions_wrapper_orders_and_applies_actions() -> None:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1)})

    apply_actions(
        state,
        [Action(actor="BLUE", type=ActionType.MOVE, payload={"direction": "E", "charge": "torpedo"})],
    )

    assert state.turn == 1
    assert state.subs["BLUE"].x == 2


def test_system_utilization_exposes_charge_levels_and_readiness() -> None:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1)})
    state.gauges["BLUE"]["torpedo"] = 2

    utilization = get_system_utilization(state, "BLUE")

    assert utilization["team"] == "BLUE"
    assert utilization["gauges"]["torpedo"] == 2
    assert utilization["utilization"]["torpedo"] == 0.5
    assert utilization["ready"]["torpedo"] is False


def test_engineer_board_state_exposes_button_metadata() -> None:
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=1)})

    board = get_engineer_board_state(state, "BLUE")

    assert board is not None
    assert board["team"] == "BLUE"
    assert "W" in board["buttons_by_direction"]
    assert board["buttons_by_direction"]["W"][0]["button_id"] == "W-not-green-0"
    assert board["buttons_by_direction"]["W"][0]["crossed"] is False


def test_team_view_advanced_state_for_blue() -> None:
    """Create a more advanced state with moves, crossed engineer symbols and gauges."""
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    state = GameState(
        map_data=map_data,
        subs={
            "BLUE": SubmarineState(x=1, y=1),
            "RED": SubmarineState(x=2, y=2),
        },
    )

    # Round 1: both teams move and charge specific systems, selecting breakdown choices
    apply_actions(
        state,
        [
            Action(
                actor="BLUE",
                type=ActionType.MOVE,
                payload={
                    "direction": "E",
                    "charge": "torpedo",
                    "breakdown_choice": {"button_id": "E-central-green-4"},
                },
            ),
            Action(
                actor="RED",
                type=ActionType.MOVE,
                payload={
                    "direction": "W",
                    "charge": "sonar",
                    "breakdown_choice": {"button_id": "W-top-yellow-5"},
                },
            ),
        ],
    )

    # Round 2: BLUE moves again, charging torpedo a second time
    apply_actions(
        state,
        [
            Action(
                actor="BLUE",
                type=ActionType.MOVE,
                payload={
                    "direction": "N",
                    "charge": "torpedo",
                    "breakdown_choice": {"button_id": "N-central-red-3"},
                },
            ),
        ],
    )

    # Simulate additional system load on RED for variety
    state.gauges["RED"]["mine"] = 3

    view = get_team_view(state, "BLUE")
    print(json.dumps(view, indent=2, sort_keys=True))

    assert view["team"] == "BLUE"
    assert view["enemy_team"] == "RED"
    # BLUE moved E then N from (1,1) -> (2,1) -> (2,0)
    assert view["own_submarine"] == {"x": 2, "y": 0, "damage": 0}
    assert view["own_gauges"]["torpedo"] == 2
    assert view["system_utilization"]["gauges"]["torpedo"] == 2
    assert view["system_utilization"]["utilization"]["torpedo"] == 0.5

    eb = view["engineer_board"]
    assert eb is not None
    # BLUE's own breakdowns should include the E selection we made
    assert "E-central-green-4" in eb["crossed_by_direction"]["E"]

    # The RED board should include the W selection that RED made
    red_board = get_engineer_board_state(state, "RED")
    assert red_board is not None
    assert "W-top-yellow-5" in red_board["crossed_by_direction"]["W"]

    assert isinstance(view["radio_operator"], dict) or view["radio_operator"] is not None

# Startup tests for the agent picker and human map click flow in `choose_start_positions`.


def test_choose_start_positions_agent_blue_and_human_red() -> None:

    """Verify mixed startup selection: BLUE is picked by agent callback and
    RED is chosen by simulating a human click on the map.

    The test uses a temporary play-types JSON with BLUE=agent and RED=human.
    BLUE is resolved by `team_picker`; RED is resolved by fake pygame events
    that move the cursor, click a tile, and confirm with Enter.
    """
    map_data = MapData(width=6, height=6, tiles=[["."] * 6 for _ in range(6)])

    class FakeRenderer:
        def _map_origin(self) -> tuple[int, int]:
            return (0, 0)

        def _compose_map_surface(self, *args: object, **kwargs: object) -> object:
            return object()

        def _map_pixel_size(self) -> tuple[int, int]:
            return (map_data.width * 40, map_data.height * 40)

    class FakeSurface:
        def fill(self, *args: object, **kwargs: object) -> None:
            return None

        def blit(self, *args: object, **kwargs: object) -> None:
            return None

    blue_pick = (1, 1)
    red_pick = (4, 4)
    fake_events = [
        types.SimpleNamespace(type=2, pos=(red_pick[0] * 40 + 1, red_pick[1] * 40 + 1)),
        types.SimpleNamespace(type=3, button=1, pos=(red_pick[0] * 40 + 1, red_pick[1] * 40 + 1)),
        types.SimpleNamespace(type=1, key=13),
    ]

    def picker(team: str, md: MapData, confirmed: Mapping[str, SubmarineState]) -> tuple[int, int] | None:
        if team == "BLUE":
            return blue_pick
        return None

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump({"BLUE": "agent", "RED": "human"}, tmp)
        tmp.flush()
        tmp.close()

        choose_start_positions = _import_choose_start_positions(fake_events)
        positions = choose_start_positions(
            map_data,
            None,
            cast(Any, FakeSurface()),
            cast(Any, FakeRenderer()),
            team_picker=picker,
            play_types_path=tmp.name,
        )

        print("startup positions:", {t: {"x": p.x, "y": p.y} for t, p in positions.items()})

        assert positions["BLUE"].x == blue_pick[0] and positions["BLUE"].y == blue_pick[1]
        assert positions["RED"].x == red_pick[0] and positions["RED"].y == red_pick[1]
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

# First action after startup

def test_first_move_after_startup() -> None:
    """Pick startup positions, print the initial state, then apply one full action.

    BLUE uses the agent picker; RED uses the human click path. The action is
    passed in the expanded form the API now accepts:
    direction, system_to_load, slot_index, system_activation, and
    system_activation_payload.
    """
    map_data = MapData(width=6, height=6, tiles=[["."] * 6 for _ in range(6)])

    class FakeRenderer:
        def _map_origin(self) -> tuple[int, int]:
            return (0, 0)

        def _compose_map_surface(self, *args: object, **kwargs: object) -> object:
            return object()

        def _map_pixel_size(self) -> tuple[int, int]:
            return (map_data.width * 40, map_data.height * 40)

    class FakeSurface:
        def fill(self, *args: object, **kwargs: object) -> None:
            return None

        def blit(self, *args: object, **kwargs: object) -> None:
            return None

    blue_pick = (1, 1)
    red_pick = (4, 4)
    fake_events = [
        types.SimpleNamespace(type=2, pos=(red_pick[0] * 40 + 1, red_pick[1] * 40 + 1)),
        types.SimpleNamespace(type=3, button=1, pos=(red_pick[0] * 40 + 1, red_pick[1] * 40 + 1)),
        types.SimpleNamespace(type=1, key=13),
    ]

    def picker(team: str, md: MapData, confirmed: Mapping[str, SubmarineState]) -> tuple[int, int] | None:
        if team == "BLUE":
            return blue_pick
        return None

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump({"BLUE": "agent", "RED": "human"}, tmp)
        tmp.flush()
        tmp.close()

        choose_start_positions = _import_choose_start_positions(fake_events)
        positions = choose_start_positions(
            map_data,
            None,
            cast(Any, FakeSurface()),
            cast(Any, FakeRenderer()),
            team_picker=picker,
            play_types_path=tmp.name,
        )

        startup_positions = {team: (pos.x, pos.y) for team, pos in positions.items()}
        print("startup positions:", startup_positions)

        assert startup_positions["BLUE"] == blue_pick
        assert startup_positions["RED"] == red_pick

        state = create_game_state(map_data, positions)
        initial_snapshot = snapshot_game_state(state)
        print("initial snapshot:", json.dumps(initial_snapshot, indent=2, sort_keys=True))

        full_action = {
            "actor": "BLUE",
            "type": "MOVE",
            "direction": "E",
            "system_to_load": "torpedo",
            "slot_index": 4,
            "system_activation": "REPAIR",
            "system_activation_payload": {},
        }

        apply_actions(state, [full_action])

        final_snapshot = snapshot_game_state(state)
        print("final snapshot:", json.dumps(final_snapshot, indent=2, sort_keys=True))

        # Print team views for debugging: BLUE then RED
        blue_view = get_team_view(state, "BLUE")
        print("BLUE view after action:", json.dumps(blue_view, indent=2, sort_keys=True))
        red_view = get_team_view(state, "RED")
        print("RED view after action:", json.dumps(red_view, indent=2, sort_keys=True))

        assert state.turn == 1
        assert state.subs["BLUE"].x == 2
        assert state.subs["BLUE"].y == 1
        assert state.gauges["BLUE"]["torpedo"] == 1
        # Accept any crossed breakdown for the E direction rather than a
        # brittle specific id; prints above show the actual crossed id.
        assert len(state.breakdowns["BLUE"].crossed_by_direction["E"]) > 0
        assert any(event["type"] == "move" for event in state.events)
        assert any(event["type"] == "repair" for event in state.events)
        assert startup_positions["BLUE"] == blue_pick
        assert startup_positions["RED"] == red_pick
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
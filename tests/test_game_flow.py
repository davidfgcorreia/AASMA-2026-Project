"""
Integration tests for turn-by-turn game flow.

Each test drives GameState directly (no UI or game loop) and runs without a
display.  Coordinates follow the convention (x=column, y=row); tiles are
indexed tiles[y][x].  The starting position is always included in the
submarine's route set, so the first move cannot return to it.
"""
from captain_sonar.actions import Action, ActionType
from captain_sonar.config import SURFACE_SKIP_TURNS
from captain_sonar.engineer_layout import ENGINEER_BUTTON_SPECS
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import MapData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def plain_map(w: int = 6, h: int = 6) -> MapData:
    return MapData(width=w, height=h, tiles=[["." ] * w for _ in range(h)])


def move(actor, direction, charge="torpedo"):
    return Action(actor=actor, type=ActionType.MOVE,
                  payload={"direction": direction, "charge": charge})


def torpedo(actor, tx, ty):
    return Action(actor=actor, type=ActionType.TORPEDO,
                  payload={"target": {"x": tx, "y": ty}})


def mine(actor, tx, ty):
    return Action(actor=actor, type=ActionType.MINE,
                  payload={"target": {"x": tx, "y": ty}})


def trigger(actor, tx, ty):
    return Action(actor=actor, type=ActionType.TRIGGER_MINE,
                  payload={"target": {"x": tx, "y": ty}})


def surface(actor):
    return Action(actor=actor, type=ActionType.SURFACE, payload={})


def two_sub_state(bx=0, by=0, rx=5, ry=5):
    return GameState(
        map_data=plain_map(),
        subs={"BLUE": SubmarineState(x=bx, y=by), "RED": SubmarineState(x=rx, y=ry)},
    )


# ---------------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------------

def test_basic_movement():
    """Submarines move and positions update correctly."""
    state = two_sub_state(bx=0, by=0, rx=5, ry=5)
    state.apply_actions([move("BLUE", "E")])
    state.apply_actions([move("RED", "W")])

    assert state.subs["BLUE"].x == 1
    assert state.subs["RED"].x == 4


def test_cannot_revisit_own_route():
    """Moving back onto a previously visited cell is rejected without surfacing."""
    state = two_sub_state(bx=1, by=1)
    state.apply_actions([move("BLUE", "E")])   # → (2,1)

    state.apply_actions([move("BLUE", "W")])   # (1,1) is in route

    assert state.subs["BLUE"].x == 2           # position unchanged
    assert state.skip_turns.get("BLUE", 0) == 0  # not surfaced
    assert any(e["type"] == "action_rejected" for e in state.events)


# ---------------------------------------------------------------------------
# Blackout
# ---------------------------------------------------------------------------

def test_blocked_move_without_blackout_is_rejected_not_surfaced():
    """A blocked direction with valid alternatives → rejected, no forced surface."""
    state = two_sub_state(bx=1, by=1)
    state.apply_actions([move("BLUE", "N")])   # → (1,0)

    # At (1,0): N=out-of-bounds, S=(1,1) in route; E=(2,0) and W=(0,0) are free
    state.apply_actions([move("BLUE", "N")])

    assert state.subs["BLUE"].y == 0
    assert state.skip_turns.get("BLUE", 0) == 0
    assert any(e["type"] == "action_rejected" for e in state.events)


def test_blackout_forces_surface_when_all_directions_blocked():
    """When every neighbour is blocked the next move triggers an immediate surface."""
    # 3-cell corridor; BLUE starts at x=1 (middle)
    map_data = MapData(width=3, height=1, tiles=[[".", ".", "."]])
    state = GameState(map_data=map_data, subs={"BLUE": SubmarineState(x=1, y=0)})

    state.apply_actions([move("BLUE", "W")])   # → (0,0); route = {(1,0),(0,0)}
    assert state.skip_turns.get("BLUE", 0) == 0  # not surfaced yet

    # At (0,0): W/N/S out-of-bounds, E=(1,0) in route → all four blocked
    state.apply_actions([move("BLUE", "E")])
    assert state.skip_turns["BLUE"] == SURFACE_SKIP_TURNS


# ---------------------------------------------------------------------------
# Torpedo
# ---------------------------------------------------------------------------

def test_torpedo_direct_hit():
    """Torpedo landing on the target cell deals 2 damage and consumes the gauge."""
    state = GameState(
        map_data=plain_map(),
        subs={"BLUE": SubmarineState(x=0, y=2), "RED": SubmarineState(x=3, y=2)},
    )
    state.gauges["BLUE"]["torpedo"] = 4

    state.apply_actions([torpedo("BLUE", 3, 2)])

    assert state.subs["RED"].damage == 2
    assert state.gauges["BLUE"]["torpedo"] == 0


def test_torpedo_indirect_hit():
    """Torpedo landing one cell away from RED deals 1 damage."""
    state = GameState(
        map_data=plain_map(),
        subs={"BLUE": SubmarineState(x=0, y=0), "RED": SubmarineState(x=3, y=0)},
    )
    state.gauges["BLUE"]["torpedo"] = 4

    # Impact at (4,0) — RED at (3,0) is adjacent → indirect hit
    state.apply_actions([torpedo("BLUE", 4, 0)])

    assert state.subs["RED"].damage == 1


def test_torpedo_gauge_fills_through_moves():
    """Four moves with charge='torpedo' fill the gauge to 4."""
    state = two_sub_state(bx=0, by=0)

    for direction in ["S", "E", "N", "E"]:    # non-backtracking path
        state.apply_actions([move("BLUE", direction, charge="torpedo")])

    assert state.gauges["BLUE"]["torpedo"] == 4


# ---------------------------------------------------------------------------
# Mine
# ---------------------------------------------------------------------------

def test_mine_drop_and_trigger_direct_hit():
    """BLUE drops a mine on RED's cell, moves away, triggers it: direct hit (2 damage)."""
    state = GameState(
        map_data=plain_map(),
        subs={"BLUE": SubmarineState(x=0, y=0), "RED": SubmarineState(x=1, y=0)},
    )
    state.gauges["BLUE"]["mine"] = 4

    state.apply_actions([mine("BLUE", 1, 0)])
    assert len(state.mines) == 1

    state.apply_actions([move("BLUE", "S")])    # move away
    state.apply_actions([trigger("BLUE", 1, 0)])

    assert state.subs["RED"].damage == 2
    assert len(state.mines) == 0


def test_mine_cannot_be_placed_on_own_route():
    """Dropping a mine on a previously visited cell is rejected."""
    # N and W auto-select green/radioactive breakdown symbols (not red),
    # so the mine system stays operational throughout.
    state = GameState(
        map_data=plain_map(),
        subs={"BLUE": SubmarineState(x=1, y=2), "RED": SubmarineState(x=5, y=5)},
    )
    state.gauges["BLUE"]["mine"] = 4

    state.apply_actions([move("BLUE", "N")])   # → (1,1); breakdown = N-not-green-0 (green)
    state.apply_actions([move("BLUE", "W")])   # → (0,1); breakdown = W-not-green-0 (green)
    # route = {(1,2),(1,1),(0,1)}; BLUE at (0,1)

    state.apply_actions([mine("BLUE", 1, 1)])  # (1,1) is in own route → blocked

    assert len(state.mines) == 0
    assert any(e.get("reason") == "mine cannot be placed on own route"
               for e in state.events)


def test_trigger_mine_does_not_count_as_system_activation():
    """Triggering a mine leaves last_action_system=False so a system can follow."""
    state = GameState(
        map_data=plain_map(),
        subs={"BLUE": SubmarineState(x=0, y=0), "RED": SubmarineState(x=5, y=5)},
    )
    state.gauges["BLUE"]["mine"] = 4

    state.apply_actions([mine("BLUE", 1, 0)])    # sets last_action_system=True
    state.apply_actions([move("BLUE", "S")])     # resets last_action_system=False
    state.apply_actions([trigger("BLUE", 1, 0)]) # must NOT flip it back to True

    assert state.last_action_system.get("BLUE", False) is False


# ---------------------------------------------------------------------------
# Surfacing
# ---------------------------------------------------------------------------

def test_voluntary_surface_clears_route_and_breakdowns():
    """Surfacing resets the route to the current cell and wipes all breakdowns."""
    state = two_sub_state(bx=0, by=0)
    state.apply_actions([move("BLUE", "E")])
    state.apply_actions([move("BLUE", "S")])
    assert len(state.routes["BLUE"]) == 3   # (0,0), (1,0), (1,1)

    state.breakdowns["BLUE"].crossed_by_direction["N"].add("N-central-red-3")

    state.apply_actions([surface("BLUE")])

    assert state.routes["BLUE"] == {(1, 1)}
    assert state.skip_turns["BLUE"] == SURFACE_SKIP_TURNS
    assert all(not s for s in state.breakdowns["BLUE"].crossed_by_direction.values())


def test_surfacing_skip_turns_not_decremented_by_apply_actions():
    """apply_actions must not touch skip_turns; decrement lives in the game loop."""
    state = two_sub_state(bx=0, by=0, rx=5, ry=5)
    state.apply_actions([surface("BLUE")])
    assert state.skip_turns["BLUE"] == SURFACE_SKIP_TURNS

    # Several RED moves must leave BLUE's counter untouched
    for _ in range(3):
        state.apply_actions([move("RED", "W")])

    assert state.skip_turns["BLUE"] == SURFACE_SKIP_TURNS


def test_surfaced_team_actions_are_skipped():
    """While skip_turns > 0 every action from the surfaced team is ignored."""
    state = two_sub_state(bx=0, by=0)
    state.apply_actions([surface("BLUE")])

    state.apply_actions([move("BLUE", "E")])

    assert state.subs["BLUE"].x == 0
    assert any(e["type"] == "action_skipped" and e["actor"] == "BLUE"
               for e in state.events)


# ---------------------------------------------------------------------------
# Engineer breakdowns
# ---------------------------------------------------------------------------

def test_circuit_self_repair_is_repeatable():
    """A circuit may self-repair more than once per surface period (bug fix #11)."""
    state = two_sub_state()
    top_ids = {
        spec.button_id
        for specs in ENGINEER_BUTTON_SPECS.values()
        for spec in specs
        if spec.circuit_part == "top"
    }

    def cross_top():
        for direction, crossed in state.breakdowns["BLUE"].crossed_by_direction.items():
            crossed.update(b for b in top_ids if b.startswith(f"{direction}-"))

    cross_top()
    assert "top_circuit" in state._repair_circuits("BLUE")

    cross_top()   # symbols were cleared; cross them again
    assert "top_circuit" in state._repair_circuits("BLUE")   # failed before the fix


# ---------------------------------------------------------------------------
# Silence
# ---------------------------------------------------------------------------

def test_silence_fails_cleanly_when_fully_blocked():
    """Silence with no room on the first step is rejected without consuming the gauge."""
    state = GameState(
        map_data=plain_map(3, 3),
        subs={"BLUE": SubmarineState(x=0, y=1)},
    )
    state.gauges["BLUE"]["silence"] = 4

    # West from (0,1) is immediately out-of-bounds
    state.apply_actions([Action(actor="BLUE", type=ActionType.SILENCE,
                                payload={"direction": "W", "steps": 2, "charge": "torpedo"})])

    assert state.subs["BLUE"].x == 0
    assert state.gauges["BLUE"]["silence"] == 4   # gauge untouched
    assert any(e.get("reason") == "silence path fully blocked" for e in state.events)


def test_silence_stops_early_but_still_activates():
    """Silence that hits a wall mid-path still consumes the gauge and moves as far as possible."""
    state = GameState(
        map_data=plain_map(3, 3),
        subs={"BLUE": SubmarineState(x=0, y=1)},
    )
    state.gauges["BLUE"]["silence"] = 4

    # Requesting 4 steps east but only (1,1) and (2,1) exist
    state.apply_actions([Action(actor="BLUE", type=ActionType.SILENCE,
                                payload={"direction": "E", "steps": 4, "charge": "torpedo"})])

    assert state.subs["BLUE"].x == 2              # stopped at right edge
    assert state.gauges["BLUE"]["silence"] == 0   # gauge consumed


# ---------------------------------------------------------------------------
# Full game end-to-end
# ---------------------------------------------------------------------------

def test_full_game_to_destruction():
    """
    BLUE fires two direct torpedoes (2 + 2 = 4 damage) to destroy RED.

    Gauge is pre-charged before each shot to keep the test focused on
    game-over logic rather than gauge mechanics (tested separately above).
    """
    # BLUE at (0,2), RED at (3,2) — same row, 3 spaces apart
    state = GameState(
        map_data=plain_map(),
        subs={"BLUE": SubmarineState(x=0, y=2), "RED": SubmarineState(x=3, y=2)},
    )
    state.gauges["BLUE"]["torpedo"] = 4

    # First torpedo — RED at 2 damage
    state.apply_actions([torpedo("BLUE", 3, 2)])
    assert state.subs["RED"].damage == 2
    assert not state.game_over

    # Move east to reset last_action_system; gauge tops up to 4 (already at cap after move)
    state.apply_actions([move("BLUE", "E", charge="torpedo")])  # BLUE → (1,2)
    state.gauges["BLUE"]["torpedo"] = 4

    # Second torpedo from (1,2) — same row, distance 2, direct hit
    state.apply_actions([torpedo("BLUE", 3, 2)])
    assert state.subs["RED"].damage == 4
    assert state.game_over
    assert state.winner == "BLUE"

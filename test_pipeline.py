"""End-to-end pipeline test through the new manager_api.collect_actions path.

Builds a TeamAgentManager with all four model agents, runs N turns, applies
each turn's actions to the GameState, and prints a summary per turn.
"""
import sys
import json
sys.path.insert(0, "src")

from agents.common.gemini import load_env_file
from agents.manager.manager import TeamAgentManager
from agents.captain.agent import ModelCaptainAgent
from agents.first_mate.agent import ModelFirstMateAgent
from agents.engineer.agent import ModelEngineerAgent
from agents.radio_operator.agent import RadioOperatorAgent
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import load_map
from captain_sonar.actions import order_actions

load_env_file("src/agents/.env")

NUM_TURNS = 1   # start small — free-tier Gemini is 15 RPM, each turn ~13 calls

# Build manager with all four model agents
manager = TeamAgentManager("BLUE")
manager.register_agent(ModelCaptainAgent("BLUE"), active=True)
manager.register_agent(ModelFirstMateAgent("BLUE"), active=True)
manager.register_agent(ModelEngineerAgent("BLUE"), active=True)
manager.register_agent(RadioOperatorAgent("BLUE"), active=True)

# Build game state directly
map_data = load_map("assets/maps/default_map.json")
state = GameState(
    map_data=map_data,
    subs={
        "BLUE": SubmarineState(x=1, y=1),
        "RED": SubmarineState(x=8, y=8),
    },
)

visited: list[tuple[int, int]] = []

for turn_idx in range(NUM_TURNS):
    print(f"\n{'='*60}")
    print(f"TURN {turn_idx + 1}")
    print(f"{'='*60}")

    record = manager.run_turn_cycle(state, max_iterations=1)
    actions = record.get("actions") or []

    print(f"  Returned {len(actions)} action(s):")
    for a in actions:
        print(f"    - type={a.type.name}  actor={a.actor}  payload={a.payload}")

    # Find the MOVE/SURFACE action and validate its shape
    move_action = next((a for a in actions if a.type.name in ("MOVE", "SURFACE")), None)
    if move_action and move_action.type.name == "MOVE":
        direction = move_action.payload.get("direction", "?")
        charge = move_action.payload.get("charge")
        bd = move_action.payload.get("breakdown_choice") or {}
        btn_id = bd.get("button_id")
        btn_prefix = btn_id.split("-")[0] if btn_id and "-" in btn_id else None

        print(f"\n  Direction : {direction}")
        print(f"  Charge    : {charge or '(missing)'}")
        print(f"  Button ID : {btn_id or '(missing)'}")
        if btn_prefix and btn_prefix != direction:
            print(f"  !! MISMATCH: button prefix '{btn_prefix}' != direction '{direction}'")
        elif btn_id and btn_prefix == direction:
            print(f"  OK Button prefix matches direction")

    # Apply actions to the game state
    success = True
    err = None
    try:
        state.apply_actions(order_actions(actions))
    except Exception as exc:
        success = False
        err = str(exc)

    print(f"\n  Apply success: {success}")
    if err:
        print(f"  Error: {err}")

    # Track position
    own_sub = state.subs.get("BLUE")
    pos = (own_sub.x, own_sub.y) if own_sub else ("?", "?")
    if pos in visited:
        print(f"  !! PATH REVISIT: position {pos} was already visited!")
    else:
        print(f"  OK Position {pos} (new)")
    visited.append(pos)

print(f"\n{'='*60}")
print(f"Done - {NUM_TURNS} turn(s) completed")
print(f"Route: {' -> '.join(str(p) for p in visited)}")

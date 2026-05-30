"""End-to-end pipeline test through the new manager_api.collect_actions path.

Runs one full turn cycle (turn_start -> iteration_cycle -> finalization -> send)
with all four model agents, applies the returned actions to the GameState, and
prints what came out. Also verifies the communications artifacts.
"""
import sys
sys.path.insert(0, "src")

from pathlib import Path

from agents.common.gemini import load_env_file
from agents.manager.manager import TeamAgentManager
from agents.captain.agent import ModelCaptainAgent
from agents.first_mate.agent import ModelFirstMateAgent
from agents.engineer.agent import ModelEngineerAgent
from agents.radio_operator.agent import ModelRadioOperatorAgent
from captain_sonar.game_state import GameState, SubmarineState
from captain_sonar.map_loader import load_map
from captain_sonar.actions import order_actions

load_env_file("src/agents/.env")

NUM_TURNS = 3  # free-tier Gemini is 15 RPM, ~13 calls per turn

# Build manager with all four model agents
manager = TeamAgentManager("BLUE")
manager.register_agent(ModelCaptainAgent("BLUE"), active=True)
manager.register_agent(ModelFirstMateAgent("BLUE"), active=True)
manager.register_agent(ModelEngineerAgent("BLUE"), active=True)
manager.register_agent(ModelRadioOperatorAgent("BLUE"), active=True)

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
comms_dir = Path("src/agents/manager/communications")

for turn_idx in range(NUM_TURNS):
    print(f"\n{'='*60}")
    print(f"TURN {turn_idx + 1}")
    print(f"{'='*60}")

    record = manager.run_turn_cycle(state, max_iterations=1)
    actions = record.get("actions") or []

    print(f"\nManager returned {len(actions)} action(s):")
    for a in actions:
        print(f"  - type={a.type.name}  actor={a.actor}  payload={a.payload}")

    # Inspect the MOVE/SURFACE action
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

    # Inspect communications artifacts produced this turn
    turn_label = turn_idx  # turn_id is 0 for turn 1 on a fresh state
    print(f"\nCommunications files produced:")
    if comms_dir.exists():
        produced = sorted(comms_dir.glob(f"to_*_blue_turn_{turn_label}.md"))
        if produced:
            for p in produced:
                print(f"  - {p.name}")
                text = p.read_text(encoding="utf-8")
                # Show just the first ~6 lines of each communications file
                for line in text.splitlines()[:6]:
                    print(f"      {line}")
        else:
            print("  (none — no questions were extracted from discussion outputs)")
    else:
        print("  (communications/ directory does not exist)")

    # Apply actions to the game state
    success = True
    err = None
    try:
        state.apply_actions(order_actions(actions))
    except Exception as exc:
        success = False
        err = str(exc)

    print(f"\nApply success: {success}")
    if err:
        print(f"  Error: {err}")

    own_sub = state.subs.get("BLUE")
    pos = (own_sub.x, own_sub.y) if own_sub else ("?", "?")
    marker = "!! PATH REVISIT" if pos in visited else "OK Position"
    print(f"{marker}: {pos}")
    visited.append(pos)

print(f"\n{'='*60}")
print(f"Done - {NUM_TURNS} turn(s) completed")
print(f"Route: {' -> '.join(str(p) for p in visited)}")

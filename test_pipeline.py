"""Full pipeline test: run 5 consecutive turn cycles with all model agents.

Verifies:
  - No revisited cells (path blindness fixed)
  - load_system always present on MOVE turns (fallback working)
  - engineer_button_id direction prefix always matches move direction (mismatch fixed)
"""
import sys
import json
sys.path.insert(0, "src")

from agents.common.gemini import load_env_file
from agents.manager.runtime import build_team_agent_manager, build_game_state

load_env_file("src/agents/.env")

NUM_TURNS = 5

state = build_game_state(
    "assets/maps/default_map.json",
    {"BLUE": (1, 1), "RED": (8, 8)},
)

manager = build_team_agent_manager("BLUE", use_model_agents=True)

visited: list[tuple[int, int]] = []

for turn_idx in range(NUM_TURNS):
    print(f"\n{'='*60}")
    print(f"TURN {turn_idx + 1}")
    print(f"{'='*60}")

    record = manager.run_turn_cycle(state, max_iterations=2)

    accepted = record.get("accepted") or []
    execution = record.get("execution") or {}

    # Pull the MOVE/SURFACE action out
    move_intent = None
    for a in accepted:
        if a.get("type") in ("MOVE", "SURFACE"):
            move_intent = a
            break

    if move_intent:
        payload = move_intent.get("payload") or {}
        direction = payload.get("direction", "?")
        charge = payload.get("charge", "—")
        bd = payload.get("breakdown_choice") or {}
        btn_id = bd.get("button_id", "—")
        btn_prefix = btn_id.split("-")[0] if "-" in btn_id else btn_id

        print(f"  Action type : {move_intent.get('type')}")
        print(f"  Direction   : {direction}")
        print(f"  Charge      : {charge}")
        print(f"  Button ID   : {btn_id}  (prefix={btn_prefix})")

        # Checks
        if move_intent.get("type") == "MOVE":
            if charge == "—":
                print("  ⚠ WARNING: load_system missing!")
            if btn_id == "—":
                print("  ⚠ WARNING: engineer_button_id missing!")
            elif btn_prefix != direction:
                print(f"  !! MISMATCH: button prefix '{btn_prefix}' != direction '{direction}'")
            else:
                print(f"  OK Button prefix matches direction")
    else:
        print("  (no MOVE/SURFACE in accepted)")

    exec_success = execution.get("success")
    exec_errors = execution.get("errors") or []
    exec_actions = execution.get("executed_actions") or []
    rejected = execution.get("rejected_intents") or []

    print(f"\n  Execution success : {exec_success}")
    if exec_errors:
        print(f"  Errors : {exec_errors}")
    if rejected:
        print(f"  Rejected intents  : {json.dumps(rejected, indent=4, default=str)}")

    # Track position
    own_sub = (state.subs.get("BLUE") or None)
    if own_sub is not None and hasattr(own_sub, "x"):
        pos = (own_sub.x, own_sub.y)
    else:
        pos = ("?", "?")

    if pos in visited:
        print(f"  !! PATH REVISIT: position {pos} was already visited!")
    else:
        print(f"  OK Position {pos} (new)")
    visited.append(pos)

print(f"\n{'='*60}")
print(f"Done — {NUM_TURNS} turns completed")
print(f"Route: {' -> '.join(str(p) for p in visited)}")

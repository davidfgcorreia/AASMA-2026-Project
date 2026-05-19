from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agents.manager.dev_state import (
    load_snapshot_file,
    load_possible_actions_file,
    PossibleActionsNavigator,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Developer inspector for snapshots and possible-actions files")
    parser.add_argument("--state-file", default=None, help="path to a snapshot JSON file (team view snapshot)")
    parser.add_argument("--possible-file", default=None, help="path to a possible-actions JSON file to navigate")
    parser.add_argument("--inspect", action="store_true", help="start interactive inspector REPL")
    parser.add_argument("--snapshot-team", default=None, help="fallback team for snapshot views (BLUE/RED)")
    return parser.parse_args()


def _pick_override(value: Any, fallback: Any) -> Any:
    return fallback if value is None else value


def _print_help():
    print("commands:")
    print("  team_view [TEAM]                - show team view for TEAM (fallback from --snapshot-team)")
    print("  submarines                      - list submarines")
    print("  mines [TEAM]                    - list mines (optionally for TEAM)")
    print("  routes [TEAM]                   - show routes")
    print("  gauges [TEAM]                   - show gauges")
    print("  events                          - show events list")
    print("  load_possible PATH              - load a possible-actions JSON file")
    print("  nav_action_kinds                - show action kinds in loaded possible-actions")
    print("  nav_move_directions             - show move directions in loaded possible-actions")
    print("  nav_move_direction DIRECTION    - show specific move direction entry")
    print("  nav_dump PATH                   - dump loaded possible-actions payload to PATH")
    print("  dump_team_view PATH [TEAM]      - write team_view JSON to PATH")
    print("  dump_possible PATH              - write loaded possible-actions to PATH")
    print("  show_map [TEAM]                 - print map tiles and size")
    print("  show_trajectory [TEAM]          - print map with own trajectory (@) and current position (O)")
    print("  belief [TEAM]                   - show radio operator belief / heatmap for TEAM")
    print("  engineer_slots [TEAM]           - show engineer buttons and which are crossed/available")
    print("  validate_captain JSON|PATH      - validate a chosen captain selection against loaded possible-actions or recomputed ones")
    print("  write_play_context [TEAM]       - write play context markdown to src/agents/common/play_context.md")
    print("  help / ?                        - show this help")
    print("  exit / quit                     - leave inspector")


def main() -> None:
    args = parse_args()

    mem = None
    nav = None
    snapshot_team = _pick_override(args.snapshot_team, "BLUE")

    if args.state_file:
        try:
            mem = load_snapshot_file(Path(args.state_file), fallback_team=snapshot_team)
            print(f"loaded snapshot: {args.state_file} (fallback team={snapshot_team})")
        except Exception as exc:
            print("failed to load snapshot:", exc)
            mem = None

    if args.possible_file:
        try:
            nav = load_possible_actions_file(Path(args.possible_file))
            print(f"loaded possible-actions: {args.possible_file}")
        except Exception as exc:
            print("failed to load possible-actions:", exc)
            nav = None

    if not args.inspect:
        # non-interactive: print summary and exit
        if mem is not None:
            print(json.dumps(mem.team_view(snapshot_team), indent=2, ensure_ascii=False))
        if nav is not None:
            print(json.dumps(nav.action_kinds(), indent=2, ensure_ascii=False))
        return

    # Interactive REPL
    print("Entering inspector REPL. Type 'help' for commands.")
    _print_help()
    while True:
        try:
            raw = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        cmd = parts[0].lower()
        if cmd in ("q", "quit", "exit"):
            break
        if cmd in ("help", "?"):
            _print_help()
            continue

        if cmd == "team_view":
            team = parts[1] if len(parts) > 1 else snapshot_team
            if mem is None:
                print("no snapshot loaded (use --state-file or load from REPL)")
                continue
            try:
                # prefer raw snapshot if it is already a team_view for this team
                snapshot = mem.snapshot if isinstance(mem.snapshot, dict) else None
                if snapshot and snapshot.get("type") == "team_view" and snapshot.get("team") == team:
                    print(json.dumps(snapshot, indent=2, ensure_ascii=False))
                else:
                    tv = mem.team_view(team)
                    print(json.dumps(tv, indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error getting team_view:", exc)
            continue

        if cmd == "submarines":
            if mem is None:
                print("no snapshot loaded")
                continue
            try:
                # Only return own_submarine (prefer raw snapshot)
                own_raw = None
                if isinstance(mem.snapshot, dict):
                    own_raw = mem.snapshot.get("own_submarine")

                if own_raw:
                    print(json.dumps({"own_submarine": own_raw}, indent=2, ensure_ascii=False))
                    continue

                subs = mem.submarines()
                own = subs.get(snapshot_team)
                if own is not None:
                    print(json.dumps({"own_submarine": {"x": own.x, "y": own.y, "damage": own.damage}}, indent=2, ensure_ascii=False))
                else:
                    print(json.dumps({"own_submarine": None}, indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error getting submarines:", exc)
            continue

        if cmd == "mines":
            team = parts[1] if len(parts) > 1 else None
            if mem is None:
                print("no snapshot loaded")
                continue
            try:
                # only return own_mines (prefer raw snapshot)
                snapshot = mem.snapshot if isinstance(mem.snapshot, dict) else None
                if snapshot and team in (None, snapshot_team):
                    own_mines = snapshot.get("own_mines")
                    if isinstance(own_mines, list):
                        print(json.dumps({"own_mines": own_mines}, indent=2, ensure_ascii=False))
                        continue
                mines = mem.mines(snapshot_team)
                out = [{"x": m.x, "y": m.y, "owner": m.owner} for m in mines]
                print(json.dumps({"own_mines": out}, indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error getting mines:", exc)
            continue

        if cmd == "show_map":
            team = parts[1] if len(parts) > 1 else snapshot_team
            if mem is None:
                print("no snapshot loaded")
                continue
            try:
                snapshot = mem.snapshot if isinstance(mem.snapshot, dict) else None
                if snapshot and snapshot.get("type") == "team_view" and snapshot.get("team") == team:
                    mv = snapshot.get("map")
                else:
                    mv = mem.team_view(team).get("map")
                if not isinstance(mv, dict):
                    print("no map available in snapshot")
                    continue
                print(f"map: {mv.get('width')}x{mv.get('height')}")
                tiles = mv.get('tiles')
                if not isinstance(tiles, list):
                    tiles = []
                for row in tiles:
                    print(''.join(str(c) for c in row))
            except Exception as exc:
                print("error showing map:", exc)
            continue

        if cmd == "show_trajectory":
            team = parts[1] if len(parts) > 1 else snapshot_team
            if mem is None:
                print("no snapshot loaded")
                continue
            try:
                snapshot = mem.snapshot if isinstance(mem.snapshot, dict) else None
                if snapshot and snapshot.get("type") == "team_view" and snapshot.get("team") == team:
                    mv = snapshot.get("map")
                    traj = snapshot.get("own_trajectory")
                    sub = snapshot.get("own_submarine")
                else:
                    tv = mem.team_view(team)
                    mv = tv.get("map")
                    traj = tv.get("own_trajectory")
                    sub = tv.get("own_submarine")

                if not isinstance(mv, dict):
                    print("no map available in snapshot")
                    continue

                tiles = mv.get("tiles")
                if not isinstance(tiles, list):
                    print("map tiles missing")
                    continue

                width = mv.get("width")
                height = mv.get("height")
                print(f"map: {width}x{height}")

                # Build a mutable grid from tiles
                grid = [list(row) for row in tiles if isinstance(row, list)]

                def valid_point(p):
                    return isinstance(p, dict) and isinstance(p.get("x"), int) and isinstance(p.get("y"), int)

                # Mark trajectory with '@' (guard dict before .get())
                if isinstance(traj, list):
                    for p in traj:
                        if not isinstance(p, dict):
                            continue
                        x_raw = p.get("x")
                        y_raw = p.get("y")
                        if not (isinstance(x_raw, int) and isinstance(y_raw, int)):
                            continue
                        x = int(x_raw)
                        y = int(y_raw)
                        if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
                            grid[y][x] = "@"

                # Mark current position with 'O' (overrides trajectory marker)
                if isinstance(sub, dict):
                    x_raw = sub.get("x")
                    y_raw = sub.get("y")
                    if isinstance(x_raw, int) and isinstance(y_raw, int):
                        x = int(x_raw)
                        y = int(y_raw)
                        if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
                            grid[y][x] = "O"

                for row in grid:
                    print(''.join(str(c) for c in row))
            except Exception as exc:
                print("error showing trajectory map:", exc)
            continue

        if cmd == "belief" or cmd == "belief_map":
            team = parts[1] if len(parts) > 1 else snapshot_team
            if mem is None:
                print("no snapshot loaded")
                continue
            try:
                snapshot = mem.snapshot if isinstance(mem.snapshot, dict) else None
                if snapshot and snapshot.get("type") == "team_view" and snapshot.get("team") == team:
                    ro = snapshot.get('radio_operator')
                else:
                    ro = mem.team_view(team).get('radio_operator')
                if not isinstance(ro, dict):
                    print("no radio operator data in snapshot")
                    continue
                belief = ro.get('belief') or ro.get('sector_probability_masses') or ro.get('possible_current_positions')
                # Format belief output: print numbers with 2 decimal places to make it visually distinct
                def fmt_num(v):
                    try:
                        if isinstance(v, (int, float)):
                            return f"{float(v):.2f}"
                    except Exception:
                        pass
                    return str(v)

                if isinstance(belief, list) and belief and all(isinstance(row, list) for row in belief):
                    # 2D grid: print each row as space-separated two-decimal numbers
                    for row in belief:
                        print(' '.join(fmt_num(v) for v in row))
                elif isinstance(belief, list):
                    # 1D list: print compact with two decimals
                    print('[{}]'.format(', '.join(fmt_num(v) for v in belief)))
                elif isinstance(belief, dict):
                    # map-like belief: format values to two decimals where numeric
                    out = {k: (fmt_num(v) if not isinstance(v, (dict, list)) else v) for k, v in belief.items()}
                    print(json.dumps(out, indent=2, ensure_ascii=False))
                else:
                    print(json.dumps(belief, indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error getting belief:", exc)
            continue

        if cmd == "engineer_slots":
            team = parts[1] if len(parts) > 1 else snapshot_team
            if mem is None:
                print("no snapshot loaded")
                continue
            try:
                snapshot = mem.snapshot if isinstance(mem.snapshot, dict) else None
                if snapshot and snapshot.get("type") == "team_view" and snapshot.get("team") == team:
                    board = snapshot.get('engineer_board')
                else:
                    board = mem.team_view(team).get('engineer_board')
                if not isinstance(board, dict):
                    print("no engineer board in snapshot")
                    continue
                buttons = board.get('buttons_by_direction', {})
                # provide detailed per-button output including whether each button is crossed
                detailed = {}
                for direction, entries in buttons.items():
                    items = []
                    if isinstance(entries, list):
                        for e in entries:
                            if isinstance(e, dict):
                                items.append({
                                    "button_id": e.get("button_id"),
                                    "label": e.get("label"),
                                    "crossed": bool(e.get("crossed")),
                                    "raw": {k: v for k, v in e.items() if k not in ("label", "button_id", "crossed")},
                                })
                            else:
                                items.append({"button_id": None, "crossed": False, "raw": e})
                    detailed[direction] = items
                print(json.dumps(detailed, indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error getting engineer slots:", exc)
            continue

        if cmd == "routes":
            team = parts[1] if len(parts) > 1 else None
            if mem is None:
                print("no snapshot loaded")
                continue
            try:
                # only return own_routes (prefer raw snapshot)
                target_team = team if team else snapshot_team
                own_raw = None
                if isinstance(mem.snapshot, dict) and target_team == snapshot_team:
                    own_raw = mem.snapshot.get("own_routes")

                if own_raw is not None:
                    print(json.dumps({"own_routes": own_raw}, indent=2, ensure_ascii=False))
                    continue

                routes = mem.routes(target_team)
                own_routes = list(routes.get(target_team, []))
                print(json.dumps({"own_routes": own_routes}, indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error getting routes:", exc)
            continue

        if cmd == "gauges":
            team = parts[1] if len(parts) > 1 else None
            if mem is None:
                print("no snapshot loaded")
                continue
            try:
                # only return own_gauges (prefer raw snapshot)
                snapshot = mem.snapshot if isinstance(mem.snapshot, dict) else None
                if snapshot and team in (None, snapshot_team):
                    own_gauges = snapshot.get("own_gauges")
                    if isinstance(own_gauges, dict):
                        print(json.dumps({"own_gauges": own_gauges}, indent=2, ensure_ascii=False))
                        continue
                gauges = mem.gauges(snapshot_team)
                print(json.dumps({"own_gauges": gauges}, indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error getting gauges:", exc)
            continue

        if cmd == "events":
            if mem is None:
                print("no snapshot loaded")
                continue
            try:
                snapshot = mem.snapshot if isinstance(mem.snapshot, dict) else None
                if snapshot and isinstance(snapshot.get("events"), list):
                    print(json.dumps(snapshot.get("events"), indent=2, ensure_ascii=False))
                else:
                    events = mem.events()
                    print(json.dumps(events, indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error getting events:", exc)
            continue

        if cmd == "load_possible":
            if len(parts) < 2:
                print("usage: load_possible PATH")
                continue
            path = parts[1]
            try:
                nav = load_possible_actions_file(Path(path))
                print(f"loaded possible-actions from {path}")
            except Exception as exc:
                nav = None
                print("error loading possible-actions file:", exc)
            continue

        if cmd == "nav_action_kinds":
            if nav is None:
                print("no possible-actions loaded")
                continue
            try:
                print(json.dumps(nav.action_kinds(), indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error reading action kinds:", exc)
            continue

        if cmd == "nav_move_directions":
            if nav is None:
                print("no possible-actions loaded")
                continue
            try:
                print(json.dumps(nav.move_directions(), indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error reading move directions:", exc)
            continue

        if cmd == "nav_move_direction":
            if len(parts) < 2:
                print("usage: nav_move_direction DIRECTION")
                continue
            if nav is None:
                print("no possible-actions loaded")
                continue
            direction = parts[1]
            try:
                entry = nav.move_direction(direction)
                print(json.dumps(entry or {}, indent=2, ensure_ascii=False))
            except Exception as exc:
                print("error reading move direction entry:", exc)
            continue

        if cmd == "nav_dump":
            if len(parts) < 2:
                print("usage: nav_dump PATH")
                continue
            if nav is None:
                print("no possible-actions loaded")
                continue
            path = parts[1]
            try:
                Path(path).write_text(json.dumps(nav.possible_actions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"wrote navigator payload to {path}")
            except Exception as exc:
                print("error dumping navigator payload:", exc)
            continue

        if cmd == "dump_team_view":
            if len(parts) < 2:
                print("usage: dump_team_view PATH [TEAM]")
                continue
            if mem is None:
                print("no snapshot loaded")
                continue
            path = parts[1]
            team = parts[2] if len(parts) > 2 else snapshot_team
            try:
                tv = mem.team_view(team)
                Path(path).write_text(json.dumps(tv, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"wrote team_view to {path}")
            except Exception as exc:
                print("error dumping team_view:", exc)
            continue

        if cmd == "dump_possible":
            if len(parts) < 2:
                print("usage: dump_possible PATH")
                continue
            if nav is None:
                print("no possible-actions loaded (use load_possible or start inspector with --possible-file)")
                continue
            path = parts[1]
            try:
                Path(path).write_text(json.dumps(nav.possible_actions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"wrote possible actions to {path}")
            except Exception as exc:
                print("error dumping possible actions:", exc)
            continue

        if cmd == "validate_captain":
            if len(parts) < 2:
                print("usage: validate_captain JSON_OR_PATH")
                continue
            # load JSON from inline string or file
            raw_arg = " ".join(parts[1:])
            payload = None
            try:
                if raw_arg.strip().startswith("{"):
                    payload = json.loads(raw_arg)
                else:
                    payload = json.loads(Path(raw_arg).read_text(encoding="utf-8"))
            except Exception as exc:
                print("failed to parse payload:", exc)
                continue

            # Expected keys: direction, load_system, engineer_button_id, activation (optional)
            direction = payload.get("direction")
            load_system = payload.get("load_system")
            engineer_button_id = payload.get("engineer_button_id")
            activation = payload.get("activation")

            # Require a loaded possible-actions navigator; do not recompute from snapshot
            validator_nav = nav
            if validator_nav is None:
                print("no possible-actions loaded; load a possible-actions file with load_possible or start with --possible-file")
                continue

            # Validate against navigator
            ok = True
            reason = []
            move = validator_nav.action("MOVE")
            if not isinstance(move, dict):
                ok = False
                reason.append("no MOVE action available")
            else:
                dirs = move.get("directions", [])
                dir_entry = None
                for d in dirs:
                    if isinstance(d, dict) and str(d.get("direction", "")).upper() == str(direction).upper():
                        dir_entry = d
                        break
                if dir_entry is None:
                    ok = False
                    reason.append(f"direction {direction} not available")
                else:
                    # find load_system branch
                    branches = dir_entry.get("load_systems", [])
                    branch = None
                    for b in branches:
                        if isinstance(b, dict) and str(b.get("load_system", "")).lower() == str(load_system).lower():
                            branch = b
                            break
                    if branch is None:
                        ok = False
                        reason.append(f"load_system {load_system} not available for direction {direction}")
                    else:
                        picks = branch.get("engineer_picks", [])
                        pick = None
                        for p in picks:
                            if isinstance(p, dict) and p.get("button_id") == engineer_button_id:
                                pick = p
                                break
                        if pick is None:
                            ok = False
                            reason.append(f"engineer button {engineer_button_id} not valid for load_system {load_system}")
                        else:
                            # activation validation
                            poss = pick.get("possible_activations") or []
                            if activation is None:
                                # if no activation requested, OK as long as pick exists
                                pass
                            else:
                                # activation could be string or dict
                                act_type = activation.get("type") if isinstance(activation, dict) else activation
                                act_payload = activation.get("payload") if isinstance(activation, dict) else None
                                found = False
                                matched_activation = None
                                for a in poss:
                                    if isinstance(a, dict):
                                        if isinstance(act_type, str) and str(a.get("type")) == str(act_type):
                                            found = True
                                            matched_activation = a
                                            break
                                    else:
                                        if str(a) == str(act_type):
                                            found = True
                                            matched_activation = a
                                            break
                                if not found:
                                    ok = False
                                    reason.append(f"activation {activation} not allowed by possible_activations")
                                else:
                                    # validate payload structure for common activations
                                    def valid_point(p):
                                        return isinstance(p, dict) and isinstance(p.get("x"), int) and isinstance(p.get("y"), int)

                                    t = str(act_type).lower() if act_type is not None else None
                                    if t == "torpedo":
                                        if not isinstance(act_payload, dict) or not isinstance(act_payload.get("targets"), list) or not any(valid_point(p) for p in act_payload.get("targets", [])):
                                            ok = False
                                            reason.append("torpedo activation requires payload.targets with at least one {x:int,y:int}")
                                    elif t == "mine":
                                        if not isinstance(act_payload, dict) or not isinstance(act_payload.get("targets"), list) or not any(valid_point(p) for p in act_payload.get("targets", [])):
                                            ok = False
                                            reason.append("mine activation requires payload.targets with at least one {x:int,y:int}")
                                    elif t == "silence":
                                        if not isinstance(act_payload, dict) or not isinstance(act_payload.get("coordinates"), list) or not any(valid_point(p) for p in act_payload.get("coordinates", [])):
                                            ok = False
                                            reason.append("silence activation requires payload.coordinates with at least one {x:int,y:int}")
                                    elif t == "drone":
                                        if not isinstance(act_payload, dict) or not isinstance(act_payload.get("sectors"), list) or not any(isinstance(s, int) for s in act_payload.get("sectors", [])):
                                            ok = False
                                            reason.append("drone activation requires payload.sectors list of ints")
                                    elif t == "trigger_mine":
                                        if not isinstance(act_payload, dict) or not valid_point(act_payload.get("target")):
                                            ok = False
                                            reason.append("trigger_mine activation requires payload.target with {x:int,y:int}")

            print("VALID" if ok else "INVALID")
            if reason:
                print("reasons:")
                for r in reason:
                    print(" -", r)
            continue

        if cmd == "write_play_context":
            team = parts[1] if len(parts) > 1 else snapshot_team
            if mem is None:
                print("no snapshot loaded")
                continue
            try:
                snapshot = mem.snapshot if isinstance(mem.snapshot, dict) else None
                if snapshot and snapshot.get("type") == "team_view" and snapshot.get("team") == team:
                    tv = snapshot
                else:
                    tv = mem.team_view(team)

                mv = tv.get("map") if isinstance(tv, dict) else None
                traj = tv.get("own_trajectory") if isinstance(tv, dict) else None
                sub = tv.get("own_submarine") if isinstance(tv, dict) else None
                gauges = tv.get("own_gauges") if isinstance(tv, dict) else None
                board = tv.get("engineer_board") if isinstance(tv, dict) else None
                ro = tv.get("radio_operator") if isinstance(tv, dict) else None

                map_lines = []
                if isinstance(mv, dict):
                    tiles = mv.get("tiles")
                    if not isinstance(tiles, list):
                        tiles = []
                    grid = [list(row) for row in tiles if isinstance(row, list)]
                    if isinstance(traj, list):
                        for p in traj:
                            if not isinstance(p, dict):
                                continue
                            x_raw = p.get("x")
                            y_raw = p.get("y")
                            if not (isinstance(x_raw, int) and isinstance(y_raw, int)):
                                continue
                            x = int(x_raw)
                            y = int(y_raw)
                            if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
                                grid[y][x] = "@"
                    if isinstance(sub, dict):
                        x_raw = sub.get("x")
                        y_raw = sub.get("y")
                        if isinstance(x_raw, int) and isinstance(y_raw, int):
                            x = int(x_raw)
                            y = int(y_raw)
                            if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
                                grid[y][x] = "O"
                    map_lines.append(f"map: {mv.get('width')}x{mv.get('height')}")
                    for row in grid:
                        map_lines.append("".join(str(c) for c in row))
                else:
                    map_lines.append("map: (missing)")

                belief_lines = []
                belief = ro.get("belief") if isinstance(ro, dict) else None
                if belief is None and isinstance(ro, dict):
                    belief = ro.get("sector_probability_masses") or ro.get("possible_current_positions")

                def fmt_num(v):
                    try:
                        if isinstance(v, (int, float)):
                            return f"{float(v):.2f}"
                    except Exception:
                        pass
                    return str(v)

                if isinstance(belief, list) and belief and all(isinstance(row, list) for row in belief):
                    for row in belief:
                        belief_lines.append(" ".join(fmt_num(v) for v in row))
                elif isinstance(belief, list):
                    belief_lines.append("[{}]".format(", ".join(fmt_num(v) for v in belief)))
                elif isinstance(belief, dict):
                    belief_lines.append(json.dumps(belief, indent=2, ensure_ascii=False))
                elif belief is not None:
                    belief_lines.append(json.dumps(belief, indent=2, ensure_ascii=False))
                else:
                    belief_lines.append("(missing)")

                crossed = {}
                if isinstance(board, dict):
                    buttons = board.get("buttons_by_direction")
                    if not isinstance(buttons, dict):
                        buttons = {}
                    for direction, entries in buttons.items():
                        crossed_list = []
                        if isinstance(entries, list):
                            for e in entries:
                                if not isinstance(e, dict):
                                    continue
                                if e.get("crossed"):
                                    label = e.get("label")
                                    button_id = e.get("button_id")
                                    crossed_list.append(label or button_id or "(unknown)")
                        crossed[direction] = crossed_list

                directions = []
                if nav is not None:
                    try:
                        directions = nav.move_directions() or []
                    except Exception:
                        directions = []

                out_lines = []
                out_lines.append("# Play Context")
                out_lines.append("")
                out_lines.append("## Trajectory Map")
                out_lines.append("```")
                out_lines.extend(map_lines)
                out_lines.append("```")
                out_lines.append("")
                out_lines.append("## Belief Map")
                out_lines.append("```")
                out_lines.extend(belief_lines)
                out_lines.append("```")
                out_lines.append("")
                out_lines.append("## System Gauges")
                out_lines.append("```json")
                if isinstance(gauges, dict):
                    out_lines.append(json.dumps(gauges, indent=2, ensure_ascii=False))
                else:
                    out_lines.append("{}")
                out_lines.append("```")
                out_lines.append("")
                out_lines.append("## Engineer Board (Crossed)")
                if crossed:
                    for direction, items in crossed.items():
                        item_text = ", ".join(items) if items else "(none)"
                        out_lines.append(f"- {direction}: {item_text}")
                else:
                    out_lines.append("- (missing)")
                out_lines.append("")
                out_lines.append("## Possible Directions")
                if directions:
                    for d in directions:
                        out_lines.append(f"- {d}")
                else:
                    out_lines.append("- (missing)")

                # My localization: explicit current position, recent trajectory, routes, and mines
                out_lines.append("")
                out_lines.append("## My Localization")
                if isinstance(sub, dict):
                    sx = sub.get("x")
                    sy = sub.get("y")
                    sd = sub.get("damage")
                    out_lines.append(f"- current_position: x={sx} y={sy} damage={sd}")
                else:
                    out_lines.append("- current_position: (missing)")

                # trajectory summary
                if isinstance(traj, list) and traj:
                    traj_points = []
                    for p in traj:
                        if isinstance(p, dict):
                            traj_points.append(f"({p.get('x')},{p.get('y')})")
                    out_lines.append(f"- trajectory: {', '.join(traj_points) if traj_points else '(none)'}")
                else:
                    out_lines.append("- trajectory: (none)")

                # routes
                routes_raw = tv.get("own_routes") if isinstance(tv, dict) else None
                if isinstance(routes_raw, list) and routes_raw:
                    out_lines.append("- routes:")
                    for r in routes_raw:
                        out_lines.append(f"  - {json.dumps(r, ensure_ascii=False)}")
                else:
                    out_lines.append("- routes: (none)")

                # own mines
                own_mines = tv.get("own_mines") if isinstance(tv, dict) else None
                if isinstance(own_mines, list) and own_mines:
                    mine_list = []
                    for m in own_mines:
                        if isinstance(m, dict):
                            mine_list.append(f"({m.get('x')},{m.get('y')})")
                    out_lines.append(f"- own_mines: {', '.join(mine_list) if mine_list else '(none)'}")
                else:
                    out_lines.append("- own_mines: (none)")

                out_path = Path("src/agents/common/play_context.md")
                out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
                print(f"wrote play context to {out_path}")
            except Exception as exc:
                print("error writing play context:", exc)
            continue

        print("unknown command")


if __name__ == "__main__":
    main()

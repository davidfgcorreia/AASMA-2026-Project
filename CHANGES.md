# Bug Fixes

## Bug 1 — SURFACE was only valid in the system phase

**Files:** `game_loop.py`, `human_controller.py`

Per the Captain Sonar rules, surfacing replaces movement — it is the captain's alternative to announcing a direction, not a system action taken after moving.

- Moved `ActionType.SURFACE` from `_is_valid_system_phase_queue` to `_is_valid_move_phase_queue`.
- Removed `SURFACE` from the `_has_system_action` guard in `HumanController` so it can be queued as a move-phase action.
- Removed `C surface` from the system-phase control hints; added it to the move-phase hints.

---

## Bug 2 — System phase was not skipped after surfacing

**File:** `game_loop.py`

After a team surfaces in the move phase their turn ends entirely — they do not get a system action. Previously the loop would advance to the system phase regardless.

- After applying move-phase actions, the loop checks `_team_just_surfaced` (looks for a `surface` event in `state.events`).
- If the team surfaced, the loop immediately switches to the opponent instead of entering the system phase.

---

## Bug 3 — Surfaced team blocked the game loop waiting for input

**File:** `game_loop.py`

When `skip_turns[team] > 0` the team's actions are silently rejected inside `apply_actions`, but the game loop still displayed that team's UI and waited for the player to confirm — stalling the game.

- Added an early-exit branch at the top of the loop: if the active team has `skip_turns > 0`, `apply_actions([])` is called (which ticks the counter down) and the turn is handed to the opponent automatically, with no UI prompt shown to the surfaced team.

---

## Bug 4 — Silence steps were hardcoded to 4

**Files:** `human_controller.py`, `renderer.py`

The rules allow the captain to move *up to* 4 spaces silently. The previous implementation always sent `steps=MAX_SILENCE_STEPS`, so a player who only wanted to move 1 space silently would always move 4.

- Added `silence_steps: int` field to `HumanController` (default `MAX_SILENCE_STEPS`).
- Added key bindings: **Q** decreases steps (min 1), **E** increases steps (max 4) — active only while **F** (silence) mode is selected.
- `reset_turn` resets `silence_steps` back to 4 each turn.
- `ui_state` exposes `silence_steps` so the renderer can show the current value in the move-phase hints.

---

## Bug 5 — Blocked silence path forced a surface instead of stopping

**File:** `game_state.py` — `_resolve_silence`

The rules state the captain may move *up to* N spaces; stopping early because a cell is blocked is valid and expected. Previously a blocked cell mid-path immediately triggered `_resolve_surface(forced=True)`, which is the rule for normal movement (you *must* move — if you can't, you surface), but silence works differently.

- Changed the loop in `_resolve_silence` to `break` when a cell is blocked rather than calling `_resolve_surface`. The submarine stops at its last valid position and the silence action completes normally.

---

## Bug 6 — ~~Mines could not be dropped on own route cells~~ (REVERTED — was incorrect)

**File:** `game_state.py` — `_resolve_mine`

The original fix incorrectly removed the route check. Per the rules, *"The Captain cannot drop a mine in a space on his route (with a line drawn in it)."* The route check has been reinstated as a hard block.

---

## Bug 7 — AI ignored the two-phase turn structure

**Files:** `game_loop.py`, `ai_placeholders.py`

The game loop enforces move-phase then system-phase for human players, but called `choose_actions` once and applied everything in a single batch for the AI — the AI never properly completed both phases.

- `choose_actions` now accepts a `phase` argument (`"move"` or `"system"`).
- Split into `_choose_move` (returns MOVE or SURFACE) and `_choose_system` (returns a weapon action or nothing).
- The game loop passes `active_phase` to `choose_actions` and handles the AI's phase transitions with the same `_team_just_surfaced` check used for humans.
- The AI's surfaced-state early exit mirrors the human path.

---

## Bug 8 — Surfacing skip counter was depleted by enemy phases, giving only ~1.5 turns

**Files:** `game_state.py`, `game_loop.py`

`apply_actions()` decremented `skip_turns` for every call — including the enemy's move phase and system phase — consuming all three skip-turns across roughly 1.5 enemy turns instead of 3. Additionally, after the last decrement the enemy received one extra full turn before the surfaced team regained control.

- Removed the blanket decrement block from `apply_actions()`.
- Each auto-advance path in the game loop now decrements `skip_turns[team]` explicitly, after `apply_actions([])` returns.
- The auto-advance only switches `active_team` to the enemy when `skip_turns > 0` after decrement; when it hits 0 the surfaced team immediately regains their turn, giving the enemy exactly 3 full turns.

---

## Bug 9 — Blocked move forced a surface even when valid directions remained

**File:** `game_state.py` — `_resolve_move`

`_resolve_move` called `_resolve_surface(forced=True)` whenever the requested direction was blocked, even if other directions were still open. A forced surface (blackout) should only occur when **all four** orthogonal directions are blocked.

- Added `_is_blackout(actor)` helper that checks all four neighbours.
- `_resolve_move` now surfaces only when `_is_blackout` returns `True`; otherwise it emits an `action_rejected` event and returns, letting the player choose another direction.

---

## Bug 10 — Mine could be dropped on own route cells

**File:** `game_state.py` — `_resolve_mine`

The mine-placement check did not verify whether the target cell was part of the submarine's own route. Per the rules: *"The Captain cannot drop a mine in a space on his route (with a line drawn in it)."*

- Added `(tx, ty) in self.routes.get(actor)` guard before deploying the mine; emits `action_failed` if violated.

---

## Bug 11 — Circuit self-repair permanently disabled after first repair

**File:** `game_state.py` — `_repair_circuits`, `BreakdownState`

`BreakdownState` carried a `circuits_status` dict that marked a circuit as permanently repaired after its first self-repair. Subsequent crossings of the same four symbols would never trigger the repair again within the same surface period, even though the rules allow it every time all four symbols are crossed.

- Removed `circuits_status` from `BreakdownState`.
- Removed the early-exit guard and the flag assignment from `_repair_circuits`; the check now runs on every call using only the live `crossed_by_direction` data.

---

## Bug 12 — Silence consumed its gauge even when the path was fully blocked

**File:** `game_state.py` — `_resolve_silence`

If the very first step of a silence move was blocked (island, own route, or own mine), `moved` stayed at 0 but the silence gauge was still consumed and a breakdown was still applied — wasting the system with no movement.

- Added a `moved == 0` check immediately after the movement loop; if no steps were taken the action emits `action_failed` and returns before touching the gauge, breakdown, or `last_action_system`.

---

## Bug 13 — TRIGGER_MINE incorrectly subject to gauge/breakdown/system-ordering restrictions

**File:** `game_state.py` — `SYSTEM_ACTION`, `_resolve_trigger_mine`

`TRIGGER_MINE` was listed in `SYSTEM_ACTION`, causing it to be blocked by the "cannot activate two systems in a row" rule and by engineer breakdowns on the mine system. Per the rules, a mine can be triggered *"at any time, except while surfaced"* and *"whether or not any spaces on the mine gauge are marked"* — it is independent of the gauge-based system activation cycle.

- Removed `TRIGGER_MINE` from `SYSTEM_ACTION`; the existing `action.type != ActionType.TRIGGER_MINE` gauge-ready bypass in `_validate_state` now naturally extends to the breakdown and ordering checks.
- Changed `_resolve_trigger_mine` to set `last_action_system = False` so that triggering a mine does not block a subsequent system activation.

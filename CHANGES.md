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

## Bug 6 — Mines could not be dropped on own route cells

**File:** `game_state.py` — `_resolve_mine`

The mine-placement check called `_route_blocked`, which returns `True` for any cell in the submarine's route set. The rules only prohibit dropping mines on islands or cells already occupied by a mine; the player should be able to mine a cell they previously visited.

- Replaced `_route_blocked` with an explicit check: `in_bounds` and `is_blocked` (island test) only.
- The existing "no mine already there" check is kept.

---

## Bug 7 — AI ignored the two-phase turn structure

**Files:** `game_loop.py`, `ai_placeholders.py`

The game loop enforces move-phase then system-phase for human players, but called `choose_actions` once and applied everything in a single batch for the AI — the AI never properly completed both phases.

- `choose_actions` now accepts a `phase` argument (`"move"` or `"system"`).
- Split into `_choose_move` (returns MOVE or SURFACE) and `_choose_system` (returns a weapon action or nothing).
- The game loop passes `active_phase` to `choose_actions` and handles the AI's phase transitions with the same `_team_just_surfaced` check used for humans.
- The AI's surfaced-state early exit mirrors the human path.

# Tasks — Environment, Human Controller, and Game Core

This file lists the immediate implementation tasks for Phase‑1 focusing on the environment (simulation core & map), the human controller (UI), and the core game mechanics. Each task includes a short description, priority, and an estimated effort.

## Priority: High

1. Implement `GameState` and action schema
- Description: Authoritative simulation state with methods to apply validated actions, snapshot state, and produce deterministic updates. Define JSON action schema used by humans and agents.
- Priority: High
- Est. effort: 2–3 days

2. Map loader and renderer (15×15 tiles)
- Description: Load map presets, tile metadata (terrain, obstacles), and render top-down grid in Pygame. Provide coordinate mapping and tile highlight support.
- Priority: High
- Est. effort: 2 days

3. Turn-based simulation loop
- Description: Implement deterministic turn loop: snapshot → collect actions → validate → resolve → log → render. Ensure tick rate and seed handling.
- Priority: High
- Est. effort: 2 days

4. Action validation & resolution system
- Description: Validate actions (schema, resource availability, bounds), apply resolution order (Captain→Engineer→First Mate→Radio→Environment), and compute outcomes (movement, collisions, torpedoes, repairs).
- Priority: High
- Est. effort: 2 days

5. JSON event logging & replay player
- Description: Record per-turn events, prompts/responses (LLM), sampled hypotheses, and final actions. Provide a simple replay tool to load and step through logs.
- Priority: High
- Est. effort: 1–2 days

## Priority: Medium

6. Human UI — role panels & multi-action selector
- Description: Implement Pygame UI: side role panels with large action buttons, multi-action queue, tile-target selection, Confirm button, and tooltips showing estimated outcomes (from Belief stub).
- Priority: Medium
- Est. effort: 3 days

7. Human input binding & shortcuts
- Description: Keyboard shortcuts, confirm hotkeys, undo before confirm, and accessibility options (scalable UI, colorblind palette).
- Priority: Medium
- Est. effort: 1 day

8. Unit tests for environment core
- Description: Tests for movement, collision, ping/noise models, deterministic replay, and action validation.
- Priority: Medium
- Est. effort: 2 days

## Priority: Low (placeholders / integration)

9. Integrate BeliefTracker stub
- Description: Add a simple BeliefGrid stub (uniform or trivial update) to allow UI tooltips and initial MCTS integration later.
- Priority: Low
- Est. effort: 1 day

10. Basic AI placeholders (rule-based)
- Description: Provide simple deterministic rule-based agents for Captain/First Mate/Engineer/Radio to enable playtesting of the human UI and simulation loop.
- Priority: Low
- Est. effort: 1–2 days

## Notes
- All randomness must be seedable via a single game seed specified at game start.
- Keep the renderer decoupled from simulation updates for stable performance.
- Add detailed logging hooks early to capture actions, validation results, and any fallback behavior for missed deadlines.

If you want, I can scaffold the repository now with the skeleton modules and a minimal Pygame demo implementing tasks 1–4. Proceed? 

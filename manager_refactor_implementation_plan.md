# Agent Manager Refactor And Implementation Plan

## Objective
Refactor the team agent manager so it can:
- Run in 3-agent mode or full-team mode per team.
- Orchestrate and capture multi-agent iterations each turn.
- Execute in-game API calls from validated agent decisions.
- Select initial strategy and role-specific starting prompts before gameplay.

This plan is implementation-first and aligned with the current code in `src/agents/manager/manager.py`.

## Current Baseline (Already Implemented)
- Role registration and active-role selection (`register_agent`, `set_active_roles`, `activate_all_registered`).
- Turn activation window (`activate_agents`, `is_activation_active`, `close_activation`).
- Team observation and role-scoped views (`observe`, `_build_role_view`).
- Inter-agent messaging with per-turn and per-pair bounds (`send_message`, `broadcast`, `read_inbox`).
- Action proposal + vote collection and majority acceptance (`propose_turn_action`, `choose_turn_actions`).
- Turn actions ledger writing (`_write_turn_actions_ledger` -> `common/turn_actions.md`).

## Target Design

### 1) Team Operating Modes
Support two team operation modes:
- `FULL_TEAM`: captain, first mate, engineer, radio operator.
- `THREE_AGENT`: exactly 3 AI active roles (first mate, engineer, radio operator), with captain filled by a human player.

Design decision:
- Keep one manager per team (`BLUE` and `RED`).
- Add explicit mode and role roster policy to manager config.
- Keep role-level behavior unchanged; only orchestration and gating change.

### 2) Iteration Orchestration
Add a deterministic turn loop inside manager:
- Iteration 0: observe + initial proposals.
- Iteration N: message exchange, refinement, and re-proposal (bounded by max iterations and deadline).
- Finalization: consensus selection + omitted/rejected reason capture.

Artifacts to capture per turn:
- Iteration snapshots (role input, proposal, messages sent/received, validation result).
- Final decision pack (accepted actions, omitted actions, confidence/justification fields).

### 3) API Execution Pipeline
Manager becomes the execution orchestrator between role output and game APIs:
- Convert role proposal to action intent schema.
- Validate action against legal actions / game state.
- Execute via game API adapter in phase order.
- Persist execution results and feedback into shared memory/ledger.

Important constraint:
- The manager should never execute raw free-form text from agents; only structured intents.

### 4) Initial Strategy And Prompt Bootstrap
At match start (or round reset), manager should:
- Pick an initial team strategy profile (aggressive, balanced, stealth, etc.).
- Select role-specific starting prompts based on strategy + mode.
- Load and inject role context + shared context + strategy directives.
- Persist selected strategy and prompt set in manager state and memory.

## Refactor Steps

## Implementation Status
- [x] Phase 1 started.
- [x] Mode-aware activation scaffold implemented in manager.
- [x] Initial mode tests added and passing.
- [ ] Phase 2 pending.

## Phase 0 - Contracts And Data Models
1. Add mode enums and dataclasses:
   - `TeamOperatingMode` enum.
   - `RoleRosterPolicy` (human vs AI role assignments).
   - `TurnIterationRecord`, `DecisionRecord`, `ExecutionRecord`.
2. Extend `AgentManagerConfig` with:
   - `operating_mode`, `human_role` (captain in 3-agent mode).
   - `api_execution_enabled`, `strategy_profile` (optional override).
3. Define strict action intent schema:
   - `type`, `payload`, `role`, `turn_id`, optional `reasoning`, optional `confidence`.

Definition of done:
- Manager can validate mode config at startup.
- Invalid combinations fail fast with clear `ValueError`.

## Phase 1 - Mode-Aware Activation
1. Add a helper to derive effective active roles from mode and roster policy.
2. Update `activate_agents` and `observe` to enforce effective roster.
3. Add a manager status export field for current mode and human role.

Definition of done:
- Full-team mode activates all registered roles.
- Three-agent mode activates exactly 3 configured roles.
- Existing tests still pass.

## Phase 2 - Iteration Capture And Orchestration
1. Add `run_turn_cycle(state, deadline_ms)` entrypoint in manager.
2. Inside cycle:
   - call `observe`.
   - collect first proposals.
   - run bounded discussion iterations (send/read inbox + re-propose).
   - call `choose_turn_actions`.
3. Persist records:
   - in-memory list for current turn.
   - optional markdown/json log writer for post-game analysis.

Definition of done:
- Every turn has at least one `TurnIterationRecord`.
- Rejected/omitted proposals include reason code (`no_majority`, `invalid_intent`, `timeout`).

## Phase 3 - Game API Execution Adapter
1. Create `ManagerGameApiAdapter` (new file under `src/agents/manager/`).
2. Adapter responsibilities:
   - map accepted intents to game API actions.
   - call game API in valid phase order.
   - return structured execution outcome (success/failure + event info).
3. Manager integration:
   - `execute_turn_actions(state, intents)` method.
   - feed results back to shared memory and role inbox (next turn context).

Definition of done:
- Manager can execute accepted intents end-to-end without direct UI input.
- Execution failures are surfaced with actionable error messages.

## Phase 4 - Strategy And Starting Prompt Selection
1. Add strategy selector module:
   - Inputs: team, map features, mode, optional user override.
   - Output: strategy profile id + role directives.
2. Add prompt bootstrap loader:
   - base role prompt + common context + strategy overlay.
   - mode-aware prompt adaptation (if role is missing in 3-agent mode).
3. Store active strategy and prompts in manager runtime state.

Definition of done:
- Manager selects and exposes chosen strategy before first turn.
- Each active role receives a concrete starting prompt payload.

## Phase 5 - Integration Tests And Validation
1. Extend tests with mode coverage:
   - 3-agent roster enforcement.
   - full-team behavior unchanged.
2. Add iteration capture tests:
   - at least one iteration record per turn.
   - message limits respected across iterations.
3. Add API execution tests:
   - accepted intent -> api call sequence.
   - invalid intent is rejected before execution.
4. Add strategy bootstrap tests:
   - profile selection deterministic with fixed seed/config.
   - role prompt selection changes by mode.

Definition of done:
- New tests pass together with existing manager tests.
- No regression on activation, messaging limits, and vote resolution.

## Proposed File-Level Changes
- Update `src/agents/manager/manager.py`:
  - add mode config, iteration cycle, execution integration, strategy bootstrap hooks.
- Add `src/agents/manager/api_adapter.py`:
  - game API bridge and result normalization.
- Add `src/agents/manager/strategy.py`:
  - strategy profile selection and role directives.
- Add `src/agents/manager/models.py` (optional):
  - shared dataclasses/enums for manager runtime records.
- Update tests:
  - `tests/test_agent_manager.py`
  - `tests/test_agent_manager_activation.py`
  - add `tests/test_agent_manager_execution.py`
  - add `tests/test_agent_manager_strategy.py`

## Execution Order (Recommended)
1. Phase 0 + Phase 1 (safe structural changes).
2. Phase 2 (iteration loop + records).
3. Phase 3 (API adapter and execution wiring).
4. Phase 4 (strategy and prompts bootstrap).
5. Phase 5 (tests and regression pass).

## Risks And Mitigations
- Risk: role outputs are inconsistent in structure.
  - Mitigation: strict intent schema and normalization layer before voting/execution.
- Risk: 3-agent mode causes role responsibility gaps.
  - Mitigation: mode-specific strategy overlays and fallback directives.
- Risk: API call ordering errors.
  - Mitigation: centralized adapter with phase-aware validation and tests.

## Acceptance Checklist
- [ ] Manager supports `FULL_TEAM` and `THREE_AGENT` modes.
- [ ] Manager captures per-turn multi-agent iterations.
- [ ] Manager executes validated in-game API calls from decisions.
- [ ] Manager selects initial strategy and role starting prompts.
- [ ] Automated tests cover modes, iterations, execution, and strategy bootstrap.

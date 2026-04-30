# PRD — Phase 1: Environment & Game (Multiagent Captain Sonar)

Version: 0.3 — Consolidated
Date: 2026-04-27

## Executive Summary

Phase‑1 delivers a turn‑based, multiagent Captain Sonar prototype: deterministic simulation core, a Pygame UI for human players, role-based agent interfaces, belief-tracking + MCTS for hidden movement, and an optional Gemini LLM advisor used only for guidance. The PRD contains rules, architecture, multi-agent design, belief strategy, LLM integration, testing specs, and a development roadmap.

## Product Description

The product is a research and prototyping platform that implements a Captain Sonar–style submarine game focused on multi-agent coordination under partial observability. It provides:
- A playable, turn-based Pygame application (human hotseat + AI agents).
- A deterministic simulation core for reproducible experiments (seeded RNG, JSON event logs).
- Agent interfaces and baseline AI modules (rule-based, MCTS-based) with a Belief Tracker for hidden movement.
- An optional Gemini LLM adapter for high-level advice and explanations (advisory only).
- Developer artifacts: source code, unit/integration tests, research notes (`docs/research/`), and prompt templates (`docs/prompts/`).

Target users: researchers and students studying multi-agent coordination, game AI developers, and course projects requiring a reproducible hidden-movement testbed.

Assumptions: local execution on Python 3.11+, Pygame 2.x; LLM access optional and can be stubbed for offline testing.

## Table of Contents

1. Terminology
2. Goals & Acceptance Criteria
3. Concrete MVP Parameters
4. Technical Stack
5. High-level Architecture
6. Game Rules & Turn Flow
7. Agent Interfaces & Roles
8. Multi-Agent Design & Belief Strategy
9. Gemini LLM Integration (Advisor)
10. Implementation Strategy (Data Flow & APIs)
11. UI / UX (Human Player)
12. Logging, Testing & Reproducibility
13. Metrics & Evaluation
14. Risks & Mitigations
15. Development Roadmap
16. Appendix — Research & References

## 1. Terminology

- Tick / Turn: discrete simulation step (default 10 ticks/sec). In turn-based mode agents submit actions per turn.
- GameState: authoritative state object maintained by the simulation.
- State snapshot: immutable, read-only copy of GameState for use by agents/LLM.
- Belief heatmap: probability distribution over enemy locations (tile grid).

## 2. Goals & Acceptance Criteria

- Playable local MVP: full turn‑based match between two subs (AI or human-hotseat).
- Determinism: same seed + scripted inputs → identical JSON event log.
- AI: at least one AI per role; First Mate/Radio use belief+MCTS for hidden-movement decisions.
- UI: Pygame map, role panels, action log; human action selection parity with agent action schema.
- Acceptance thresholds: determinism 100%; Action Agreement Rate ≥ 0.6; Top-5 belief accuracy ≥ 0.8 in ping-rich scenarios.

## 3. Concrete MVP Parameters

- Map presets: 15×15 tiles, tile size 32 px (2 presets shipped).
- Torpedoes per sub: 4
- Hull: 100 HP
- Systems: {engine, sonar, weapons, control} (integer damage levels)
- Default tick rate: 10 ticks/sec

## 4. Technical Stack

- Language: Python 3.11+
- Rendering / GUI: Pygame 2.x
- Concurrency: asyncio for agent messaging and background tasks
- Search & Belief: custom MCTS + BeliefGrid
- LLM Adapter: Gemini-compatible adapter (stubbed in Phase 1)
- Packaging: virtualenv / pip; `requirements.txt`

## 5. High-level Architecture

- Simulation Core (`GameState`): authoritative, single-threaded turn resolution and logger.
- Renderer / UI: Pygame process reading `GameState` snapshots each frame; non-blocking.
- Agent Layer: agents implement `observe(state_snapshot)` and `act(deadline_ms)`.
- Belief Tracker: Bayesian update module producing tile heatmaps and top-K cache.
- MCTS Runner: conditioned on sampled hypotheses from the Belief Tracker.
- LLM Adapter: optional advisory module; responses logged and used as soft evidence.
- Logger / Replay: JSON event log and replay tools.

## 6. Game Rules & Turn Flow

### Setup
- Two submarines on a single map; each has four role slots (Captain, First Mate, Engineer, Radio). Roles may be human or AI.
- Starting positions chosen by map preset; initial resources per concrete parameters.

### Turn Structure
1. Simulation writes immutable `state_snapshot`, increments `turn_id`.
2. Roles receive snapshot and call `act(deadline_ms)` to submit role-specific actions.
3. Validation: actions checked for schema, resource availability, and map bounds.
4. Optional advisory: LLMAdapter invoked and its advisory stored in log.
5. Belief Tracker updates using transition, observations, and optional LLM soft evidence.
6. Resolution order: Captain (movement) → Engineer (repairs/constraints) → First Mate (weapons/active) → Radio (reports) → Environment (collision, torpedo travel, pings).
7. Apply damage/resources, log events, render next frame.

### Actions (MVP)
- Move: heading + speed (Captain)
- Ping/Sonar: probabilistic sensing (Radio / First Mate)
- Fire Torpedo: target tile/heading (First Mate)
- Ram: contact damage (Captain/First Mate)
- Repair: Engineer selects a system to reduce damage
- Charge: First Mate allocates charge/time to reload or boost
- Special: scenario-specific actions (optional)

### Constraints & Resolution
- Movements constrained by engine damage and obstacles. Sonar returns noisy evidence; torpedoes travel in straight lines; Engineer repairs reduce damage by units per turn.
- Missed deadlines apply fallback policies (no-op or safe default).

### Victory
- Sub sunk when hull ≤ 0. Match ends on sink or on turn limit; tiebreak by hull.

## 7. Agent Interfaces & Roles

All agents implement:
- `observe(state_snapshot)`: receive role-specific view.
- `act(deadline_ms) -> List[Action]`: return actions before deadline.

Roles
- Captain: movement/navigation.
- First Mate: weapons and tactical decisions; main MCTS user.
- Engineer: repairs and power management.
- Radio: contact reporting and ping operation; belief assistance.

Agent implementations: rule-based, MCTS-based, LLM-advised (advisory only).

## 8. Multi-Agent Design & Belief Strategy

This section contains an implementable belief strategy inspired by Nijssen & Winands (2011), Mirsky et al. (2022), and Ribeiro et al. (2023).

### Core components
- Belief Tracker (`BeliefGrid`): 15×15 histogram with per-tile metadata and top-K cache.
- Particle Sampler: draws hypotheses (tile + short trajectory) for MCTS.
- MCTS Runner: conditioned rollouts over sampled hypotheses.
- ATPO Teammate Inference: template bank + online Bayesian updates.
- LLM Adapter: optional soft evidence provider.

### Models & Algorithms (summary)
- Motion model: uniform over reachable tiles given max speed and obstacles.
- Observation model: discretized Gaussian for ping, directional likelihoods for passive noise, delta-like for contact.
- Bayesian update: belief_t ∝ likelihood(observation | tile) · transition_prior(tile).
- Location Categorization: prune unreachable tiles using reachability convolution and cluster feasible tiles; discard tiny isolated tiles.
- Sampling: Stage A draw from top-K (K=50), Stage B expand into short trajectories; default N_particles=100, adapt by entropy.
- MCTS: UCT selection (c=1.4), progressive widening, rollout heuristics; evaluation combines damage, risk, and information gain.
- ATPO: update posterior over small template bank to adapt coordination and condition simulations.

### Defaults & tuning
- ping_range=5, sigma_ping=1.5, N_particles=100, MCTS rollouts per hypothesis=20, UCT c=1.4, LLM λ=0.3.

## 9. Gemini LLM Integration (Advisor)

Design constraints:
- LLM is advisory only; final action selection deterministic.
- All LLM prompts/responses logged for reproducibility.

Usage:
- Input: compact JSON `{role, turn_id, recent_events, belief_topk, systems_status, task}`.
- Output: JSON `{actions: [...], rationale: "", confidence: 0-1}`.
- Integration: LLM scores converted to per-tile soft-likelihoods and applied with weight λ; invalid outputs validated and ignored.

## 10. Implementation Strategy (Data Flow & APIs)

Per-turn guaranteed sequence: `GameState` snapshot → optional LLMAdapter → Belief Tracker → Particle Sampler → ATPO update → MCTS Runner → Agent validation → GameState apply.

APIs
- `GameState.snapshot(turn_id)` → frozen JSON-able structure.
- `LLMAdapter.query(prompt_struct, timeout_ms)` → advisory JSON or timeout.
- `BeliefGrid` methods: `apply_transition(max_speed)`, `apply_observation(obs)`, `apply_llm(soft)`, `prune_by_reachability()`, `top_k(k)`.
- `Agent.act(deadline_ms)` → actions.

Validation & safety: schema-validate LLM and agent outputs; clamp coordinates; fallback if invalid or timeout.

Traceability: per-turn log entries include `seed`, `turn_id`, `state_snapshot_hash`, `LLM_prompt`, `LLM_response`, `belief_snapshot`, `actions_applied`.

## 11. UI / UX (Human Player)

Design principles: minimal, role-focused, accessible. Human UI maps directly to agent action schema.

Layout & interactions:
- Center: top-down map with fog-of-war.
- Side panels: role boards with action buttons and system status.
- Bottom: action log, turn controls (Confirm, Auto-resolve), seed display.
- Multi-action selector: click actions, select target tiles, confirm to submit.

Accessibility: colorblind palette, scalable UI elements, keyboard shortcuts.

## 12. Logging, Testing & Reproducibility

Logging: JSON event log stores turn-ordered events, LLM prompts/responses, sampled hypotheses, and MCTS traces.

Testing specifications (key suites):
- Action Agreement Rate (AAR): measure First Mate recommendations vs Captain executed action category; alert if AAR<0.6.
- Belief State Coherence (BSC): Top-K accuracy (k=5), MSE on belief at true tile, entropy stability.
- Shared State Consistency Test (SSCT): ensure all agents read same authoritative `GameState`; detect desync via snapshot hash comparisons.
- Stress Scenarios: inject delays, conflicting updates, increased noise; verify fallback policies and no crashes.
- Team-vs-Team evaluation: tournaments across agent configs; compute payoffs, regret, and analyze strategy robustness under resource asymmetry.

Automated harness & CI:
- `pytest` for unit/integration tests.
- `tools/run_scenario.py` to run scripted scenarios, inject faults, and produce JSON reports.
- Nightly reduced tournaments for regression monitoring.

Acceptance thresholds:
- Determinism: identical event logs for same seed (100%).
- AAR: ≥ 0.6 average.
- BSC Top-5 accuracy: ≥ 0.8 in ping-rich scenarios.

## 13. Metrics & Evaluation

- Functional: win rate, detection latency, Action Agreement Rate, belief accuracy.
- Performance: average render FPS (target ≥45), simulation tick consistency (10 tps ±5%).
- Robustness: determinism pass rate in CI.

## 14. Risks & Mitigations

- LLM hallucination: schema validation, coordinate clamping, fallback policies.
- Concurrency/desync: enforce turn-based MVP and snapshot reads; test SSCT.
- Computational cost: adaptive sampling, progressive widening, caching of simulated trajectories.

## 15. Development Roadmap

Phase 1 (MVP, 4–6 weeks):
- Scaffold repo and Pygame prototype (map renderer + turn loop).
- Implement `GameState`, action schema, validator, and logger.
- Implement `BeliefGrid`, observation models, and Location Categorization pruning.
- Implement `sampler.py` and simple `mcts.py` runner; integrate ATPO templates.
- Add LLMAdapter stub and logging hooks; unit tests and CI harness.

Phase 2 (post-MVP):
- Real-time mode, distributed agents, richer UI overlays, ablation studies, and human subject tests.

## 16. Appendix — Research & References

- Nijssen, J.P.A.M. & Winands, M.H.M. (2011). Monte-Carlo Tree Search for the Game of Scotland Yard.
- Mirsky, R., Carlucho, I., Stone, P., Albrecht, S.V., et al. (2022). A Survey of Ad Hoc Teamwork Research.
- Ribeiro, J.G., Martinho, C., Sardinha, A., Melo, F.S. (2023). Making Friends in the Dark: Ad Hoc Teamwork Under Partial Observability.

Developer notes:
- Create `docs/research/` with PDFs and pseudocode; `docs/prompts/` for prompt templates.

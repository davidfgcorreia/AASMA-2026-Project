# TODO

## Global Reviews

- [ ] Confirm the APIs and their execution of the game environment.
- [X] Possible action generator returns a useful, consistent format.

## Manager Agent

- [ ] Manager: connection with game APIs (endpoints, call patterns, error handling).
- [ ] Manager: agent configurations (per-agent settings, roles, timeouts, priorities).
- [ ] Manager: agent activation loops (scheduling, heartbeat, activation conditions).
- [ ] Manager: Validate activation/calling, config handling for agents, and info flow from agent action selection to the game.
- [ ] Manager: memory usage (persistent + shared) and strategy orchestration.

## Radio Operator Agent

- [ ] Radio Operator: context role definition, prompt set alignment, and prompt creation pipeline.
- [ ] Radio Operator: Review belief state interpretation and sonar reasoning; assess silence usage to reduce detection and increase opponent uncertainty.
- [ ] Radio Operator: memory usage (persistent + shared) and strategy notes.

## Engineer Agent

- [ ] Engineer: context role definition, prompt set alignment, and prompt creation pipeline.
- [ ] Engineer: Review board reasoning for selecting parts based on direction, systems, and strategy.
- [ ] Engineer: memory usage (persistent + shared) and strategy notes.

## First Mate Agent

- [ ] First Mate: context role definition, prompt set alignment, and prompt creation pipeline.
- [ ] First Mate: Review charging logic and response to attacks; ensure info is passed to other agents; in 3-agent mode, recommend actions to the human captain.
- [ ] First Mate: memory usage (persistent + shared) and strategy notes.

## Captain Agent

- [ ] Captain: context role definition, prompt set alignment, and prompt creation pipeline.
- [ ] Captain: Review path planning vs map constraints and system activation logic.
- [ ] Captain: memory usage (persistent + shared) and strategy notes.

## Shared Memory

- [ ] Shared memory for discussion, information sharing, and move strategy.

## Additional Reviews

- [ ] Strategy adaptation review.
- [ ] Prompt refining.
- [ ] Game evaluators (design evaluators to score/compare game play and agent strategies).

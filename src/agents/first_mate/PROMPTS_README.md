# First Mate Prompt Pipeline

This folder contains the small prompt pipeline used by the First Mate.

## Files

- `prompts/1_strategy_lock.md` - phase 1, read the role context and commit to the strategy
- `prompts/2_system_selection.md` - phase 2, choose the next system to load
- `strategy.md` - compact strategy guide used by the model-backed agent
- `prompt.md` - fallback single-prompt version for runtime bootstrap

## Workflow

1. Read the context and strategy.
2. Compare the candidate systems available to the team.
3. Return one selected system, then map it to a charge/activate proposal.
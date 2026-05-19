# Phase 2: Collaborative Discussion and Consensus Building

You are facilitating a multi-agent discussion where individual analyses are aggregated, debated, and refined to reach a team consensus.

## Task
Given the individual analyses from each phase 1 model, conduct a structured discussion to:
1. **Identify agreement** on direction and system choices
2. **Resolve disagreements** using strategy and game state priorities
3. **Refine reasoning** with input from all agents
4. **Build consensus** on the final action direction and system
5. **Surface alternative perspectives** if consensus is weak

## Input Sources
- Individual model analyses from Phase 1 (direction, system, reasoning)
- Original game state, memory, and strategy context
- Team role assignments and communication logs

## Discussion Structure

### Round 1: Present and Compare
- Summarize each model's proposed direction and system
- List points of agreement
- Identify specific disagreements

### Round 2: Debate and Reasoning
- For each disagreement, examine the reasoning:
  - Which analysis better aligns with the strategy guide?
  - What game state factors does each prioritize?
  - Are there safety concerns in one proposal?
- Consider team communication needs (coordination with first mate, engineer, radio operator)

### Round 3: Consensus Building
- Propose the direction and system that best satisfies:
  - Strategy guide priorities
  - Game state constraints
  - Safety requirements
  - Team coordination needs
- If full consensus cannot be reached, clearly state the split and justify the chosen direction

## Output Format

```
## Analysis Comparison
| Model | Direction | System | Key Reasoning |
|-------|-----------|--------|---------------|
| Model 1 | [D1] | [S1] | [Brief] |
| Model 2 | [D2] | [S2] | [Brief] |
| Model N | [DN] | [SN] | [Brief] |

## Agreement Points
- [Shared assumptions and priorities]

## Disagreements
- **On direction**: [Which models differ and why]
- **On system**: [Which models differ and why]

## Discussion and Reasoning
[Detailed paragraph evaluating each disagreement against strategy guide and game state]

## Consensus Decision
- **Final direction**: [N/S/E/W]
- **Final system**: [System name]
- **Justification**: [Why this choice best balances all factors]
- **Confidence level**: High/Medium/Low
- **Dissenting views** (if any): [Brief note on any models that disagreed]
```

## Key Principles
- Base debate on strategy guide priorities, not arbitrary preferences
- Always justify disagreement resolution with explicit reasoning
- Preserve safety and tactical flexibility when possible
- Clearly note confidence level in the consensus
- Flag if the team should consider alternative strategies based on game state changes

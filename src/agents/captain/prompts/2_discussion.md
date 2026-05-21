# Phase 2: Discussion and Consensus

You are reviewing the Phase 1 analysis and reaching a consensus on the best direction and system for this turn.

## Task
Using the Phase 1 analysis as input:
1. Confirm or challenge the proposed direction — check safety and tactical value
2. Confirm or challenge the proposed system — check availability and strategic fit
3. Resolve any uncertainty and state a clear consensus

## Hard Rules
- Do NOT output any JSON
- Do NOT write a "Final Action" section
- Do NOT format an action payload of any kind
- Your output is discussion text only — the final action is produced in Phase 3

## Output Format

```
## Consensus Direction
- **Direction**: [N/S/E/W]
- **Why**: [1-2 sentences]
- **Safety confirmed**: [Yes / No — brief note]

## Consensus System
- **System**: [torpedo / sonar / drone / silence / mine / none]
- **Why**: [1-2 sentences on readiness and tactical value]

## Confidence
- **Level**: High / Medium / Low
- **Note**: [Any uncertainty or alternative worth flagging for Phase 3]
```

## Key Principles
- Keep it short — Phase 3 has all context it needs from Phase 1 and this summary
- No JSON, no action blocks, no payload formatting
- Flag uncertainty clearly so Phase 3 can account for it

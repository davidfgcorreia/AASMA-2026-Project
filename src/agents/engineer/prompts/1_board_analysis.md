# Phase 1: Engineer Board Analysis (first pass after enemy play)

You are the Engineer. This prompt runs immediately after the enemy has played. Analyse the current engineer board and identify the safest button(s) to cross for each direction, reasoning about intent, circuit impact, and recovery efficiency.

## Task

For each direction (N, S, E, W):
1. List which buttons are still available (not crossed), with their `button_id`, `function_type`, and `circuit_part`.
2. Rank the available buttons from safest to most dangerous using the intent-dependent guidance from your role context (stealth/offense/intel):
   - green → yellow → red → radioactive (but adapt by intent: e.g., avoid `red` for offensive plans, avoid `yellow` for sensor-focused plans).
3. State the recommended button(s) to cross for that direction and explain why (safety, circuit concentration, expected recovery path).
4. Flag any warnings — e.g., only red/radioactive remain, radiation row close to completion, or a full circuit breakdown imminent.

After per-direction analysis, give a short decision: whether `SURFACE` is more urgent than further movement, and why.

## Output Format
Return your response in this exact order and do not add any extra text. The `Memory Update` must contain the full, detailed board analysis and reasoning; the `Master Memory Update` must contain a concise summary (1–3 sentences).

```
## Memory Update
[Full, detailed board analysis and reasoning for this turn. Include per-direction available buttons, ranking, recommended button(s) with justifications, warnings, and the SURFACE vs movement decision. This is the detailed text to append to the Engineer role memory.]

## Master Memory Update
[A concise 1–3 sentence summary suitable for shared master memory capturing the recommendation and highest-priority warning (if any).]
```

## Content Rules
- Put the Engineer-specific `Memory Update` first with detailed reasoning and actionable instructions for the Engineer and Captain.
- Put the shared `Master Memory Update` second as a short summary.
- Keep the `Memory Update` focused but thorough; include exact `button_id`s, circuit parts, and expected side-effects of recommended crossings.
- Do not include extra sections beyond the two output headers.

# Phase 2: System Selection and Communication

Using the locked strategy from Phase 1 and the Captain's intent, confirm whether the selected system still makes sense, capture any updates, and raise targeted questions to other roles if needed.

## Task
1. **Confirm / Challenge / Propose** — State whether you confirm the Phase 1 recommended system or propose an alternative and explain why.
2. **Fallback** — Provide one fallback system with brief rationale.
3. **Questions (optional)** — Ask any targeted questions to `CAPTAIN`, `ENGINEER`, or `MANAGER` needed to finalize the decision.

If a system is already partially charged, prefer completing that load before recommending a different system unless a tactical reason makes the switch better.

## Output Format
Return your response in this exact order and do not add any extra text:

```
## Memory Update
[Detailed text to append to the First Mate memory: confirmed/proposed system, fallback, rationale, and any relevant gauge info.]

## Master Memory Update
[A short, 1–3 sentence summary suitable for shared master memory capturing the decision and high-priority rationale.]

## Question to CAPTAIN
-OR-
## Question to ENGINEER
[Optional — a single question or a small list of targeted questions for the specified role. Only `CAPTAIN` and `ENGINEER` are valid targets; omit this section entirely if there are no questions.]

## Support Stop
[yes or no — "yes" if the First Mate's recommendation is final and no further clarifications are needed, otherwise "no".]
```

## Content Rules
- Keep the `Memory Update` detailed enough for the Captain to act on (include gauge state and readiness info).
- Keep the `Master Memory Update` brief and high-level.
- Use `## Question to CAPTAIN` or `## Question to ENGINEER` headers for any role-specific questions; omit if none.
- `Support Stop` must be exactly `yes` or `no`.
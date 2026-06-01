# Phase 1: Strategy Lock

Review the First Mate context and the Captain's stated intent before selecting a system to charge. Your role is to propose system loads that support the Captain's plan.

Task:
- Confirm the current charge state and gauge availability.
- Use the Captain's stated intent to prioritize which systems should be charged next.
- If a system is already partially charged, prioritize completing that load before starting a different system unless the Captain's current intent clearly favors a switch.
- Produce one recommended system to charge and one fallback, with brief rationale.

Output format:
Return your response in this exact order and do not add any extra text:

```
## Memory Update
[Detailed text to append to the First Mate memory: current gauge state, recommended system to charge, fallback option, and short rationale.]

## Master Memory Update
[A short, 1–3 sentence summary of the recommended system and why it supports the Captain's intent.]
```

Content rules:
- Put the First Mate-specific `Memory Update` first.
- Put the shared `Master Memory Update` second.
- Keep both sections concise and actionable.
- Do not include the final system activation — only the charging recommendation.
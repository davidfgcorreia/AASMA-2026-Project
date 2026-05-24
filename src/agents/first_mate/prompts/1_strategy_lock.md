# Phase 1: Strategy Lock

Review the First Mate context and strategy before selecting a system.

Task:
- Confirm the current charge state.
- Keep the strategic priorities in view.
- Identify whether torpedo, sonar, silence, mine, or drone should be favored next.

Output format:
Return your response in this exact order and do not add any extra text:

```
## Memory Update
[Write the text that should be appended to the First Mate memory file for this turn.]

## Master Memory Update
[Write the text that should be appended to the shared master memory for this turn.]
```

Content rules:
- Put the First Mate-specific memory update first.
- Put the shared master memory update second.
- Keep both sections short and directly actionable.
- Do not include system selection text or any other sections.
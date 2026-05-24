# Phase 1: Engineer Board Analysis

You are the Engineer. Analyse the current board state and identify the safest button to cross for each direction.

## Task

For each direction (N, S, E, W):
1. List which buttons are still available (not crossed), with their button_id and function_type.
2. Rank the available buttons from safest to most dangerous using the priority order:
   green → yellow → red → radioactive
3. State the recommended button (safest uncrossed).
4. Flag any warnings — e.g. only red/radioactive remain, or a full circuit breakdown is close.

Then decide whether REPAIR is more urgent than further movement.

## Output Format
Return your response in this exact order and do not add any extra text:

```
## Memory Update
[Write the text that should be appended to the Engineer memory file for this turn.]

## Master Memory Update
[Write the text that should be appended to the shared master memory for this turn.]
```

## Content Rules
- Put the Engineer-specific memory update first.
- Put the shared master memory update second.
- Keep both sections short and directly actionable.
- Do not include board analysis, repair assessment, or any other sections.

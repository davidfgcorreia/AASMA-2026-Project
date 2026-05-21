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

```
## Direction N
- Available: [button_id (type), ...]
- Recommended: [button_id] — reason
- Warning: [any danger note, or "none"]

## Direction S
...

## Direction E
...

## Direction W
...

## Repair Assessment
- Recommended: yes / no
- Reason: [brief]
```

Keep it short. One line per point.

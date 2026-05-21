# Phase 2: Button Selection

Using your Phase 1 board analysis, output your per-direction button recommendations as JSON.

## Rules

- Pick the safest uncrossed button for each direction.
- Only include buttons that are not already crossed.
- If no safe button exists for a direction, omit that direction from recommendations.
- Set repair_recommended to true only if REPAIR is more urgent than movement.

## Required JSON shape

```json
{
  "recommendations": {
    "N": "N-not-green-0",
    "S": "S-down-green-4",
    "E": "E-not-green-1",
    "W": "W-not-green-0"
  },
  "repair_recommended": false
}
```

Return valid JSON only. No commentary outside the JSON block.

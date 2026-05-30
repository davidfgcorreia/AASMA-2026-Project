# Phase 2: Radio Operator Decision

You are the Radio Operator finalizing your Phase 1 analysis into a structured JSON decision.

## Input
Your Phase 1 prose analysis is included in the context. The lie detection result is also already provided in `--- LIE DETECTION (pre-computed) ---` — do not recalculate it, just read it from there.

## Task
Produce a JSON decision object with sensor recommendation and enemy position estimate.

## Output Format
Return ONLY a valid JSON object. No markdown fences, no extra text.

```json
{
  "sonar_recommendation": {
    "use_sonar": false,
    "target_sector": null,
    "reasoning": "brief reason"
  },
  "recommended_sensor": "none",
  "best_sector": null,
  "most_likely_sector": null,
  "most_likely_position": null
}
```

## Field Definitions
- `sonar_recommendation.use_sonar`: true if using sonar this turn would give significant information.
- `sonar_recommendation.target_sector`: sector number to query (null if not applicable).
- `recommended_sensor`: one of `"sonar"`, `"drone"`, or `"none"`.
- `best_sector`: integer sector with the highest probability mass right now (null if unknown).
- `most_likely_sector`: integer sector for the current best enemy position estimate.
- `most_likely_position`: object `{"x": int, "y": int}` or null if unknown.

## Rules
- All sector numbers are integers 1–6.
- Return ONLY the JSON object.

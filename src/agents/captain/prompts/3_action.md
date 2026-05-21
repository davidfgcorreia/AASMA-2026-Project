# Phase 3: Final Action JSON

Output a single JSON object. No prose, no headers — just the JSON block.

## Required Fields

```json
{
  "direction": "N",
  "load_system": "torpedo",
  "engineer_button_id": "N-not-green-0"
}
```

## Rules (follow strictly)

### 1. direction
- Must be one of the legal move directions listed in `possible_actions` in the game state.
- Check `own_routes` — never pick a direction that would land on an already-visited cell.
- Use the Phase 2 consensus direction unless it is illegal, in which case pick the safest legal alternative.
- If no legal move exists, use `"SURFACE"` (omit the other two fields).

### 2. load_system
- The system to charge this turn.
- **Check inbox first**: if the First Mate sent a charge recommendation, use it.
- Must be one of: `torpedo`, `mine`, `sonar`, `drone`, `silence`, `repair`.
- Always include this field.

### 3. engineer_button_id
- **The direction prefix of the button MUST match your chosen `direction`.**
  - Moving N → button must start with `N-`
  - Moving S → button must start with `S-`
  - Moving E → button must start with `E-`
  - Moving W → button must start with `W-`
- **Check inbox first**: if the Engineer sent per-direction recommendations, use the one for your chosen direction.
  - Example inbox message: `"Engineer board recommendations: N→N-not-green-0, S→S-down-green-4, E→E-not-green-1, W→W-not-green-0"`
  - If moving S, use `S-down-green-4`.
- If no Engineer recommendation is available, pick the safest uncrossed button for your direction from `engineer_board` (green > yellow > red > radioactive).
- Always include this field.

## Examples

Moving S, First Mate recommends sonar, Engineer recommends `S-down-green-4` for South:
```json
{
  "direction": "S",
  "load_system": "sonar",
  "engineer_button_id": "S-down-green-4"
}
```

Moving N, no inbox messages:
```json
{
  "direction": "N",
  "load_system": "torpedo",
  "engineer_button_id": "N-not-green-0"
}
```

Surfacing (no legal moves):
```json
{
  "direction": "SURFACE"
}
```

Return valid JSON only. No other text outside the JSON block.

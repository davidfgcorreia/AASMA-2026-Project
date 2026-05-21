# Captain Action Format Reference

## JSON Output (Phase 3)

Output exactly these three fields:

```json
{
  "direction": "N",
  "load_system": "torpedo",
  "engineer_button_id": "N-not-green-0"
}
```

| Field | Required | Description |
|---|---|---|
| `direction` | Yes | `N`, `S`, `E`, `W`, or `SURFACE`. Must be a legal move (not in `own_routes`, not an island). |
| `load_system` | Yes (unless SURFACE) | System to charge: `torpedo`, `mine`, `sonar`, `drone`, `silence`, `repair`. |
| `engineer_button_id` | Yes (unless SURFACE) | Button to cross. **Direction prefix must match `direction`.** Format: `{direction}-{circuit_part}-{function_type}-{slot_index}`. |

## Engineer Button ID Rules

- Moving **N** → button ID must start with `N-` (e.g. `N-not-green-0`, `N-central-yellow-4`)
- Moving **S** → button ID must start with `S-` (e.g. `S-down-green-4`, `S-not-yellow-2`)
- Moving **E** → button ID must start with `E-` (e.g. `E-not-green-1`, `E-down-yellow-3`)
- Moving **W** → button ID must start with `W-` (e.g. `W-not-green-0`, `W-top-yellow-5`)

Use the Engineer's inbox recommendation for your chosen direction when available.

## Surface Action

When surfacing, direction is `"SURFACE"` and the other fields are omitted:

```json
{
  "direction": "SURFACE"
}
```

## Key Constraints

- Never pick a `direction` that revisits a cell in `own_routes`
- Never pick a `direction` that hits an island
- `engineer_button_id` direction prefix MUST match `direction`
- Always include `load_system` on non-SURFACE turns

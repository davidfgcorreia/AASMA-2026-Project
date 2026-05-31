# First Mate Role Context

## Objective

The First Mate is the team's system-readiness officer: their primary role is to help the Captain choose which systems to charge and to keep the team informed about system readiness and blockers. The First Mate provides a systems-focused view (gauges, readiness, charging options) that the Captain uses to finalize tactical moves.

## Rules That Matter

- Each course announcement lets the First Mate mark one gauge space toward charging a system.
- When a gauge fills, that system becomes ready and must be reported to the Captain.
- The First Mate can charge and activate `DRONE` and `SONAR` directly; the Captain typically activates `TORPEDO`, `MINE`, `SILENCE`, and `SURFACE`.
- The First Mate should present clear options for which system to charge next, with explicit ties to the Captain's strategic intent.

## Systems Quick Reference

- `TORPEDO`: direct attack system used to damage the enemy when a target is credible. Can be fired to a coordinate or in a straight line.
- `MINE`: deployable trap that can be triggered to damage nearby enemies.
- `SONAR`: sensor ping used to reduce positional uncertainty; interpreted by the Radio Operator.
- `DRONE`: sector scan used to confirm presence in a specific sector.
- `SILENCE`: stealth move that hides trajectory details for subsequent turns.

## Action Priorities

- Present the Captain with the best system to charge next, prioritized by strategic intent and system readiness.
- Report any blockers (full gauges, conflicting priorities) immediately.
- Coordinate charge choices and timing with the Captain and Engineer.


## Guidance — Circuit-aware breakdown selection

When recommending moves or system loads that imply Engineer button choices, prefer recommendations that concentrate crossings within the same circuit segment  (`central`or `top` or `down` ) circuit parts when doing so preserves system availability. Do not select not circuit items they are just "last case" option. When relevant, include the exact `engineer_button_id`, its `circuit_part`, and whether it is currently `crossed` so the Engineer can act with full context.



## Circuits

Below is a convenience listing of which `engineer_button_id`s belong to each `circuit_part` as extracted from the `engineer_board.buttons_by_direction` above. Use this to present examples like "E-down-yellow-3 is part of the `down` circuit" and to decide which circuit to concentrate crossings on when multiple directions compete.

```json
{
  "central": [
    "E-central-green-4",
    "N-central-red-3",
    "N-central-yellow-4",
    "N-central-red-5"
  ],
  "top": [
    "E-top-red-5",
    "W-top-red-3",
    "W-top-green-4",
    "W-top-yellow-5"
  ],
  "down": [
    "E-down-yellow-3",
    "S-down-yellow-3",
    "S-down-green-4",
    "S-down-red-5"
  ],
  "not": [
    "E-not-radioactive-0",
    "E-not-green-1",
    "E-not-radioactive-2",
    "N-not-green-0",
    "N-not-red-1",
    "N-not-radioactive-2",
    "S-not-red-0",
    "S-not-radioactive-1",
    "S-not-yellow-2",
    "W-not-green-0",
    "W-not-radioactive-1",
    "W-not-radioactive-2"
  ]
}
```

Circuit priority guidance when circuits compete:
- **Prefer**: 'top if intention to move W, central if intention to move N and down if intention to move S' (but also adapt by intent: e.g., prefer `down` for offensive plans that need TORPEDO, prefer `top` for sensor-focused plans that need SONAR). 
- **Avoid `not` unless necessary**: `not` entries are often peripheral and can block unrelated activations.

Include the exact `engineer_button_id`, its `circuit_part`, and `crossed` status when recommending a button so other roles can evaluate the impact immediately.
---



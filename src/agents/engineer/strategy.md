# Engineer Strategy Guide

This strategy guide aligns with the strategic rules and recommendations in the Engineer role context (`src/agents/engineer/context.md`). It avoids hard-coded board layouts (those are provided in the play context) and instead gives intent-driven decision rules and priorities.

## Baseline Button Safety (reference only)

Use this baseline ordering as a starting point, but adapt based on mission intent and circuit state:
1. **green** — lowest disruption to systems.
2. **yellow** — impacts sensors when exhausted.
3. **red** — impacts weapons when exhausted; higher-risk for offensive plans.
4. **radioactive** — can cause direct damage; avoid whenever possible.

## Strategy Principles

- Choose buttons based on the strategy objective (stealth, offense, or intelligence), not a universal preference.
- Concentrate crossings within the same circuit segment to enable faster clearing and recovery.
- Preserve critical systems required by the near-term plan: if a torpedo is planned, avoid crossings that risk disabling red circuits; if sonar is needed, avoid crossings that threaten yellow circuits.
- Never cross a `radioactive` button if any non-radioactive button is available, unless survival requires it.

## Decision Rules

- Prefer the safest uncrossed button relevant to the current mission intent (refer to the Captain/First Mate recommendations for intent).
- If multiple uncrossed buttons share the same safety tier, prefer the one that helps concentrate crossings on the same circuit segment.
- If the only available buttons for a required direction are red or radioactive, (or `SURFACE`) and notify the Captain immediately with the blocking `button_id`s and circuits.
- When in doubt, ask targeted questions to `CAPTAIN` or `FIRST_MATE` about intent before committing to a high-risk crossing.

## When to Recommend SURFACE

- A radioactive button has been crossed and the next available option in that direction is radioactive.
- The team has taken damage and restoring system availability outweighs movement.
- Multiple elements of a high-priority circuit are nearly exhausted and continued crossings will disable a critical system.




# Engineer Strategy Guide

## Button Safety Priority (safest to most dangerous)

1. **green** — blocks silence when all green crossed. Silence is low-priority at game start.
2. **yellow** — blocks sonar and drone when all yellow crossed. Medium priority.
3. **red** — blocks torpedo and mine when all red crossed. High priority — avoid crossing.
4. **radioactive** — causes direct damage when all radioactive crossed. Avoid at all costs.

## Button Layout Reference

| Direction | slot 0 | slot 1 | slot 2 | slot 3 | slot 4 | slot 5 |
|-----------|--------|--------|--------|--------|--------|--------|
| W | green | radioactive | radioactive | red | green | yellow |
| N | green | red | radioactive | red | yellow | red |
| S | red | radioactive | yellow | yellow | green | red |
| E | radioactive | green | radioactive | yellow | green | red |

## Decision Rules

- Always prefer the safest uncrossed button for the active direction.
- Never cross a radioactive button if any non-radioactive button remains uncrossed.
- Avoid crossing red buttons when torpedo or mine is the current charge target.
- If multiple buttons share the same safety tier, prefer the one whose function_type
  already has more crossed siblings — spreading damage across circuits is safer than
  concentrating it on one.
- If the only remaining buttons for a direction are red or radioactive, recommend REPAIR.

## When to Recommend REPAIR

- A radioactive button has been crossed and another radioactive is the only remaining
  option for an upcoming direction.
- The team has already taken damage and restoring system availability outweighs
  the cost of skipping movement.
- All buttons in a high-priority circuit (red) are nearly exhausted.

## Strategy to follow:

Turn 1: Move East. Select E-not-green-1 to minimize system impact. Keep red (Torpedo/Mine) and green (Silence) circuits clear for future tactical needs.

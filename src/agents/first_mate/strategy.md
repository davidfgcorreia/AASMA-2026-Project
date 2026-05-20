# First Mate Strategy

The first mate is the system-readiness specialist for the team.

Core rule:
- Choose the next system to charge, not the submarine movement direction.

## Mode 1: Attack

Goal:
- Keep pressure with attack-ready systems.

Load plan:
- Turn 1: load torpedo.
- Turn 2: load silence.
- After turn 2: keep loading the attack system that is not full yet (torpedo first, then mine if needed).

## Mode 2: Discovery

Goal:
- Improve enemy localization before committing heavy weapons.

Load plan:
- Turn 1: load sonar.
- Turn 2: load silence.
- After turn 2: keep sonar ready, then rotate to drone when sonar is already full.

## Mode 3: Stealth

Goal:
- Maximize concealment while keeping one backup option available.

Load plan:
- First two loads: silence, silence.
- Third load: one non-silence system (prefer sonar; if sonar is full, use torpedo or mine).

## Shared Constraints

- Never waste a load on a system that is already full if another required system is not full.
- If the current mode sequence is blocked by full gauges, advance to the next step in that mode.
- If all mode-priority systems are full, default to torpedo.
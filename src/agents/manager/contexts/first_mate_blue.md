# Turn Context for FIRST_MATE (team: BLUE)

## Context
```
# First Mate Role Context

## Objective

The First Mate manages gauges and system readiness for the team.

## Rules That Matter

- Each course announcement lets the First Mate mark one gauge space.
- When a gauge fills, the system becomes ready.
- The First Mate must inform the Captain when a system is ready.
- The First Mate can activate drone and sonar.
- The Captain activates most other systems, including torpedo, mine, silence, surface

## Systems Quick Reference

- Torpedo: direct attack system used to damage the enemy when a target is credible. can launched to a specific sector or in a straight line 4 blocks. 
- Mine: trap system deployed next to the submarine can be activated to damage nearby enemies.
- Sonar: information system used to narrow enemy position uncertainty.
- Drone: sector-check system used to check if enemy is on that sector.
- Silence: stealth movement system that hides path details and breaks enemy tracking.


## Action Priorities

- Maintain readiness on the most likely next system.
- Report blockers immediately.
- Coordinate charge choices with the Captain.
```

## Strategy
```
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
```

## Memory
```
# First Mate Agent Memory

- Primary responsibility: system charge, readiness, and weapon/sensor planning.
- Reads system utilization and turn state from the manager role view.
- Shares short planning messages with the captain and engineer through the manager.
```

## Master Memory
```
# Master Team Memory

This file stores the agreed team strategy, gameplay hypotheses, and next moves.

## Agreed Strategy

- Keep the team coordinated through the manager.
- Share short, role-specific updates instead of long speculative notes.
- Favor safe, information-preserving actions unless the current plan justifies risk.
- Use the radio operator to narrow targets before committing torpedoes.
- Use the first mate to preserve system readiness and avoid wasted charge.
- Use the engineer to choose the best board selection for the active direction.

## Game Hypotheses

- Enemy movement patterns should be updated after every turn.
- Sensor results should be treated as the strongest short-term evidence.
- Silence and surface actions should be treated as information-shaping events.
- When confidence is low, preserve options rather than forcing an attack.

## Next Moves

- Update the team view.
- Read the latest inbox for each active role.
- Reconcile the current hypothesis with new sensor evidence.
- Confirm the next tactical move and the charge plan.

## Decision Log

- Initial shared team memory created.
```

## Play Context
```
# Play Context

## Trajectory Map
```
map: 15x15
...............
..#...#.....##.
..#.....#...#..
........#......
..O............
...............
.#.#..#.#......
.#.#..#........
...#...#...###.
...............
...#...........
..#....#...#...
#...........#..
..#...#.#....#.
...#...........
```

## Belief Map
```
0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.00 0.00 0.01
0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.01 0.01
0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.00 0.01 0.00 0.01 0.01 0.00 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.00 0.01 0.00 0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.00 0.00 0.01
0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.01 0.01 0.01
0.00 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.00 0.01 0.01
0.01 0.01 0.00 0.01 0.01 0.01 0.00 0.01 0.00 0.01 0.01 0.01 0.01 0.00 0.01
0.01 0.01 0.01 0.00 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01 0.01
```

## Engineer Board (Crossed)
- W: (none)
- N: (none)
- S: (none)
- E: (none)

- team: BLUE
- turn: 12
- round_type: normal
- source: api
- enemy_last_play: {"type": "move", "direction": "W", "charged_system": "sonar"}

```json
{
  "source": "api",
  "round_type": "normal",
  "team": "BLUE",
  "turn": 12,
  "own_submarine": {
    "x": 2,
    "y": 4,
    "damage": 0
  },
  "own_gauges": {
    "torpedo": 0,
    "mine": 0,
    "drone": 0,
    "sonar": 0,
    "silence": 0,
    "scenario": 0
  },
  "engineer_board": {
    "team": "BLUE",
    "circuits_status": {},
    "crossed_by_direction": {
      "W": [],
      "N": [],
      "S": [],
      "E": []
    },
    "buttons_by_direction": {}
  },
  "radio_operator": {
    "heard_moves": [
      "W"
    ],
    "most_likely_sector": null
  },
  "enemy_last_play": {
    "type": "move",
    "direction": "W",
    "charged_system": "sonar"
  }
}
```

```

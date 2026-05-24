# Turn Context for ENGINEER (team: BLUE)

# Context
# Engineer Role Context

## Objective

The Engineer tracks breakdowns caused by movement and protects the submarine from dangerous system failures.

## Rules That Matter

- After every Captain course announcement, the Engineer crosses out one symbol for that direction.
- The symbol choice matters because some symbols disable systems.
- If all symbols for a system are crossed, that system cannot be used until repaired.
- Radiation breakdowns can deal damage when all radiation symbols are crossed.
- A complete area breakdown can also deal damage.
- Surfacing repairs breakdowns.

## Strategy Notes

- Prefer safe symbol choices that keep critical systems available.
- Avoid dangerous circuits when a safer option exists.
- Treat repair opportunities as strategic resets, not just damage recovery.

## Action Priorities

- Protect weapon and sensor availability.
- Warn the Captain about risky directions.
- Use repairs to remove harmful breakdown patterns.

# Strategy
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


# Memory
# Engineer Agent Memory

- Primary responsibility: engineer board selection and breakdown handling.
- Reads the engineer board snapshot and crossed button state from the manager.
- Communicates selection intent and repair status through bounded manager messages.

# Master Memory
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

# Play Context
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


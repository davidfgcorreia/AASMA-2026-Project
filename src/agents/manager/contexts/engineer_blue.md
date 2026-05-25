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

## Engineer Turn 2 Reasoning

Turn 12: No buttons crossed yet. For upcoming movement, prioritize green (System: Silence) or yellow (System: Sonar/Drone) to preserve red (Torpedo/Mine) and radioactive (Damage) circuits. Current board is fully functional.

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

## Captain Turn 2

The enemy is actively using SONAR to locate us. We need to prioritize SILENCE or DRONE to regain the initiative. Move E to shift position and allow the Engineer to charge critical systems.
## Engineer Turn 2

Turn 12: Submarine is at (2, 4) with zero damage. Engineer board is clean. Maintain focus on charging critical systems (Torpedo/Mine) while avoiding red and radioactive circuits during movement. Next move: Proceed with Captain's heading, prioritizing green/yellow buttons.
## First Mate Turn 2

Turn 12: Enemy moving West and using Sonar. Blue team adopting Discovery mode; prioritizing Sonar readiness to counter enemy tracking.
## Captain Turn 0

Turn 1: Team BLUE initiating movement East. Strategy: Prioritize early SONAR charge to establish enemy position. Engineer to focus on E-circuit green/yellow buttons. Radio Operator to monitor for initial enemy movement.

## Engineer Turn 0

The Captain has chosen East. Engineer has marked E-not-green-1 (Green) to minimize system impact. Team is moving to (2, 1). First Mate: maintain focus on charging Sonar/Drone.

## First Mate Turn 0

Turn 0: Starting position (1, 1). Team adopting Discovery mode to localize the enemy early. First Mate prioritizing Sonar to support Radio Operator intelligence.


# Play Context
# Play Context

## Trajectory Map
```
map: 15x15
...............
.O#...#.....##.
..#.....#...#..
........#......
...............
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
- turn: 0
- round_type: startup
- source: api
- enemy_last_play: None

```json
{
  "enemy_last_play": null,
  "engineer_board": {
    "buttons_by_direction": {
      "E": [
        {
          "button_id": "E-not-radioactive-0",
          "circuit_part": "not",
          "crossed": false,
          "direction": "E",
          "function_type": "radioactive",
          "slot_index": 0
        },
        {
          "button_id": "E-not-green-1",
          "circuit_part": "not",
          "crossed": false,
          "direction": "E",
          "function_type": "green",
          "slot_index": 1
        },
        {
          "button_id": "E-not-radioactive-2",
          "circuit_part": "not",
          "crossed": false,
          "direction": "E",
          "function_type": "radioactive",
          "slot_index": 2
        },
        {
          "button_id": "E-down-yellow-3",
          "circuit_part": "down",
          "crossed": false,
          "direction": "E",
          "function_type": "yellow",
          "slot_index": 3
        },
        {
          "button_id": "E-central-green-4",
          "circuit_part": "central",
          "crossed": false,
          "direction": "E",
          "function_type": "green",
          "slot_index": 4
        },
        {
          "button_id": "E-top-red-5",
          "circuit_part": "top",
          "crossed": false,
          "direction": "E",
          "function_type": "red",
          "slot_index": 5
        }
      ],
      "N": [
        {
          "button_id": "N-not-green-0",
          "circuit_part": "not",
          "crossed": false,
          "direction": "N",
          "function_type": "green",
          "slot_index": 0
        },
        {
          "button_id": "N-not-red-1",
          "circuit_part": "not",
          "crossed": false,
          "direction": "N",
          "function_type": "red",
          "slot_index": 1
        },
        {
          "button_id": "N-not-radioactive-2",
          "circuit_part": "not",
          "crossed": false,
          "direction": "N",
          "function_type": "radioactive",
          "slot_index": 2
        },
        {
          "button_id": "N-central-red-3",
          "circuit_part": "central",
          "crossed": false,
          "direction": "N",
          "function_type": "red",
          "slot_index": 3
        },
        {
          "button_id": "N-central-yellow-4",
          "circuit_part": "central",
          "crossed": false,
          "direction": "N",
          "function_type": "yellow",
          "slot_index": 4
        },
        {
          "button_id": "N-central-red-5",
          "circuit_part": "central",
          "crossed": false,
          "direction": "N",
          "function_type": "red",
          "slot_index": 5
        }
      ],
      "S": [
        {
          "button_id": "S-not-red-0",
          "circuit_part": "not",
          "crossed": false,
          "direction": "S",
          "function_type": "red",
          "slot_index": 0
        },
        {
          "button_id": "S-not-radioactive-1",
          "circuit_part": "not",
          "crossed": false,
          "direction": "S",
          "function_type": "radioactive",
          "slot_index": 1
        },
        {
          "button_id": "S-not-yellow-2",
          "circuit_part": "not",
          "crossed": false,
          "direction": "S",
          "function_type": "yellow",
          "slot_index": 2
        },
        {
          "button_id": "S-down-yellow-3",
          "circuit_part": "down",
          "crossed": false,
          "direction": "S",
          "function_type": "yellow",
          "slot_index": 3
        },
        {
          "button_id": "S-down-green-4",
          "circuit_part": "down",
          "crossed": false,
          "direction": "S",
          "function_type": "green",
          "slot_index": 4
        },
        {
          "button_id": "S-down-red-5",
          "circuit_part": "down",
          "crossed": false,
          "direction": "S",
          "function_type": "red",
          "slot_index": 5
        }
      ],
      "W": [
        {
          "button_id": "W-not-green-0",
          "circuit_part": "not",
          "crossed": false,
          "direction": "W",
          "function_type": "green",
          "slot_index": 0
        },
        {
          "button_id": "W-not-radioactive-1",
          "circuit_part": "not",
          "crossed": false,
          "direction": "W",
          "function_type": "radioactive",
          "slot_index": 1
        },
        {
          "button_id": "W-not-radioactive-2",
          "circuit_part": "not",
          "crossed": false,
          "direction": "W",
          "function_type": "radioactive",
          "slot_index": 2
        },
        {
          "button_id": "W-top-red-3",
          "circuit_part": "top",
          "crossed": false,
          "direction": "W",
          "function_type": "red",
          "slot_index": 3
        },
        {
          "button_id": "W-top-green-4",
          "circuit_part": "top",
          "crossed": false,
          "direction": "W",
          "function_type": "green",
          "slot_index": 4
        },
        {
          "button_id": "W-top-yellow-5",
          "circuit_part": "top",
          "crossed": false,
          "direction": "W",
          "function_type": "yellow",
          "slot_index": 5
        }
      ]
    },
    "circuits_status": {},
    "crossed_by_direction": {
      "E": [],
      "N": [],
      "S": [],
      "W": []
    },
    "team": "BLUE"
  },
  "own_gauges": {
    "drone": 0,
    "mine": 0,
    "scenario": 0,
    "silence": 0,
    "sonar": 0,
    "torpedo": 0
  },
  "own_submarine": {
    "damage": 0,
    "x": 1,
    "y": 1
  },
  "radio_operator": {
    "heard_moves": [],
    "most_likely_sector": 1
  },
  "round_type": "startup",
  "source": "api",
  "team": "BLUE",
  "turn": 0
}
```


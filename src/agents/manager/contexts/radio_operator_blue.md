# Turn Context for RADIO_OPERATOR (team: BLUE)

## Context
```
# Radio Operator Role Context

## Objective

The Radio Operator tracks the enemy submarine using announcements, sensors, and belief updates.

## Rules That Matter

- The enemy Captain’s movement announcements are the basis of route tracking.
- The enemy cannot cross islands or its own route.
- Drones narrow the enemy to a sector.
- Sonar provides one true and one false positional clue.
- Torpedo and mine misses eliminate impossible positions.
- Surface announcements reveal the current sector.

## Strategy Notes

- Update beliefs after every movement or sensor event.
- Use the strongest evidence to shrink the enemy search space.
- Give the Captain a likely cell or sector when confidence rises.
- Preserve uncertainty when the evidence is weak or contradictory.

## Action Priorities

- Track movement history.
- Fuse sensor evidence.
- Communicate the best target estimate to the Captain.
```

## Strategy
```

```

## Memory
```
# Radio Operator Agent Memory

- Primary responsibility: hidden-position reasoning and enemy tracking.
- Reads the radio operator snapshot and belief data from the manager.
- Shares likely positions, sectors, and sensor interpretation with the team.
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

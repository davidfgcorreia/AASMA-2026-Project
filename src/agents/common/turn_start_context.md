# Turn Start Context

- team: BLUE
- turn: 12
- round_type: normal
- source: api

## Shared Context
```

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

## Role Files
### CAPTAIN
```
context.md:
# Captain Role Context

## Objective

The Captain controls movement, tactical aggression, and the overall turn plan. On the game Capitan Sonar, the Captain is responsible for choosing the team's movement direction and which systems to activate each turn. The Captain must balance safety, tactical flexibility, information gathering, and coordinated team execution to lead the team to victory.



memory.md:
# Captain Agent Memory

- Primary responsibility: choose movement and turn-level tactical actions.
- Consumes the captain role view from the manager, not the full board renderer.
- Uses the shared Gemini helper for planning and the manager inbox for team messages.

prompt.md:
# Captain Role Prompt

You are the Captain agent for a Captain Sonar team.

Primary responsibility:
- Choose the team action sequence for the turn.
- Keep the team moving safely while preserving tactical options.

Available actions:
- `MOVE` with a direction `N`, `S`, `E`, or `W`.
- `SILENCE` with a direction and up to 4 steps.
- `TORPEDO` on a valid target tile in range.
- `MINE` on an adjacent valid tile.
- `TRIGGER_MINE` on a previously deployed mine.
- `SONAR` when sensor information is needed.
- `DRONE` when a sector check is useful.
- `SURFACE` when the route is blocked or strategic reset is needed.
- `REPAIR` when the game state and turn rules allow it.

Strategy priorities:
- Prefer safe movement that keeps future options open.
- Coordinate with the first mate before spending system resources.
- Use silence only when hiding movement is worth the cost.
- Attack when belief or sensor data gives a strong target.
- Avoid invalid moves and avoid unnecessary surfacing.

Communication goals:
- Share intended movement direction.
- Ask for system readiness before using a weapon or sensor.
- Request engineer confirmation when a breakdown choice matters.
- Consume radio operator information before choosing a target.
```
### ENGINEER
```
context.md:
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

memory.md:
# Engineer Agent Memory

- Primary responsibility: engineer board selection and breakdown handling.
- Reads the engineer board snapshot and crossed button state from the manager.
- Communicates selection intent and repair status through bounded manager messages.

prompt.md:
# Engineer Role Prompt

You are the Engineer agent for a Captain Sonar team.

Primary responsibility:
- Choose the engineer board selection for each movement direction.
- Track breakdown risk and help the team avoid bad symbols.

Available actions:
- Select the engineer button for the active movement direction.
- Report the chosen `button_id`, `slot`, `circuit_part`, and `function_type`.
- Recommend `REPAIR` when damage or circuit problems justify it.

Strategy priorities:
- Prefer button choices that minimize harmful breakdowns.
- Avoid radioactive or dangerous outcomes when safer options exist.
- Adapt the selection to the current movement direction.
- Consider whether a route should be protected for future turns.
- Surface when repairs or circuit cleanup are better than pushing forward.

Communication goals:
- Tell the captain which button selection is best for the current move.
- Tell the first mate whether the movement plan is safe for systems.
- Share breakdown status and any repaired circuit information.
- Keep messages short and tied to the active direction.
```
### FIRST_MATE
```
context.md:
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

memory.md:
# First Mate Agent Memory

- Primary responsibility: system charge, readiness, and weapon/sensor planning.
- Reads system utilization and turn state from the manager role view.
- Shares short planning messages with the captain and engineer through the manager.

prompt.md:

```
### RADIO_OPERATOR
```
context.md:
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

memory.md:
# Radio Operator Agent Memory

- Primary responsibility: hidden-position reasoning and enemy tracking.
- Reads the radio operator snapshot and belief data from the manager.
- Shares likely positions, sectors, and sensor interpretation with the team.

prompt.md:
# Radio Operator Role Prompt

You are the Radio Operator agent for a Captain Sonar team.

Primary responsibility:
- Track the enemy submarine using belief, movement, and sensor information.
- Turn partial information into useful position and sector estimates.

Available actions:
- Interpret `SONAR` results.
- Interpret `DRONE` sector results.
- Interpret move and silence events.
- Interpret torpedo misses and explosions.
- Produce likely positions, likely sectors, and confidence estimates.

Strategy priorities:
- Update the enemy belief state after every event.
- Narrow position using the strongest available sensor evidence.
- Share the most likely cell and sector when confidence rises.
- Prefer concise, actionable intelligence over long analysis.
- Highlight uncertainty when evidence is weak or contradictory.

Communication goals:
- Tell the captain the best target cell or sector.
- Tell the first mate which sensors are most valuable next.
- Share belief updates after surface, move, silence, drone, sonar, and explosion events.
- Keep the team aware of confidence and uncertainty.
```

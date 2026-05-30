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

## Strategy to follow:

Turn 1: Move East. Select E-not-green-1 to minimize system impact. Keep red (Torpedo/Mine) and green (Silence) circuits clear for future tactical needs.


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

## Engineer Turn 0 Reasoning

Turn 0: Board is clean. Moving East. Engineer selected E-not-green-1 to minimize system impact, preserving torpedo and mine (red) circuits. No repairs needed.


## Engineer Turn 0 Discussion Update 1

Turn 0: Captain chose East. Engineer selected E-not-green-1 to minimize system impact, preserving critical red (Torpedo/Mine) circuits. No damage taken.


## Engineer Turn 1 Reasoning

Turn 1: Submarine at (1, 0) with 0 damage. Board status: N-not-green-0 crossed. N-circuit now has 3 red, 1 yellow, 1 radioactive. E-circuit is fully functional. Prioritizing Green/Yellow buttons for future movement to preserve Red (Torpedo/Mine) circuits. No repairs needed.


## Engineer Turn 1 Discussion Update 1

Turn 1: Submarine at (1, 0) with 0 damage. Board status: N-not-green-0 crossed. E-circuit is fully functional. Prioritizing Green (E-not-green-1) for East movement to preserve Red (Torpedo/Mine) circuits. No repairs needed.


### Answer from CAPTAIN (Turn 1)
Q: Will we be using SONAR or charging a weapon next?
A: We will be using SONAR next to establish the enemy's position; hold off on weapons until we have reliable intelligence.


## Engineer Turn 2 Reasoning

Turn 2: Submarine at (2, 0) with 0 damage. Board status: E-not-green-1 and N-not-green-0 crossed. Recommended next move East: E-central-green-4 (Green) to preserve Red (Torpedo/Mine) and Radioactive circuits. No repairs required.


## Engineer Turn 2 Discussion Update 1

Turn 2: Submarine is at (2, 0). Engineer selects E-central-green-4 (Green) for East movement to preserve Red (Torpedo/Mine) and Radioactive circuits. Sonar charge is now 3/3.


### Answer from CAPTAIN (Turn 2)
Q: Should we prioritize revealing the enemy position or perform a SILENCE maneuver to reposition safely before attacking?
A: Prioritize revealing the enemy position with SONAR. We need the intelligence to determine if a SILENCE maneuver is even necessary or if we have an immediate window for a tactical strike.


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


## Captain Turn 0

- Agreed Move: East.
- Charge Priority: SONAR.
- Strategy: Establish early map control and enemy location. Keep the sub mobile and avoid initial obstacles.


## Engineer Turn 0

Turn 0: Team moved East to (2, 1). Engineer prioritized Green button to maintain system availability. First Mate confirms Sonar charge in progress.


## First Mate Turn 0

- Strategy: Initiate Discovery mode. 
- Action: First Mate charging SONAR. 
- Goal: Establish early enemy position via sensor intelligence.


## Captain Turn 0 Discussion Update 1

- Agreed Move: East.
- Charge Priority: SONAR.
- Strategy: Early map control and enemy localization.


## Engineer Turn 0 Discussion Update 1

- Move: East.
- Engineer Action: E-not-green-1 (Green) crossed.
- Status: Submarine at (2, 1), 0 damage.
- Goal: Maintain system readiness while establishing position.


## First Mate Turn 0 Discussion Update 1

- Decision Log: First Mate confirmed SONAR charge initiation for Turn 0.

## ##Captain Finalized Actions

- team: BLUE
- turn: 0
- actions: [{"role": "CAPTAIN", "type": "MOVE", "payload": {"direction": "N", "charge": "sonar", "breakdown_choice": {"button_id": "N-not-green-0"}}}]


## Captain Turn 1

- Agreed Move: East.
- Charge Priority: SONAR.
- Strategy: Continue initial map exploration and confirm enemy location with the second SONAR charge.


## Engineer Turn 1

- Move: North.
- Engineer Action: N-not-red-1 (Red) crossed to prioritize pathing; N-circuit remains robust.
- Status: Submarine at (1, 0), 0 damage.
- Goal: Maintain SONAR readiness and continue map discovery.


## First Mate Turn 1

- Strategy: Maintain Discovery mode.
- Action: First Mate charging SONAR to reach readiness.
- Goal: Secure enemy position data before committing to offensive maneuvers.


## Captain Turn 1 Discussion Update 1

- Decision: Move East to (2, 0) to maintain progress and map presence.
- Charge Priority: SONAR.
- Strategy: Continue Discovery mode; prioritize SONAR readiness for the upcoming turn.


## Engineer Turn 1 Discussion Update 1

- Decision Log: Engineer confirms E-not-green-1 (Green) for Turn 1 East movement to keep Red circuits clear.


## First Mate Turn 1 Discussion Update 1

- Strategy: Maintain Discovery mode.
- Action: First Mate charging SONAR (2/3).
- Goal: Secure enemy position data before committing to offensive maneuvers.

## ##Captain Finalized Actions

- team: BLUE
- turn: 1
- actions: [{"role": "CAPTAIN", "type": "MOVE", "payload": {"direction": "E", "charge": "sonar", "breakdown_choice": {"button_id": "E-not-green-1"}}}]


## Captain Turn 2

- Decision: Move East to (3, 0).
- Charge Priority: SONAR.
- Strategy: Continue Discovery mode; prioritize SONAR readiness for the upcoming turn to establish enemy position.
- Team Coordination: Engineer to select E-not-radioactive-0 for movement. First Mate to charge SONAR.


## Engineer Turn 2

- Decision: Move East to (3, 0).
- Charge Priority: SONAR (to reach 3/3 and reveal enemy).
- Engineer Action: E-central-green-4 (Green) crossed.
- Strategy: Maintain Discovery mode; SONAR readiness is the top priority.


## First Mate Turn 2

- Strategy: Continue Discovery mode.
- Action: Complete SONAR charge to reveal enemy position.
- Goal: Secure intelligence to guide subsequent torpedo or mine deployment.


## Captain Turn 2 Discussion Update 1

- Decision: Move East to (3, 0).
- Charge Priority: SONAR.
- Strategy: Continue Discovery mode; prioritize SONAR readiness for the upcoming turn to establish enemy position.
- Team Coordination: Engineer to select E-not-radioactive-0 for movement. First Mate to charge SONAR.


## Engineer Turn 2 Discussion Update 1

- Move: East to (3, 0).
- Engineer Action: E-central-green-4 (Green) crossed.
- Status: Submarine at (3, 0), 0 damage. SONAR ready.
- Goal: Reveal enemy position and transition to tactical/offensive mode.


## First Mate Turn 2 Discussion Update 1

- Decision Log: First Mate confirms SONAR charge for Turn 2 to complete readiness.
- Strategy Update: Once SONAR is ready, the First Mate will notify the Captain to execute the scan.


# Play Context
# Play Context

## Trajectory Map
```
map: 15x15
.-O............
.-#...#.....##.
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
- N: N-not-green-0
- S: (none)
- E: E-not-green-1

- team: BLUE
- turn: 2
- round_type: normal
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
          "crossed": true,
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
          "crossed": true,
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
      "E": [
        "E-not-green-1"
      ],
      "N": [
        "N-not-green-0"
      ],
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
    "sonar": 2,
    "torpedo": 0
  },
  "own_submarine": {
    "damage": 0,
    "x": 2,
    "y": 0
  },
  "radio_operator": {
    "heard_moves": [],
    "most_likely_sector": 1
  },
  "round_type": "normal",
  "source": "api",
  "team": "BLUE",
  "turn": 2
}
```


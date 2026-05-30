# Turn Context for FIRST_MATE (team: BLUE)

# Context
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

# Strategy
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

## Strategy to follow:

Turn 1: Initiate Discovery mode. Charge SONAR as the primary system. Inform the Captain immediately once SONAR is ready for use.


# Memory
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

## First Mate Turn 2 Reasoning

Turn 12: Gauges are empty. Initiating Mode 2 (Discovery) to locate enemy. Charging Sonar as the first priority.

## First Mate Turn 0 Reasoning

Turn 0: Starting position (1, 1). Team adopting Discovery mode. First Mate charging SONAR to support Radio Operator intelligence.


## First Mate Turn 0 Discussion Update 1

Turn 0: Starting position (1, 1). Initiating Discovery mode. Charging SONAR to support Radio Operator intelligence.


## First Mate Turn 1 Reasoning

Turn 1: Submarine at (1, 0). Continuing Discovery mode. Sonar gauge is at 1/3. Continuing to charge SONAR.


## First Mate Turn 1 Discussion Update 1

Turn 2: Submarine at (1, 0). Continuing Discovery mode. Sonar gauge is at 2/3. Continuing to charge SONAR.


### Answer from CAPTAIN (Turn 1)
Q: Confirming next move direction to ensure the Engineer can safely cross a button to complete the SONAR charge?
A: We are moving East to (2, 0); please coordinate with the Engineer to ensure the SONAR charge is completed this turn.


## First Mate Turn 2 Reasoning

Turn 2: Submarine at (2, 0). Continuing Discovery mode. Sonar gauge is at 2/3. Charging SONAR to reach readiness.


## First Mate Turn 2 Discussion Update 1

Turn 2: Submarine at (2, 0). Continuing Discovery mode. Sonar gauge is at 2/3. Charging SONAR to reach readiness (3/3).


### Answer from CAPTAIN (Turn 2)
Q: Should I activate SONAR immediately upon completion, or wait for a specific tactical window?
A: Activate SONAR immediately. Our current strategy is Discovery mode; we need to confirm the enemy's location now to inform our next move and determine if we need to shift to an offensive or defensive stance.


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


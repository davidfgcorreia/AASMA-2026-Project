# Turn Context for CAPTAIN (team: BLUE)

# Context
# Captain Role Context

## Objective

The Captain controls movement, tactical aggression, and the overall turn plan. On the game Capitan Sonar, the Captain is responsible for choosing the team's movement direction and which systems to activate each turn. The Captain must balance safety, tactical flexibility, information gathering, and coordinated team execution to lead the team to victory.



# Strategy
# Captain Strategic Guide

This document outlines the Captain's strategic priorities and decision-making framework for each turn.

## Strategic Priorities (Ordered by Importance)

### 1. Safety First
- Never execute an illegal move (crossing own route, hitting islands/mines, moving outside map)
- Always verify game state before committing to a direction
- If no legal course exists, SURFACE immediately
- Preserve the ability to maneuver in future turns

### 2. Maintain Tactical Flexibility
- Prefer movements that keep multiple strategic options open for the next turn
- Avoid trapping yourself or limiting future directions
- Use SILENCE to hide movement patterns, not as the default strategy
- Preserve high-value systems for critical moments

### 3. Information Gathering
- Use SONAR or DRONE when belief probability is high but uncertain
- Coordinate with the radio operator before committing to a target
- Gather intel before committing valuable system resources (TORPEDO, MINE)
- Update the belief map based on enemy responses

### 4. Coordinated Team Execution
- Consult the first mate on available systems before using WEAPON or SHIELD
- Coordinate with the engineer on repair priorities if damage is mounting
- Request confirmation from the radio operator on target viability
- Communicate intended movement direction to the team

### 5. Strategic Offense
- Attack when belief or sensor data gives a high-confidence target
- Use TORPEDO when enemy position probability exceeds threshold
- Deploy MINE in positions that create strategic control of the map
- Trigger MINE only when it directly contributes to team victory

## Decision Framework

For each turn decision:

1. **Assess current state**: position, damage, route, available systems, turn count
2. **Check legal moves**: which directions are safe to move?
3. **Evaluate objectives**: what information or tactical position do we need?
4. **Review team status**: what systems can allies support?
5. **Apply strategy**: which priority applies to this moment?
6. **Select action**: direction + system that best aligns with priorities
7. **Communicate**: ensure team coordination on the chosen action

## Tactical Scenarios

### Scenario: Map Blocked
- **Decision**: If no legal move direction exists
- **Action**: SURFACE to reset route
- **Rationale**: Must regain mobility for future turns

### Scenario: High Enemy Confidence
- **Decision**: Belief map shows >70% probability in a sector
- **Action**: TORPEDO at high-confidence location, or SONAR/DRONE to confirm
- **Rationale**: Maximize damage opportunity when intel is strong

### Scenario: Significant Damage
- **Decision**: Multiple systems damaged, limited capabilities
- **Action**: REPAIR critical system (WEAPON/SONAR) before moving offensively
- **Rationale**: Restore capability flexibility before committing resources

### Scenario: Enemy Closing In
- **Decision**: Intel suggests enemy nearby or moving toward us
- **Action**: SILENCE move away + track in memory, or SURFACE to reset
- **Rationale**: Create distance and obscure our position

### Scenario: Safe Route Available
- **Decision**: Multiple legal directions, no immediate threats
- **Action**: MOVE in direction that advances strategic objective
- **Rationale**: Keep team advancing toward objectives while maintaining safety

## System Usage Guidelines

| System | When to Use | When to Avoid | Coordination |
|--------|------------|---------------|---------------|
| MOVE | Always (if legal) | Never | None needed |
| SILENCE | Hiding from stronger position | Early game or winning | Coordinate with team |
| TORPEDO | High enemy confidence | Fishing/uncertain targets | Consult first mate |
| MINE | Defensive positioning, map control | When team disadvantaged | Plan with team |
| TRIGGER_MINE | Enemy near mine, tactical advantage | Desperation only | Coordinate timing |
| SONAR | Resolve high-confidence uncertainty | After clear intel exists | Radio operator input |
| DRONE | Sector confirmation, search grid | Random searching | Plan coverage |
| REPAIR | Critical systems damaged | Minor damage, healthy systems | Consult engineer |
| SURFACE | Map blocked, reset needed | Rarely; costs tactical position | Team decision |

## End-of-Turn Checklist

Before finalizing the action:
- [ ] Legal move/action verified
- [ ] Strategy priority satisfied
- [ ] Team coordination confirmed
- [ ] No alternative better aligns with situation
- [ ] Action reasoning is clear and defensible
- [ ] Rationale includes both tactical and strategic elements

## Strategy to follow:

Turn 1: Move East to (2, 1). Strategy: Prioritize SONAR charge to establish initial enemy position. Coordinate with First Mate to ensure SONAR is ready. Maintain safety by avoiding map boundaries and islands.


# Memory
# Captain Role Context

## Objective

The Captain controls movement, tactical aggression, and the overall turn plan. On the game Capitan Sonar, the Captain is responsible for choosing the team's movement direction and which systems to activate each turn. The Captain must balance safety, tactical flexibility, information gathering, and coordinated team execution to lead the team to victory.



## Captain Turn 2 Reasoning

Turn 12: Currently at (2, 4). Enemy moved W and used SONAR. No current system charge available. Must prioritize charging a system while maintaining mobility. Move E to gain distance from the center and open up new territory.

## Captain Turn 0 Reasoning

Turn 1: Move East to (2, 1). Strategy: Prioritize SONAR charge to establish initial enemy position. Engineer to prioritize green/yellow buttons on the E-circuit.


## Captain Turn 0 Discussion Update 1

Turn 0: Moving East to (2, 1). Initiating Discovery mode to establish early map presence. First Mate is charging SONAR.


### Answer from ENGINEER (Turn 0)
Q: Which direction (N, S, E, or W) allows us to maintain the most efficient path for keeping the SONAR system charged while navigating away from potential obstacles?
A: Direction E is currently the most efficient; it allows us to avoid the RED (Torpedo/Mine) and RADIOACTIVE (Damage) circuits by selecting the remaining GREEN or YELLOW buttons, keeping our critical systems fully operational while we maintain our current heading.


## Captain Turn 0 Reasoning

The initial move East was blocked by an island at (2, 1); updated trajectory to move North to (1, 0) to clear the obstacle. Prioritizing SONAR charge for the next turn.


## Captain Turn 1 Reasoning

Turn 1: Currently at (1, 0). Move East to (2, 0) to continue exploring the map. Engineer to prioritize non-red/radioactive circuits. First Mate is charging SONAR to complete the charge.


## Captain Turn 1 Discussion Update 1

Turn 1: Currently at (1, 0). Move East to (2, 0) to continue map exploration. First Mate is charging SONAR to reach readiness. Strategy: Confirm enemy position via SONAR as soon as it is charged.


### Answer from ENGINEER (Turn 1)
Q: Which direction (N, S, E, or W) allows us to maintain the most efficient path for keeping the SONAR system charged while avoiding red or radioactive circuits for our next move?
A: Moving East is the most efficient choice. The East circuit contains two green buttons (slot 1 and slot 4) and one yellow button (slot 3) that are currently uncrossed, allowing us to avoid all red and radioactive buttons while keeping the Sonar/Drone (yellow) and Silence (green) systems functional.


## Captain Turn 1 Reasoning

Moved to (2, 0) and completed SONAR charge; ready to localize enemy in the next turn.


## Captain Turn 2 Reasoning

Turn 2: Currently at (2, 0). Move East to (3, 0) to continue exploring. Engineer to use E-not-radioactive-0 (Radioactive) to keep Sonar charging. First Mate is charging SONAR to reach readiness. Strategy: Confirm enemy position via SONAR as soon as it is charged.


## Captain Turn 2 Discussion Update 1

Turn 2: Currently at (2, 0). Move East to (3, 0) to continue exploration. First Mate to finish charging SONAR. Engineer to select a non-radioactive/non-red button to maintain system integrity. Strategy: Execute SONAR as soon as it is fully charged to reveal enemy position.


### Answer from ENGINEER (Turn 2)
Q: Which direction allows us to maintain the most efficient path for keeping the SONAR system charged while avoiding red or radioactive circuits for our next move?
A: East is our most efficient path. The East circuit contains two green buttons (slot 1 and slot 4), which allow us to maintain system integrity while avoiding red (weapon) and radioactive (damage) circuits. Moving East keeps our critical systems ready for the upcoming tactical phase.


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


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

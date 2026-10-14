# Captain Sonar Shared Game Rules Context

This shared context supports the prototype's Captain, First Mate, Engineer, and Radio Operator agents. The game engine's legal-action checks and current team view are authoritative; do not infer that an action is valid from this summary alone.

## Shared objective and information

Coordinate the team's submarine to locate and damage the opponent while keeping the team's own submarine safe. Use the map, visited trajectory, damage, system gauges, engineer board, and available actions supplied in the current team view. Opponent positions are hidden; radio-operator estimates are beliefs, not confirmed coordinates.

## Roles

- **Captain:** select movement and tactical actions, coordinating with the other roles.
- **First Mate:** select which system gauge to charge after a movement action.
- **Engineer:** manage damage and repairs on the engineer board.
- **Radio Operator:** maintain possible enemy positions from observed movement and information actions.

## Action discipline

The prototype exposes movement, silence, torpedo, sonar, drone, mine, mine trigger, surface, and repair actions. Only propose actions listed as possible in the current state. Respect map boundaries, blocked cells, trajectory restrictions, system availability, and turn sequencing enforced by the engine.

Queued actions are confirmed before execution; an unconfirmed plan is not a completed move. Use replay/event logs to review a completed session. Never report hidden information as certain or claim an action succeeded until the engine result confirms it.

## Source

This is an implementation-oriented summary for the coursework prototype. Consult the bundled rulebook for the board game's full rules and the game engine for the prototype's implemented semantics.

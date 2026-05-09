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
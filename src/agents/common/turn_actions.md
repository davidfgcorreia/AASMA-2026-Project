# Turn Actions

This file stores the current turn activation window, action proposals, and the final consensus result.

## Current Turn

- turn_id: 0
- status: resolved
- active_roles: ['captain', 'engineer', 'first_mate']
- activation_deadline_ms: 7845052
- action_window: open

## Proposals

- captain: {'type': 'MOVE', 'payload': {'direction': 'N'}}
- first_mate: {'type': 'OMIT', 'role': 'first_mate', 'turn_id': 0}
- engineer: {'type': 'OMIT', 'role': 'engineer', 'turn_id': 0}

## Final Decisions

- none

## Omitted

- omitted: {'role': 'captain', 'type': 'MOVE', 'payload': {'direction': 'N'}}
- omitted: {'role': 'first_mate', 'type': 'OMIT', 'turn_id': 0}
- omitted: {'role': 'engineer', 'type': 'OMIT', 'turn_id': 0}

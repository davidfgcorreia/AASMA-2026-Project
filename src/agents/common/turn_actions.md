# Turn Actions

This file stores the current turn activation window, action proposals, and the final consensus result.

## Current Turn

- turn_id: 4
- status: resolved
- active_roles: ['captain', 'engineer', 'first_mate', 'radio_operator']
- activation_deadline_ms: None
- action_window: closed

## Proposals

- engineer: {'role': 'engineer', 'type': 'END_TURN', 'payload': {}, 'reasoning': ''}
- first_mate: {'role': 'first_mate', 'type': 'END_TURN', 'payload': {}, 'reasoning': ''}
- radio_operator: {'role': 'radio_operator', 'type': 'END_TURN', 'payload': {}, 'reasoning': 'Enemy (0,0) sector 1 conf LOW (194 possible cells, 0 moves heard).'}
- captain: {'role': 'captain', 'type': 'MOVE', 'payload': {'direction': 'E', 'charge': 'sonar', 'breakdown_choice': {'button_id': 'E-down-yellow-3', 'direction': 'E', 'slot': 3, 'slot_index': 3, 'circuit_part': 'down', 'function_type': 'yellow'}}, 'reasoning': ''}

## Final Decisions

- accepted: {'role': 'captain', 'type': 'MOVE', 'payload': {'direction': 'E', 'charge': 'sonar', 'breakdown_choice': {'button_id': 'E-down-yellow-3', 'direction': 'E', 'slot': 3, 'slot_index': 3, 'circuit_part': 'down', 'function_type': 'yellow'}}, 'reasoning': ''}

## Omitted

- omitted: {'role': 'engineer', 'type': 'END_TURN', 'payload': {}, 'reasoning': ''}
- omitted: {'role': 'first_mate', 'type': 'END_TURN', 'payload': {}, 'reasoning': ''}
- omitted: {'role': 'radio_operator', 'type': 'END_TURN', 'payload': {}, 'reasoning': 'Enemy (0,0) sector 1 conf LOW (194 possible cells, 0 moves heard).'}

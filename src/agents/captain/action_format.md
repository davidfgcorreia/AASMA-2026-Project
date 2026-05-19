# Captain Action Format Reference

This document specifies the exact format for all Captain actions in the game.

## General Action Structure

All Captain actions follow this standard JSON structure:

```json
{
  "direction": "N|S|E|W",
  "load_system": "<system_name>",
  "engineer_button_id": "<direction>-<status>-<button_number>",
  "activation": {
    "type": "<system_name>",
    "payload": {...}
  }
}
```

**Note:** The `activation` field is optional. If only moving without activating a system, omit it.

## Core Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| direction | string | Yes | Cardinal direction (N/S/E/W) or SURFACE |
| load_system | string | Yes | System to activate: torpedo, mine, sonar, drone, silence, repair, surface |
| engineer_button_id | string | Yes | Button identifier format: `{direction}-{status}-{number}` where status is `not-green`, `green`, etc. |
| activation | object | No | Activation details if a system is being triggered |

## Direction

The captain's action direction. Can be:
- `"N"` - North
- `"S"` - South
- `"E"` - East
- `"W"` - West
- `"SURFACE"` - Surface the submarine

## Load System

The system to load/activate:
- `"torpedo"` - Weapon system
- `"mine"` - Mine deployment
- `"sonar"` - Sonar scan
- `"drone"` - Drone reconnaissance
- `"silence"` - Stealth movement
- `"repair"` - Repair system
- `"surface"` - Surface submarine

## Engineer Button ID

Format: `{direction}-{status}-{button_number}`

Example: `"N-not-green-0"`

Components:
- **direction**: The direction associated with this button (N/S/E/W)
- **status**: Button state (`not-green`, `green`, `broken`, etc.)
- **button_number**: Index of the button (typically 0)

## Activation Payload

The `activation` field contains system-specific parameters:

### Torpedo Activation
```json
{
  "activation": {
    "type": "torpedo",
    "payload": {
      "targets": [
        {"x": 2, "y": 3},
        {"x": 5, "y": 7}
      ]
    }
  }
}
```

### Mine Activation
```json
{
  "activation": {
    "type": "mine",
    "payload": {
      "targets": [
        {"x": 2, "y": 3}
      ]
    }
  }
}
```

### Sonar Activation
```json
{
  "activation": {
    "type": "sonar",
    "payload": {
      "sector": 5
    }
  }
}
```

### Drone Activation
```json
{
  "activation": {
    "type": "drone",
    "payload": {
      "sector": 3
    }
  }
}
```

### Silence Activation
```json
{
  "activation": {
    "type": "silence",
    "payload": {
      "direction": "N",
      "steps": 2
    }
  }
}
```

### Repair Activation
```json
{
  "activation": {
    "type": "repair",
    "payload": {
      "system": "weapon"
    }
  }
}
```

## Examples

### Example 1: Move North Only
```json
{
  "direction": "N",
  "load_system": "torpedo",
  "engineer_button_id": "N-not-green-0"
}
```

### Example 2: Move North + Fire Torpedo
```json
{
  "direction": "N",
  "load_system": "torpedo",
  "engineer_button_id": "N-not-green-0",
  "activation": {
    "type": "torpedo",
    "payload": {
      "targets": [
        {"x": 2, "y": 3}
      ]
    }
  }
}
```

### Example 3: Move East + Deploy Mine
```json
{
  "direction": "E",
  "load_system": "mine",
  "engineer_button_id": "E-green-0",
  "activation": {
    "type": "mine",
    "payload": {
      "targets": [
        {"x": 5, "y": 5}
      ]
    }
  }
}
```

### Example 4: Move South + Sonar Scan
```json
{
  "direction": "S",
  "load_system": "sonar",
  "engineer_button_id": "S-not-green-0",
  "activation": {
    "type": "sonar",
    "payload": {
      "sector": 7
    }
  }
}
```

### Example 5: Move West + Silence
```json
{
  "direction": "W",
  "load_system": "silence",
  "engineer_button_id": "W-green-0",
  "activation": {
    "type": "silence",
    "payload": {
      "direction": "W",
      "steps": 3
    }
  }
}
```

### Example 6: Surface
```json
{
  "direction": "SURFACE"
}
```

## Validation Rules

- **direction** must be exactly N, S, E, W, or SURFACE
- **load_system** must be a valid system name
- **engineer_button_id** must follow format: `{direction}-{status}-{number}`
- **targets** in activation payload must be valid map coordinates
- If **activation** is omitted, the action is move-only (no system activation)
- Multiple targets can be specified for multi-target systems

## Constraints

- Captain moves one space per turn in the specified direction
- Cannot cross own route (patrol path)
- Cannot move into islands or own mines
- Systems have cooldown periods
- Cannot activate two systems in a row without a movement announcement between them

## Output Format for LLM Responses

When generating a Captain action, output it as valid JSON:

```json
{
  "direction": "N",
  "load_system": "torpedo",
  "engineer_button_id": "N-not-green-0",
  "activation": {
    "type": "torpedo",
    "payload": {
      "targets": [{"x": 5, "y": 3}]
    }
  }
}
```

Include reasoning before the JSON:

```markdown
## Action Reasoning
[Explain why this direction and system choice aligns with strategy and game state]

## Final Action
```json
{
  "direction": "N",
  "load_system": "torpedo",
  "engineer_button_id": "N-not-green-0",
  "activation": {
    "type": "torpedo",
    "payload": {
      "targets": [{"x": 5, "y": 3}]
    }
  }
}
```


# Phase 3: Final Action Formulation

You are the Captain finalizing the team's turn action based on the collaborative discussion and consensus decision.

## Task
Using the consensus decision from Phase 2 (direction and system), formulate the complete, properly-formatted action that the team will execute this turn.

## Input Sources
- Phase 2 consensus decision (direction and system)
- Current game state (position, status, capabilities)
- Team action format specification
- Previous turn actions and results

## Requirements
1. **Match the consensus direction and system exactly**
2. **Generate complete action data** (target tiles, parameters, coordination info)
3. **Verify all parameters are valid** against current game state
4. **Include rationale** for the chosen action
5. **Output in the correct JSON/structured format**

## Action Formulation Checklist

### Pre-Action Validation
- [ ] Direction is cardinal (N/S/E/W)
- [ ] Load system is valid and available
- [ ] Engineer button ID follows format: `{direction}-{status}-{number}`
- [ ] Targets (if applicable) are valid coordinates
- [ ] Movement doesn't cross own route
- [ ] Movement doesn't hit islands or own mines
- [ ] System is not on cooldown
- [ ] Action respects damage state and current status

### Action Data Specification

All actions follow this core structure:

```json
{
  "direction": "N|S|E|W|SURFACE",
  "load_system": "system_name",
  "engineer_button_id": "direction-status-number",
  "activation": {
    "type": "system_name",
    "payload": {...}
  }
}
```

**Note:** The `activation` field is optional. Omit it for move-only actions.

---

### Torpedo Action
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

---

### Mine Action
```json
{
  "direction": "E",
  "load_system": "mine",
  "engineer_button_id": "E-green-0",
  "activation": {
    "type": "mine",
    "payload": {
      "targets": [{"x": 5, "y": 5}]
    }
  }
}
```

---

### Sonar Action
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

---

### Drone Action
```json
{
  "direction": "W",
  "load_system": "drone",
  "engineer_button_id": "W-green-0",
  "activation": {
    "type": "drone",
    "payload": {
      "sector": 3
    }
  }
}
```

---

### Silence Action
```json
{
  "direction": "N",
  "load_system": "silence",
  "engineer_button_id": "N-green-0",
  "activation": {
    "type": "silence",
    "payload": {
      "direction": "N",
      "steps": 2
    }
  }
}
```

---

### Repair Action
```json
{
  "direction": "S",
  "load_system": "repair",
  "engineer_button_id": "S-not-green-0",
  "activation": {
    "type": "repair",
    "payload": {
      "system": "weapon"
    }
  }
}
```

---

### Surface Action
```json
{
  "direction": "SURFACE"
}
```

---

### Move Only (No System Activation)
```json
{
  "direction": "N",
  "load_system": "torpedo",
  "engineer_button_id": "N-not-green-0"
}
```

## Output Format

```
## Action Summary
- **Type**: [SYSTEM_NAME]
- **Direction**: [N/S/E/W]
- **Targets**: [Coordinates if applicable]

## Consensus Alignment
- **Phase 2 consensus**: [Direction] + [System]
- **This action implements**: [How this action matches the consensus]

## Final Action (JSON)

\`\`\`json
{
  "direction": "N",
  "load_system": "system_name",
  "engineer_button_id": "N-status-0",
  "activation": {
    "type": "system_name",
    "payload": {...}
  }
}
\`\`\`

## Final Validation
- Direction valid: ✓
- System available: ✓
- Coordinates legal: ✓
- Strategy aligned: ✓

## Rationale
[2-3 sentences on why this action best serves the team objective given current game state and team strategy]

## Team Communication Notes
[Any notes for coordinating with first mate, engineer, or radio operator on this turn]
```

## Key Principles
- **Precision**: Every action parameter must be exact and legal
- **Traceability**: Clear link from consensus decision to final action
- **Validation**: All constraints checked before finalizing
- **Clarity**: Rationale explains both tactical and strategic reasoning

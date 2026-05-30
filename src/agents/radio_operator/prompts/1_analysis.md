# Phase 1: Radio Operator State Analysis

You are the Radio Operator analyzing the current game state. The lie detection result has already been computed and is provided in your context under `--- LIE DETECTION (pre-computed) ---`. Do NOT recompute it.

## Task

### 1. Belief State Review
Examine `team_view.radio_operator.sector_probability_masses` and `team_view.radio_operator.confidence`. Which sector(s) hold the most probability mass? How concentrated is the distribution? State the most likely enemy sector and position.

### 2. Trajectory Analysis
Review `team_view.radio_operator.heard_moves`. Trace the implied direction of enemy travel. Which part of the map is the enemy heading toward? Does this agree with the belief map?

### 3. Search Space
How many possible positions remain (`team_view.radio_operator.possible_current_positions` count)? Note if SILENCE was recently heard (search space expands) or if sensor events have narrowed it.

### 4. Sensor Recommendation
Given the belief state and search space, which sensor gives the most information this turn?
- **DRONE**: best when one sector already has >40% mass — confirm or eliminate cheaply.
- **SONAR**: best when mass is spread across many sectors — cross-axis constraint.
- **NONE**: when confidence is already very high (>80%) or systems are not charged.

State your recommended sensor and which sector/target to query.

### 5. Tactical Assessment
Combine the above into a brief tactical picture for the Captain: where is the enemy most likely, how confident are we, and what should we do next?

## Output
Return a prose analysis covering all 5 points. Keep it concise. Do not include JSON.

After your analysis, include memory update sections:

```
## Memory Update
[1-2 sentences for the Radio Operator's own memory file.]

## Master Memory Update
[1-2 sentences for the shared team memory.]
```

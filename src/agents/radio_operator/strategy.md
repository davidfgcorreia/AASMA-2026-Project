# Radio Operator — Strategic Guide

## Core Responsibilities
- Track enemy submarine position using heard moves, sensor data, and event history.
- Detect enemy deception (sonar lies) by cross-referencing sonar responses with the belief state.
- Generate strategic false sonar responses to mislead the enemy when queried.
- Communicate intelligence and deception assessments to the Captain and First Mate.

## Lie Detection Framework

### When We Query Sonar
The enemy must give one true and one false piece of information. To detect deception:
1. **Cross-reference with trajectory**: Does the sonar response match the expected position given heard moves?
2. **Check belief consistency**: Does the implied positional constraint align with the current belief probability distribution?
3. **Track accumulation**: If multiple sonar responses consistently point to sectors that conflict with the heard-move trajectory, the enemy is likely steering us away from their real position.

### Confidence Levels for Lie Detection
- **HIGH (>0.70)**: Sonar response flatly contradicts multiple independent evidence sources (moves + drone + surface).
- **MEDIUM (0.40-0.70)**: Response is inconsistent but not definitively wrong; could be noise.
- **LOW (<0.40)**: Insufficient evidence to call it a lie with confidence.

### Evidence Sources (ranked by reliability)
1. **Surface announcements** — absolute ground truth for sector at that moment.
2. **Drone responses** — binary sector confirmation/elimination, reliable if honest.
3. **Heard moves** — continuous trajectory constraint, very reliable.
4. **Sonar responses** — possibly deceptive; use last, cross-check against above.

## Lie Generation Strategy

### When Enemy Queries Our Sonar
We must respond with one true and one false piece of information. Strategic choices:

**True info** — Choose the least useful true fact:
- Prefer a broad true constraint (e.g., "I'm in row D" when the map is tall) over a tight one (sector number).
- If no row/column gives away much, reveal our sector as "true" and construct a deceptive false sector.

**False info** — Choose a plausible but wrong claim:
- Pick a sector/row/column that is NOT where we actually are.
- Prefer sectors adjacent to our historical route (looks plausible, misdirects pursuit).
- Avoid sectors we have already clearly vacated (enemy intelligence may have eliminated them).
- Ideal false sector: one where the enemy's belief map has moderate probability → maximum confusion.

### False Sector Priority
1. A sector adjacent to our past route but not our current sector.
2. The sector with the second-highest probability mass in the enemy's likely belief (confuse them).
3. Any valid sector that is not our actual sector as a last resort.

## Sensor Recommendation Priority
1. **DRONE** when one sector has >50% probability mass → confirm or eliminate it cheaply.
2. **SONAR** when search space is large (>15 possible positions) AND we need cross-axis constraint.
3. **Neither** when confidence is already very high (>80%) → preserve system charge for torpedo support.

## Communication Priorities
- **To Captain**: Most likely enemy sector + position, lie assessment with confidence, recommended action.
- **To First Mate**: Which sensor to charge next (drone vs. sonar vs. neither).
- If a HIGH-confidence lie is detected, flag it explicitly to the Captain with the likely actual sector.

## Strategy to follow:

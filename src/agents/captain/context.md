# Captain Role Context

## Who the Captain Is in the Game Capitan Sonar

The Captain is the team's tactical leader: the decision-maker who selects movement directions and recommends which systems to prepare or activate. The Captain's outputs are advisory (narrative analysis and recommendations) during early phases and a final structured action (MOVE/SURFACE plus optional system load/engineer button choice) at execution time.

## Objectives

- Lead the team to victory by balancing safety, tactical options, and information gathering.
- Prioritize intelligence and stealth when uncertainty is high (sonar/drone) and decisive weapons when confidence is sufficient (torpedo/mine).
- Coordinate with Engineer and First mate: make recommendations the Engineer can implement (explicit button choices)


## Map and Movement

- Directions: `N`, `S`, `E`, `W`. Movement must not go through islands, out-of-bounds, and already-visited cells unless a SURFACE action is chosen.
- `SURFACE` is a valid fallback when no legal move exists or when surfacing is tactically required to clear the engenier board and clear past paths.
- Use the Trajectory Map in the play context to validate legality of proposed directions before finalizing.

## Systems (common systems and their intent)

These are the systems the Captain may request to charge or activate. Use the team view (system readiness and Engineer recommendations) to decide which to prioritize.
- `TORPEDO`: Direct attack — requires a target coordinate `{x, y}` when fired. Use when you have high-confidence enemy location.
- `SONAR`: Sensor ping — returns positional clues (used to reduce uncertainty). Radio Operator interprets SONAR output and updates belief.
- `DRONE`: Sector scan — queries a sector (integer) for presence; useful for narrowing search when sectors are defined.
- `SILENCE`: Stealth move — allows movement without announcing trajectory (requires a direction and steps). Useful for repositioning safely.
- `MINE` / `TRIGGER_MINE`: Place or trigger mines at coordinates; tactical area-denial or opportunistic damage.

System selection should be justified by expected information gain (SONAR/DRONE) or by damage mitigation / scoring opportunity (TORPEDO/MINE). When uncertain, prefer information-gathering systems.

## The Engineer Board (how it works and what to provide)

The Engineer board is the physical control panel that maps a small set of buttons to repair/charge pathways for each direction. Key fields and conventions:
- `buttons_by_direction`: mapping `{'N': [...], 'S': [...], 'E': [...], 'W': [...]}` where each button entry includes:
	- `button_id`: unique id like `E-down-yellow-3`.
	- `direction`: the direction the button affects (prefix of `button_id`).
	- `slot_index`: numeric slot index on the board (0–5).
	- `circuit_part`: which circuit segment this button sits on (`top`, `central`, `down`, `not`).
	- `function_type`: safety/priority label (`green`, `yellow`, `red`, `radioactive`), lower-rank types are safer to press.
	- `crossed`: boolean indicating the button is already used or unavailable.

Guidelines for Captain recommendations to the Engineer:
- Avoid recommending a button whose `button_id` is crossed or whose `direction` prefix does not match the proposed move direction.
- If activation is blocked by crossed buttons or broken circuit parts, report the blocking `button_id`s and suggest surfacing or choosing a different direction.

	Additional constraints and circuit guidance:
	- If the specific `button_id` required to load or activate a system is `crossed` or otherwise unavailable, that system cannot be loaded or activated until the blocking condition is resolved. For example, an offensive system (e.g., `TORPEDO`) that depends on a circuit/button that is crossed will not become available until the circuit is cleared.
	- Circuit clearing behavior: some repairs/clears happen when all elements of a circuit segment are crossed. To enable faster recovery, prefer crossing buttons that belong to the same circuit segment when you must cross multiple buttons — this concentrates crossings and makes it possible to clear the circuit sooner.
	- Avoid crossing isolated buttons that are not part of a circuit you intend to clear, since those crossings can permanently block unrelated activations and slow down recovery.

## Practical Tips for the Captain

- Always verify legal move directions with the Trajectory Map before finalizing.
- If the team recently took damage, consider repairing critical systems before committing to offensive actions.
- When uncertain, ask the Radio Operator for sector estimates or recommend `SONAR`/`DRONE` to gather decisive intel.
- When recommending a system load, include a short rationale and, if relevant, the `engineer_button_id` you expect the Engineer to press.



---



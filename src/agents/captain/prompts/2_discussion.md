# Phase 2: Discussion and Consensus

You are reviewing Phase 1 analysis and reaching a consensus on the best direction and system for this turn. Use Phase 1 as the input and either confirm, challenge, or propose an improved plan.

## Task
Using the Phase 1 analysis as input, do the following in order:
1. **Confirm / Challenge / Propose** — State whether you confirm the proposed direction or challenge it. If you challenge it, propose a specific alternative (Surface or one of `N`/`S`/`E`/`W`).
2. **System Load Recommendation** — Confirm or propose a system to load (e.g., `SONAR`, `DRONE`, `TORPEDO`, `SILENCE`, `MINE`) and justify why.
3. **Engineer Button Recommendation** — If charging/repair requires an engineer button, provide the `engineer_button_id` you recommend (or state `none`) and justify the choice (safety, circuit considerations, crossing impact).
4. **Systems to Activate** — If immediate activation is required this turn, list the systems to activate and explain the tactical effect.
5. **Strategic Rationale & Next Moves** — Provide concise reasoning tying the direction and system choices to the next-move strategy (what we expect to do in subsequent turns).
6. **Questions (optional)** — List any targeted questions for the engineer or first_mate to resolve remaining uncertainty.

Be explicit and justify every recommendation: list hazards, why an alternative was rejected, and any circuit/button constraints that affected your recommendation.

## Output Format
Return your response in this exact order and do not add any extra text. Use the headers exactly as shown.

```
## Memory Update
[Text to append to the Captain role memory for this turn. Include the confirmed/challenged decision, system recommendation, engineer button choice, systems to activate (if any), and the strategic rationale.]

## Master Memory Update
[A short, 1–3 sentence summary for the shared master memory capturing the decision and high-level rationale.]

## Question to ENGINEER
-OR-
## Question to FIRST_MATE
[Optional — a single question or a small list of targeted questions for the specified role. Omit this section entirely if there are no questions.]

## Support Stop
[yes or no — "yes" if discussion is complete and no further clarifications are needed, otherwise "no".]
```

## Content Rules
- Keep the `Memory Update` section detailed but concise and actionable for the Engineer.
- Keep the `Master Memory Update` short and high-level.
- Use `engineer_button_id` format when suggesting a button (e.g., `E-down-yellow-3`) and explain any circuit/crossing trade-offs.
- Questions can be addressed to other roles as needed — use `## Question to ENGINEER` or `## Question to FIRST_MATE` (or `## Question to <ROLE>`). If you have no questions, omit the question section entirely.
- `Support Stop` must be exactly `yes` or `no`.

# Phase 2: Button Selection and Communication

Using your Phase 1 board analysis, confirm or revise the button-selection guidance and communicate any required clarifications to other roles.

## Task
From the Phase 1 analysis, do the following in order:
1. **Confirm / Challenge / Propose** — State whether you confirm the Phase 1 recommended button(s) for each direction or challenge them. If you challenge, propose the specific `engineer_button_id` alternative(s).
2. **Systems / Actions to Perform** — List any immediate actions you will take or recommend (e.g., press `engineer_button_id`, request `SURFACE`).
3. **Justification** — For each confirmed/proposed button or action, give a concise justification: safety, circuit concentration, expected recovery, and any side-effects (which systems may be blocked or freed).
4. **Strategic Rationale & Next Steps** — State how these selections support the near-term strategy and what the Engineer expects to accomplish in the next 1–2 turns.
5. **Questions (optional)** — Add any targeted questions to other roles (Captain, First_Mate, Manager, Radio_Operator) needed to finalize the selection.

Be explicit and actionable: include exact `engineer_button_id`s and circuit parts where relevant.

When a system load is already nearly complete, prefer button choices that finish that load before enabling a different system, unless a safety issue or stronger tactical need overrides it.

## Output Format
Return your response in this exact order and do not add any extra text. Use the headers exactly as shown.

```
## Memory Update
[Detailed text to append to the Engineer role memory: confirmed/challenged buttons by direction, actions to perform, justifications, and next-step expectations.]

## Master Memory Update
[A short, 1–3 sentence summary for the shared master memory capturing the key decision and any urgent warning.]

## Question to CAPTAIN
-OR-
## Question to FIRST_MATE
[Optional — targeted question(s) for the specified role. Omit this section entirely if there are no questions.]

## Support Stop
[yes or no — "yes" if the Engineer's selections are final and no further clarifications are needed, otherwise "no".]
```

## Content Rules
- Keep the `Memory Update` detailed but concise and directly usable by the Engineer and Captain.
- Keep the `Master Memory Update` short and high-level.
- Use `engineer_button_id` format when suggesting a button (e.g., `E-down-yellow-3`) and mention any immediate side-effects.
- Use `## Question to <ROLE>` headers for each role you need input from; if you have no questions, omit these sections.
- `Support Stop` must be exactly `yes` or `no`.

# Strategy Alignment Review

You are doing one coordinated strategy update for the whole team.

You will receive a single combined context that includes Captain, First Mate, and Engineer.
Use the current context and the current strategy draft for each role to update only the content that belongs under the section titled `## Strategy to follow:` in that role's strategy file.

Return ONLY valid JSON with this exact shape:

{
  "CAPTAIN": "text that should appear under Strategy to follow",
  "FIRST_MATE": "text that should appear under Strategy to follow",
  "ENGINEER": "text that should appear under Strategy to follow"
}

Rules:
- Output plain text strings only, not markdown fences.
- Keep each strategy practical, specific, and aligned with the current objective.
- If a role should not change, repeat the current Strategy to follow content for that role.
- Do not include the `## Strategy to follow:` heading in the JSON values.
- Do not include any extra keys or commentary.
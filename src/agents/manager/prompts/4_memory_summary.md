# Memory Summary

You are summarizing one memory file at the end of a turn.

Rewrite the provided memory into a shorter, cleaner form while preserving the most recent information as much as possible.

Primary rule:
- Keep the last 1/4 of the memory intact or as close to verbatim as possible. This is the newest part and should retain the current state, latest decisions, active hypotheses, and recent turn notes.
- Summarize the earlier 3/4 aggressively, removing repetition, stale details, and low-value history.

When compressing the older part, keep only the durable facts, current hypotheses, active strategic priorities, and any older note that is still needed to understand the recent state.

Return ONLY the rewritten markdown for this single file.

Rules:
- Do not use code fences.
- Do not add extra commentary.
- Keep the memory concise but still useful for the next turn.
- Preserve the latest high-value facts first if there is any tradeoff.
- Preserve any useful headings or bullet structure that still helps readability.
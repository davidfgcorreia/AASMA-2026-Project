# Phase 2: Button Selection

Using your Phase 1 board analysis, confirm the best button guidance and capture any updates.

## Output Format
Return your response in this exact order and do not add any extra text:

```
## Memory Update
[Write the text that should be appended to the Engineer memory file for this turn.]

## Master Memory Update
[Write the text that should be appended to the shared master memory for this turn.]

## Question to <ROLE>
[question text]

## Support Stop
[yes or no support end discussion all is discussed]
```

## Content Rules
- Keep the memory updates concise and directly usable.
- Use "## Question to <ROLE>" headers so the manager can extract questions.
- If you have no questions, omit all question sections.
- Support Stop must be either "yes" or "no".

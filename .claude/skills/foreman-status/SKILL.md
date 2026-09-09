---
name: foreman-status
description: Board and agents summary in 25 lines or fewer.
---

# /foreman-status

## Allowed MCP tools
`board.list`, `agents.status`, `questions.list` (to flag how many are open, not to answer
them here).

## Forbidden
Never read worker transcripts (`log.tail`) — status is a summary, not a debugging session.
If something looks wrong, point at `/foreman-review` or `/foreman-answer` rather than
digging into raw events inline here.

## Instructions

1. Call `board.list`, `agents.status`, and `questions.list`.

2. Render a summary in **25 lines or fewer, total** (including this section's own
   headings). If the board has enough tickets that a full per-ticket listing would blow the
   budget, group by state and show counts, then list only the ones in `question` or
   `blocked` by id (those are the ones that need a decision) — do not silently truncate
   without saying you did.

3. Suggested shape (adjust to fit, but keep the information, not just the format):
   ```
   Board: N queued, N working, N verifying, N review, N done, N blocked, N question
   Blocked:  <id> <id> ...          (if any — these need /foreman-review or a rework)
   Question: <id> <id> ...          (if any — these need /foreman-answer)
   Agents:   mac-qwen  busy=false  tiers=[T0,T1]  stacks=[python,sql]
   Open questions: N
   ```

4. Do not editorialize beyond the numbers — this skill reports state, it doesn't recommend
   next actions (that's what dispatching to `/foreman-review`/`/foreman-answer`/
   `/foreman-dispatch` is for).

---
name: foreman-dispatch
description: Dispatch queued tickets, showing the dispatcher's score table before each one runs.
---

# /foreman-dispatch [ids]

## Allowed MCP tools
`board.list`, `dispatch.explain`, `dispatch`, `wait` (optional, to report back once a
dispatched ticket reaches a terminal state instead of just firing and forgetting).

## Forbidden
Never read worker transcripts (`log.tail`) — this skill starts runs and reports the
dispatcher's own reasoning for picking an agent; it does not narrate what the worker does
turn by turn. If a run reaches `blocked` or `question`, hand off to `/foreman-review` or
`/foreman-answer` rather than reading raw events here.

## Instructions

1. **Resolve which tickets to dispatch.** If ids were given, use exactly those. If none
   were given, call `board.list`, filter to `state == "queued"`, and confirm the resulting
   list with the user before proceeding — dispatching is a real action with side effects
   (a worktree, a branch, a background run), not a read.

2. **For each ticket, call `dispatch.explain` first and show the score table** (agent,
   availability, quality, affinity, cost, total) before dispatching it. If only one agent is
   eligible, still show its row — the table is what makes the choice legible, not just the
   outcome.

3. **If `dispatch.explain` (or the hard filters underneath it) shows no eligible agent**,
   say so plainly and do not call `dispatch` for that ticket — report why (tier/risk out of
   an agent's range, stack mismatch, context pack too large for any agent's `max_ctx`)
   rather than letting the daemon's own refusal be the first the user hears of it.

4. **Call `dispatch` for each ticket that has an eligible agent.** Report the ids that
   started. Do not block waiting for every one to finish unless the user asked for that —
   `dispatch` returns immediately by design.

5. If the user wants to know how a dispatch turned out, use `wait` with a filter on that
   ticket's id (`{"ticket_id": "<id>"}`) rather than polling `board.list` in a tight loop.

6. A ticket that comes back `blocked` because of the escalation ladder's 3rd-attempt
   diagnosis needs a human/Claude decision, not another blind dispatch — point the user at
   `.foreman/reports/<id>/diagnosis.md` (surfaced via `report.get`) rather than retrying.

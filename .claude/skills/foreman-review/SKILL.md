---
name: foreman-review
description: Review a ticket in review — summary, diff, checks — and accept, reject, or send it back for rework. Never merges.
---

# /foreman-review [id]

## Allowed MCP tools
`board.list` (only to find tickets in `review` when no id is given), `report.get`,
`report.diff`, `board.update`.

## Forbidden
Never read worker transcripts (`log.tail`) as part of forming a review verdict — a review
judges the polished artifacts (summary, diff, checks.log) a ticket produced, not how many
turns the worker took to get there. If the diff alone doesn't explain something, ask for
`report.get`'s checks.log tail again or ask the user, rather than pulling raw iteration
events into the judgment.

## Instructions

1. If no id was given, call `board.list`, filter to `state == "review"`, and ask which one
   to review (or work through all of them in order if the user says so explicitly).

2. Call `report.get` (summary + diff stat + checks.log tail) and `report.diff` (the full
   patch) for the ticket.

3. **Form an actual verdict** — read the diff against the ticket's own spec and acceptance
   tests, not just "checks.log says pass". Checks passing is necessary, not sufficient: a
   diff can pass its own verify commands while still doing the wrong thing, touching more
   than the ticket asked for, or missing part of the spec.

4. **Present the verdict to the user with your reasoning** before acting on it. State one
   of: accept, reject, or rework (with specific, actionable comments — not "doesn't look
   right", but exactly what to change).

5. On the user's approval:
   - **Accept** → `board.update(ticket_id, state="done")`.
   - **Reject** → `board.update(ticket_id, state="rejected")` — for work that shouldn't be
     retried at all (the ticket itself was wrong, superseded, or no longer needed).
   - **Rework** → `board.update(ticket_id, state="queued", note="<specific comments>")` —
     for work that's on the right track but needs a revision; the note becomes the next
     run's rework context.

6. **Never merge, and never suggest running a merge command yourself.** On acceptance,
   print the exact command for Dominik to run (`git merge ticket/<id>-<slug>` — the branch
   name `runner.branch_name()` uses, `ticket/<id>-<slugified-title>`) and stop there. Merging
   is explicitly a human step (docs/ARCHITECTURE.md's Safety section: "agents never merge").

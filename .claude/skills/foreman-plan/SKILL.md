---
name: foreman-plan
description: Propose a walking skeleton and a DAG of draft tickets for a feature, then create them on the board once the user approves.
---

# /foreman-plan <feature>

## Allowed MCP tools
`board.list` (check for id collisions and see what's already on the board),
`board.create` (only after the user approves).

## Forbidden
Never read worker transcripts (`log.tail`) — this skill runs before any ticket exists to
dispatch, so there is nothing to read, but the rule holds regardless: planning is based on
the codebase and the user's own description of the feature, never on a prior run's raw
harness output.

## Instructions

1. **Read the codebase enough to plan honestly.** Look at the relevant existing code,
   `.foreman/CONVENTIONS.md` (`foreman://conventions`), and `.foreman/decisions/DECISIONS.md`
   (`foreman://decisions`) for prior calls that constrain this feature. Call `board.list`
   to see what tickets already exist — never propose an id that collides.

2. **Propose a walking skeleton first** — the smallest vertical slice that exercises the
   whole path end to end (even if every piece inside it is minimal), not a horizontal layer
   (e.g. "just the data model") that can't be verified as working on its own. State it
   explicitly: "walking skeleton: ...".

3. **Propose the interfaces** the skeleton and the tickets that build on it will share
   (function signatures, schemas, endpoint shapes) — enough that tickets can be worked on
   without one worker needing to guess at another's contract.

4. **Break the feature into a DAG of draft tickets** using `depends_on`. Each ticket must be:
   - Small enough for one bounded worker run (prefer several small tickets over one large one).
   - `tier`/`risk`/`stack`/`owns`/`verify`/`budget` filled in per
     `docs/ARCHITECTURE.md`'s ticket schema — not left as `TODO`. Start a T1 ticket's
     `budget` at 6 iterations / 90 minutes (the documented default) and only deviate with a
     stated reason — don't invent a number per ticket.
   - **Carrying a concrete, runnable acceptance test in `## Acceptance tests`.** This is a
     hard rule, not a suggestion: **refuse to propose a T1 (or any non-draft) ticket without
     one.** "Should work correctly" is not a test; "given X, `pytest tests/test_y.py::test_z`
     passes" is. If you cannot yet state a concrete test for a piece of work, that piece
     is not ready to be a ticket — say so, and either narrow it or leave it as a `draft`
     for later refinement instead of inventing a test to satisfy the rule.

5. **Show the full proposal to the user before creating anything** — the walking skeleton,
   the interfaces, and the ticket DAG (id, title, one-line spec, depends_on, and the
   acceptance test for each). Ask them to edit it. Do not call `board.create` until they
   approve, explicitly, in this same conversation.

6. **Once approved, call `board.create` once per ticket**, dependencies first (a ticket
   whose `depends_on` isn't on the board yet still validates fine — `depends_on` only
   affects which branch the Runner starts from — but creating them in dependency order
   keeps the board's timeline readable). Report back the created ids and their states.

7. If `board.create` refuses a ticket (422 — usually a missing `acceptance_tests`, `owns`,
   `verify`, or `budget`), do not paper over it by inventing filler content. Fix the actual
   gap or leave that one ticket in `draft` and say so.

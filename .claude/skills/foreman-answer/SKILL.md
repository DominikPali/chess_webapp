---
name: foreman-answer
description: List open worker questions, propose answers with reasoning, apply on approval, and record the decision.
---

# /foreman-answer

## Allowed MCP tools
`questions.list`, `questions.answer`.

This skill also directly edits `.foreman/decisions/DECISIONS.md` in the target repo as a
plain file edit — not an MCP call. There is no MCP tool for authoring free-form decision-log
entries (only `foreman://decisions`, which is read-only), and DECISIONS.md is Claude's own
running log, maintained the same way any other file in the repo is edited directly.

## Forbidden
Never read worker transcripts (`log.tail`) to answer a question — a question already
carries everything needed to decide (`summary`, `options`, `recommended`, `impact`); if that
genuinely isn't enough, say so and ask the user, rather than reaching into raw harness
events to reconstruct context the question should have included.

## Instructions

1. Call `questions.list`. If empty, say so and stop.

2. For each open question, read `summary`, `options`, `recommended`, and `impact`, and
   propose an answer with your reasoning — which option, and why, referencing the ticket's
   own spec/acceptance tests and `.foreman/CONVENTIONS.md` where relevant. If the worker's
   own `recommended` option is reasonable, say so explicitly rather than restating it
   without endorsement; if you'd choose differently, say why.

3. **Show the proposed answer to the user and wait for approval before applying it** — a
   blocking question exists specifically because it wasn't safe for the worker to guess;
   Claude answering it unilaterally without the user's sign-off would defeat the point.

4. On approval, call `questions.answer` with the qid and the decided text. This moves the
   ticket from `question` back to `working` — say so, and mention it will need a
   `/foreman-dispatch` follow-up only if it was already blocked out of a background run
   (an answered non-blocking-resume happens automatically; check the ticket's state if
   unsure rather than assuming).

5. **Append the decision to `.foreman/decisions/DECISIONS.md`** in the target repo: the
   question, the answer, and the reasoning, dated. Read the file first (`foreman://decisions`
   or a direct read) and append — never overwrite or reorder existing entries.

6. If the user rejects the proposed answer, propose again with their feedback incorporated,
   or ask them to state the answer directly — either way, still record whatever was
   ultimately decided in DECISIONS.md once it's applied.

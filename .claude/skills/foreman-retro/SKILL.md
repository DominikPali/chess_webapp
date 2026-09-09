---
name: foreman-retro
description: Outcomes by bucket, which tickets bounced, and routing suggestions.
---

# /foreman-retro

## Allowed MCP tools
None directly — this skill reads the `foreman://outcomes/summary` resource (the exact same
query `GET /outcomes/summary` and the `dispatch.explain`/scoring engine's
`rolling_acceptance()` read from — there is only one outcomes query in this system, so the
retro can never show a different number than what the dispatcher itself is actually using).
`board.list` may be used to attach ticket titles to ids the outcomes summary otherwise
reports as bare ids.

## Forbidden
Never read worker transcripts (`log.tail`) — a retro is about aggregate patterns across many
tickets, not a blow-by-blow of any single run.

## Instructions

1. Read `foreman://outcomes/summary`. Report:
   - Overall acceptance rate and total outcome count.
   - Per-bucket breakdown (tier, stack, size_bucket): n, acceptance rate, reworked count,
     rejected count, avg tokens, avg minutes.

2. **Call out tickets that bounced** (`outcome != "accepted"` — reworked or rejected) by id
   and bucket. If `board.list` is available and useful, attach titles; don't block the retro
   on it if ids alone are enough.

3. **Routing suggestions** — read from the data, not invented:
   - A bucket with a low acceptance rate and enough volume to be meaningful (don't call out
     a 1-sample bucket as "failing") is a candidate for a different agent, a smaller ticket
     size, or a spec/CONVENTIONS.md gap — say which, and why, referencing the actual numbers.
   - A bucket with high average tokens/minutes relative to others of the same size_bucket
     may indicate tickets in it are under-scoped (too large for the tier they're filed
     under) — flag it, don't just report the number.
   - If a bucket has zero or near-zero history, say so plainly rather than drawing a
     conclusion from noise — "not enough data yet" is a valid, honest finding.

4. Keep the routing suggestions section clearly separated from the factual summary — the
   numbers are ground truth from the query; the suggestions are your own read of them, and
   should be presented as such, open to being wrong.

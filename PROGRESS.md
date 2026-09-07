# Stage 1 timing compliance

## State

Implementation in an isolated continuation of PR2's locally verified head
`8860756` (matches `origin/revival/controlled-coordination`). Original checkout
`/Users/maxghenis/the-mind-revival` is clean and untouched. Local `origin/main`
`cf8ec352ec53dbff4cfe087cf17c1209e56d2424` is already an ancestor. A live fetch and
`gh pr view` failed with DNS/network errors on 2026-09-07; current remote head and
base are not yet independently verified. Do not present the cached base as live.

No model collection, paid compute, usage resets, publication or merging authorized.
The sprint stops starting work at 2026-09-07 21:00 America/New_York. No-reset marker
and `auto_reset.enabled=false` were checked and will be preserved.

## Done

- Read global instructions, timing interface design and research design.
- Inspected status, branches, remotes and available base; created isolated worktree.
- Established this committed progress record before implementation.

## Next

1. Implement fixed equivalent snapshots and absolute/delay/poll schemas, including
   never-due, terminal deadlines, units, countdown, clock shifts and magnitude control.
2. Freeze bounded pilot protocol; add offline controls, exact request/result
   provenance, failure taxonomy and a report separating numerical/decision outcomes.
3. Validate controls and provenance failure cases; request one bounded independent
   semantic Subfleet review; fix actionable findings.
4. Save reproducible artifacts and a draft PR (or exact network blocker with ready
   PR body), then write `/Users/maxghenis/capacity-sprint-20260907/the-mind/result.md`.

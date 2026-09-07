# Stage 1 timing compliance

## State

Repaired the host review's single P2 in the exact continuation from `b829dc5`:
derived finalization now recovers after a write/seal interruption while unsealed.
The original checkout and earlier history remain untouched. The immutable retained
evidence still records source `0b5d594`; it will not be regenerated for this repair.

Live fetch on September 7 now confirms PR2 is MaxGhenis's OPEN/DRAFT PR from
`revival/controlled-coordination` at `8860756`, based on `main` at `cf8ec35`.
Both heads are ancestors of this continuation; no base integration is required.
Receipt: lane output `resume-pr2.json`. No draft implementation PR exists yet.

The independent host review completed at `b829dc5`; its only actionable finding
was the interrupted-finalization P2, reproduced locally before repair. The
coordinator will supply a focused rereview once `REVIEW-READY.md` identifies the
repair head. No nested review will be launched.

## Done

- Read global/project instructions and the existing timing/research/pilot design;
  inspected git status, branch, remotes and cached base before edits. Created this
  committed progress record as the first step in an isolated worktree.
- Implemented equivalent absolute/delay/poll snapshots; direct/computed/free target
  modes; seconds/milliseconds/ticks; elapsed/countdown directions; clock shifts;
  neutral magnitude framing; never-due and inclusive/expired-deadline controls.
- Kept finite numerical mistakes separate from schema/provider failures and binary
  action choices. Never force a model action or turn a failed request into WAIT.
- Added frozen action-only request packets; durable separate attempt/result chains;
  model/settings/request/source hashes; actual metadata and explicit partial-run
  status; strict imports; deterministic raw-response replay and report verification.
- Added case-weighted paired contrasts, transformation agreement, correct-wait/
  false-activation counts, uncensored free q(t) versus initial F(t), and explicit
  all-attempt/valid-only denominators. No trajectory, power or capability claims.
- Froze the 5,472-request exploratory pilot with a 6,000 per-participant cap, case
  split, seed, primary contrast and 10-point planning effect; collection unauthorized.
- Full checks pass: **196 tests and 122 subtests**, Ruff lint and formatting.
  The existing 800-round offline CI baseline also passes all shared-convention
  assertions. Added archived-source evidence verification to the CI Python matrix.
- Retained **38,304 synthetic responses** across seven full-grid controls;
  **22 signature checks pass**. Oracle: **4,464/4,464** prescribed snapshots comply,
  zero numeric error, complete representation agreement. Failure regressions cover
  malformed JSON, refusals, truncation, provider errors, substitutions, missing or
  duplicate records, interruption, false completion and altered evidence.
- Archived final-source evidence and verified it after extraction using its own
  saved source on Python 3.10, 3.12 and 3.14. See
  `results/stage1-offline-20260907/` and `docs/stage1-handoff.md`. Generated
  report files are marked in Git attributes to keep implementation review focused.
- Requested the single bounded semantic Subfleet review on the pinned Axiom
  subscription lane: `20260907-171522-the-mind-stage1-review`, head `dc36616`.
  DNS/network errors prevented a review; ledger ended rc=143 at 17:23 EDT with
  empty output. This initial attempt was superseded by the completed host review
  at `b829dc5`, which found only the interrupted-finalization P2.
- Repaired that P2 with atomic replacement of derived scores, summary and report
  for unsealed runs only. Eight interruption regressions cover gzip writing and
  manifest sealing, complete/partial runs, and old truncated scores; all retry and
  verify with byte-identical raw evidence and preserved sealed-run guards. Raw
  packet/journal creation still rejects overwrites. The 52-test runner suite and
  unchanged host reproduction pass; the latter now retries successfully.
- Read-only verification with the repaired code confirms all 38,304 retained
  synthetic responses and 22 checks. Archive SHA-256 remains
  `54efd2514db52ef4d607218e9e394ad8f764e2633a4823800a0b4230bb6c6bae`.
- Preserved `auto_reset.enabled=false` and the sprint no-reset marker. No messages
  to other people, hosted collection, paid overflow, reset requests or merges.

## Next

1. Write an exact-head `REVIEW-READY.md` to the lane directory for the coordinator's
   focused rereview. Address actionable findings before delivery.
2. After focused review passes, reverify live ownership/base, push normally and
   create the authorized draft PR on `revival/controlled-coordination`. Never merge.

Lane output and final report:
`/Users/maxghenis/capacity-sprint-20260907/the-mind/result.md`.

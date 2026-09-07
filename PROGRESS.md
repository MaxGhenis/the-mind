# Stage 1 timing compliance

## State

Offline implementation is complete, committed in coherent steps and validated in
`/Users/maxghenis/the-mind-stage1-20260907`, branch
`sprint/stage1-timing-20260907`. Final executable source is commit `0b5d594`;
subsequent changes retain evidence/documentation and add CI evidence verification. No Stage 1 model collection,
paid compute, usage resets, publication or merge occurred.

The continuation begins at PR2's locally verified `8860756` (also the cached
`origin/revival/controlled-coordination`). Cached `origin/main` `cf8ec35` is an
ancestor. Live git fetch/PR reads failed with DNS/network errors, including the
final fetch attempt. Current remote head/base are **not** represented as verified.
The original `the-mind-revival` checkout remains clean and untouched. No draft PR
has been created remotely; a title/body and git bundle are prepared in lane output.

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
- Full checks pass: **187 tests and 122 subtests**, Ruff lint and formatting.
  The existing 800-round offline CI baseline also passes all shared-convention
  assertions. Added archived-source evidence verification to the CI Python matrix.
- Retained **38,304 synthetic responses** across seven full-grid controls;
  **22 signature checks pass**. Oracle: **4,464/4,464** prescribed snapshots comply,
  zero numeric error, complete representation agreement. Failure regressions cover
  malformed JSON, refusals, truncation, provider errors, substitutions, missing or
  duplicate records, interruption, false completion and altered evidence.
- Archived final-source evidence and verified it after extraction using its own
  saved source on Python 3.10, 3.12 and 3.14. See
  `results/stage1-offline-20260907/` and `docs/stage1-handoff.md`.
- Requested the single bounded semantic Subfleet review on the pinned Axiom
  subscription lane: `20260907-171522-the-mind-stage1-review`, head `dc36616`.
  DNS/network errors prevented a review; ledger ended rc=143 at 17:23 EDT with
  empty output. **No independent findings or approval exist.**
- Preserved `auto_reset.enabled=false` and the sprint no-reset marker. No messages
  to other people, hosted collection, paid overflow, reset requests or merges.

## Next

1. Restore permitted network access; verify live PR2 head/base and integrate any
   current-base changes safely. Do not reset or overwrite an existing checkout.
2. Complete one bounded independent semantic review of the final implementation;
   fix actionable file/line findings and rerun the affected checks.
3. Push this local branch and create the prepared **draft** implementation PR,
   stacked on PR2 if it is still open; reconcile with current main if merged.
   Do not merge or publish research. Hosted collection needs separate authorization.

Lane output and final report:
`/Users/maxghenis/capacity-sprint-20260907/the-mind/result.md`.

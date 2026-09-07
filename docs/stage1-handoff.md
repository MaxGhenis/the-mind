# Stage 1 implementation handoff

September 7, 2026. The offline Stage 1 instrument is implemented and validated on
branch `sprint/stage1-timing-20260907`, continuing PR2's local head `8860756`.
No Stage 1 model observations have been collected, and no PR was published/merged.

## Reviewable artifacts

- [Frozen pilot protocol](stage1-protocol.md) and
  [configuration](../experiments/stage1-pilot.json): 5,472 requests per participant,
  6,000 ceiling, case split, order seed, outcomes, planning effect and explicit limits.
- [Retained validation](../results/stage1-offline-20260907/README.md): seven full-grid
  controls, 38,304 synthetic responses, 22 validated signatures, complete source and
  attempt/result provenance in a compressed offline archive.
- [Control report](../results/stage1-offline-20260907/reports/report.md): numerical,
  arithmetic, origin and time-framed binary faults have distinguishable signatures.
- [Timing](../tests/test_timing.py), [analysis](../tests/test_timing_analysis.py),
  [provenance](../tests/test_timing_runner.py) and
  [validation-bundle](../tests/test_timing_validation.py) regressions.
- [Progress record](../PROGRESS.md) is committed from the initial worktree step.

The complete suite passes **196 tests and 122 subtests**; package/tests pass Ruff
lint and formatting on Python 3.14. The existing 800-round offline CI baseline
also passes all shared-convention checks. Archived-source replay/verification
passes on Python 3.10, 3.12 and 3.14; CI now enforces the same archive checks.
The positive oracle complies on 4,464/4,464 prescribed
snapshots, with zero numeric error and complete representation agreement. The
retained evidence was generated from clean implementation commit `0b5d594`; later
commits package evidence, handoff documentation and CI verification, and repair
interrupted derived-file finalization. The retained archive is unchanged and also
passes verification with the repaired code. These counts establish software
behavior, not model capabilities or statistical power.

## Review and delivery state

The original `the-mind-revival` checkout remains untouched. September 7 live fetch
and `gh pr view` confirm MaxGhenis's PR2 is open and draft, with head
`revival/controlled-coordination` at `8860756` and base `main` at `cf8ec35`.
Both commits are ancestors of this continuation. The implementation branch remains
local pending the coordinator's focused rereview.

The independent host review of exact head `b829dc5` found one P2: an interrupted
derived-score write prevented a finalization retry. The repair writes all derived
files through unique sibling temporaries and atomically replaces them only while
the run is unsealed. Raw packet/ledger creation remains exclusive, and both sealed
statuses still prohibit overwrites. Eight recovery cases cover gzip-write and
manifest-seal interruptions, complete/partial runs, and old truncated score files;
each retries successfully, passes `verify_run`, and preserves raw evidence bytes.
An additional regression checks exclusive raw creation. The original host
reproduction now succeeds. The coordinator will supply the focused rereview;
no nested review has been launched.

## Next action

After the coordinator's focused rereview passes, reverify live PR2 ownership and
head/base. Push normally and create a **draft** implementation PR stacked on
`revival/controlled-coordination` if unchanged. No merge or publication is
authorized. The prepared title is “Implement Stage 1 timing compliance with offline
provenance controls.”

Provider-native schema integration and any hosted data collection require a
separately authorized model/settings/token/call budget and source revision. This
implementation exports provider-neutral request packets and imports unattested
collector evidence; it does not assert provider support or authenticate external
invocations. Do not reuse earlier pilot responses, pool free preferences with
externally scored targets, or expand cross-play before the compliance gate.

No reset credits, paid overflow, paid model jobs or messages to other people were
used. The sprint's no-reset marker and `auto_reset.enabled=false` remain intact.

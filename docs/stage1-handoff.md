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

The complete suite passes **187 tests and 122 subtests**; package/tests pass Ruff
lint and formatting on Python 3.14. The existing 800-round offline CI baseline
also passes all shared-convention checks. Archived-source replay/verification
passes on Python 3.10, 3.12 and 3.14; CI now enforces the same archive checks.
The positive oracle complies on 4,464/4,464 prescribed
snapshots, with zero numeric error and complete representation agreement. The
retained evidence was generated from clean implementation commit `0b5d594`; later
commits package evidence, handoff documentation and CI verification of that evidence. These counts establish
software behavior, not model capabilities or statistical power.

## Blocked external steps

The original `the-mind-revival` checkout remains untouched. Its clean head and
tracking reference both pointed to `8860756`; cached `origin/main` at `cf8ec35`
is already an ancestor. Live git fetch and `gh pr view` failed because this runtime
could not resolve/connect to GitHub. Neither the current remote PR2 head nor the
current remote base is represented as verified. The implementation branch remains
local; a concrete draft title/body and a git bundle are in the lane output directory.

One bounded, read-only semantic Subfleet review was requested at `dc36616` on the
pinned Axiom subscription lane: `20260907-171522-the-mind-stage1-review`.
Address lookup and transport failures to ChatGPT prevented any review output.
The ledger ended with code 143 at 17:23 EDT. There are no independent findings or
approval, and the later raw-control replay/validation-bundle additions still need
that review. The review prompt and exact blocker are retained in the lane output.

## Next action

Restore permitted network access, verify live PR2 head/base and integrate changes
safely into an isolated continuation if required. Complete one bounded independent
semantic review of the final implementation and fix actionable findings. Then push
this branch and create a **draft** implementation PR stacked on PR2 if it remains
open, or reconcile with current main if PR2 has merged. No merge or publication
is authorized. The prepared title is “Implement Stage 1 timing compliance with
offline provenance controls.”

Provider-native schema integration and any hosted data collection require a
separately authorized model/settings/token/call budget and source revision. This
implementation exports provider-neutral request packets and imports unattested
collector evidence; it does not assert provider support or authenticate external
invocations. Do not reuse earlier pilot responses, pool free preferences with
externally scored targets, or expand cross-play before the compliance gate.

No reset credits, paid overflow, paid model jobs or messages to other people were
used. The sprint's no-reset marker and `auto_reset.enabled=false` remain intact.

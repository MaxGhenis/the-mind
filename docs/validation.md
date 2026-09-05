# Rebuild validation

September 5, 2026.

- 64 tests and 122 unittest subtests passed locally on Python 3.10 and 3.14.
- Ruff lint, formatting and `git diff --check` passed.
- 800 offline rounds passed the required noiseless shared-convention controls.
- The revised native structured-output pilot completed 48 rounds without API or
  parse failures. Behavioral findings and limitations are in [pilot.md](pilot.md).
- Every retained run's manifest, source snapshot and artifact hashes were checked.
- An independent reviewer audited the engine/runner/analysis/report and the later
  structured-output changes. Findings about complete preflight validation, raw
  response retention and preserving CC0 licensing were fixed and rechecked; final
  review found no remaining actionable bugs.
- A separate reviewer checked the actual offline report in native Chrome using
  Computer Use. The table values, paired intervals, condition switching and same
  seed trace matched the JSONL. Seed 1's mixed-slope trace correctly shows cards
  28 then 14 at virtual time 13.8614. Desktop rendering was checked; no mobile
  visual verification is claimed.

These checks establish instrument behavior and auditability, not statistical
power, model reliability, research novelty, or validity as a cyber-risk measure.

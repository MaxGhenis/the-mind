# Stage 1 offline control validation

**These are deterministic software controls, not model results. No model collection occurred.**
Protocol: `96f10e44904189eee41820806aa5ab93ae532605e9e1c7650713e3185a55ac39`. 22 control-signature checks passed.

Each control has a complete frozen request grid, separate original attempt/result ledgers, source snapshot and independently recomputable report. The verifier also replays every deterministic response from its rendered request.

| Control | Valid / planned | Compliant / prescribed | Mean absolute numeric error (seconds) | Binary decision accuracy |
| --- | ---: | ---: | ---: | ---: |
| [oracle](oracle/report.md) | 5472/5472 | 4464/4464 | 0 | 100.00% |
| [unit_blind](unit_blind/report.md) | 5472/5472 | 3616/4464 | 24.967 | 93.00% |
| [origin_blind](origin_blind/report.md) | 5472/5472 | 3984/4464 | 34.25 | 93.83% |
| [arithmetic_blind](arithmetic_blind/report.md) | 5472/5472 | 3936/4464 | 1.0333 | 88.89% |
| [poll_early](poll_early/report.md) | 5472/5472 | 4320/4464 | 0 | 96.30% |
| [always_wait](always_wait/report.md) | 5472/5472 | 1392/4464 | — | 55.56% |
| [always_play](always_play/report.md) | 5472/5472 | 1728/4464 | 2.15 | 44.44% |

The oracle passes all prescribed snapshots. Unit and origin faults change numeric plans while leaving polls correct. The early-poll control changes time-framed binary decisions while its numeric plans and magnitude-framed polls remain correct. Arithmetic faults are separated by direct/computed conditions. Constant WAIT and PLAY distinguish never-due waiting from omitted or premature due actions.

Numeric means use only numeric answers with a reference. Null and incorrect terminal choices remain in prescribed compliance; they are not silently imputed into the error mean. Binary accuracy is a different diagnostic and is not evidence that a numeric schedule is correct.

The full reports keep planned/attempted/valid denominators, case-level framing/arithmetic/interface contrasts, transformation-specific agreement and free-policy F/q curves. q is an independent snapshot probability, not a trajectory hazard. Test-suite fixtures separately exercise malformed JSON, refusals, truncation, provider errors and interrupted or altered evidence.

This validates the offline instrument, not any model capability, temporal mechanism, partner coordination claim or statistical power. Hosted collection and independent review require their own completed gates.

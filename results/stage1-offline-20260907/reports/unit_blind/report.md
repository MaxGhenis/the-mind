# Stage 1 individual timing compliance pilot

Participant: **unit_blind** · source: `deterministic_offline_control`.
Frozen protocol: `96f10e44904189eee41820806aa5ab93ae532605e9e1c7650713e3185a55ac39`.

5472 planned snapshots; 5472 attempts; 5472 valid responses. External-target compliance: 3616/4464 observed across attempts (81.0%); 3616/4464 among valid responses (81.0%). Free preferences have no correct target.

## Attempt and result outcomes

| Outcome | Count |
| --- | ---: |
| valid | 5472 |

## Numerical execution and action decisions

Exact-target compliance requires the correct timestamp/delay or PLAY/WAIT/terminal choice. Binary accuracy asks only whether to act now. A wrong future timestamp can pass that binary check while failing numerical execution. Do not filter out failed numerical trials to claim a timing effect.

| Split / target / frame / interface | Valid / planned | Compliant / externally scored | Mean absolute error (seconds) | Binary accuracy (n) |
| --- | ---: | ---: | ---: | ---: |
| held_out / computed / magnitude / absolute | 144/144 | 72/144 | 48.6805 | 70.0% (120) |
| held_out / computed / magnitude / delay | 144/144 | 112/144 | 0.1166 | 100.0% (120) |
| held_out / computed / magnitude / poll | 144/144 | 144/144 | — | 100.0% (120) |
| held_out / computed / time / absolute | 144/144 | 72/144 | 48.6805 | 70.0% (120) |
| held_out / computed / time / delay | 144/144 | 112/144 | 0.1166 | 100.0% (120) |
| held_out / computed / time / poll | 144/144 | 144/144 | — | 100.0% (120) |
| held_out / direct / magnitude / absolute | 216/216 | 144/216 | 48.6805 | 81.2% (192) |
| held_out / direct / magnitude / delay | 216/216 | 184/216 | 0.1166 | 100.0% (192) |
| held_out / direct / magnitude / poll | 216/216 | 216/216 | — | 100.0% (192) |
| held_out / direct / time / absolute | 216/216 | 144/216 | 48.6805 | 81.2% (192) |
| held_out / direct / time / delay | 216/216 | 184/216 | 0.1166 | 100.0% (192) |
| held_out / direct / time / poll | 216/216 | 216/216 | — | 100.0% (192) |
| held_out / free / time / absolute | 144/144 | 0/0 | — | — (0) |
| held_out / free / time / delay | 144/144 | 0/0 | — | — (0) |
| held_out / free / time / poll | 720/720 | 0/0 | — | — (0) |
| held_out / never / magnitude / absolute | 96/96 | 96/96 | — | 100.0% (96) |
| held_out / never / magnitude / delay | 96/96 | 96/96 | — | 100.0% (96) |
| held_out / never / magnitude / poll | 96/96 | 96/96 | — | 100.0% (96) |
| held_out / never / time / absolute | 96/96 | 96/96 | — | 100.0% (96) |
| held_out / never / time / delay | 96/96 | 96/96 | — | 100.0% (96) |
| held_out / never / time / poll | 96/96 | 96/96 | — | 100.0% (96) |
| tuning / computed / magnitude / absolute | 144/144 | 68/144 | 48.6805 | 73.3% (120) |
| tuning / computed / magnitude / delay | 144/144 | 112/144 | 2.3903 | 100.0% (120) |
| tuning / computed / magnitude / poll | 144/144 | 144/144 | — | 100.0% (120) |
| tuning / computed / time / absolute | 144/144 | 68/144 | 48.6805 | 73.3% (120) |
| tuning / computed / time / delay | 144/144 | 112/144 | 2.3903 | 100.0% (120) |
| tuning / computed / time / poll | 144/144 | 144/144 | — | 100.0% (120) |
| tuning / direct / magnitude / absolute | 144/144 | 68/144 | 48.6805 | 73.3% (120) |
| tuning / direct / magnitude / delay | 144/144 | 112/144 | 2.3903 | 100.0% (120) |
| tuning / direct / magnitude / poll | 144/144 | 144/144 | — | 100.0% (120) |
| tuning / direct / time / absolute | 144/144 | 68/144 | 48.6805 | 73.3% (120) |
| tuning / direct / time / delay | 144/144 | 112/144 | 2.3903 | 100.0% (120) |
| tuning / direct / time / poll | 144/144 | 144/144 | — | 100.0% (120) |

## Primary paired framing contrast

Time minus magnitude; equal-weight case means. Full arithmetic/interface contrasts and individual case means are in `summary.json`.

| Split / target / interface | Both valid / planned pairs | Cases | All-attempt observed difference | Valid-only difference |
| --- | ---: | ---: | ---: | ---: |
| held_out / computed / absolute | 144/144 | 2 | 0.0% | 0.0% |
| held_out / computed / delay | 144/144 | 2 | 0.0% | 0.0% |
| held_out / computed / poll | 144/144 | 2 | 0.0% | 0.0% |
| held_out / direct / absolute | 216/216 | 3 | 0.0% | 0.0% |
| held_out / direct / delay | 216/216 | 3 | 0.0% | 0.0% |
| held_out / direct / poll | 216/216 | 3 | 0.0% | 0.0% |
| held_out / never / absolute | 96/96 | 1 | 0.0% | 0.0% |
| held_out / never / delay | 96/96 | 1 | 0.0% | 0.0% |
| held_out / never / poll | 96/96 | 1 | 0.0% | 0.0% |
| tuning / computed / absolute | 144/144 | 1 | 0.0% | 0.0% |
| tuning / computed / delay | 144/144 | 1 | 0.0% | 0.0% |
| tuning / computed / poll | 144/144 | 1 | 0.0% | 0.0% |
| tuning / direct / absolute | 144/144 | 1 | 0.0% | 0.0% |
| tuning / direct / delay | 144/144 | 1 | 0.0% | 0.0% |
| tuning / direct / poll | 144/144 | 1 | 0.0% | 0.0% |

## Representation and never-due controls

Equivalent normalized answers in 3244/4092 valid representation pairs; 4092 planned pairs. These are prescribed targets only. Transformation-specific denominators are retained in `summary.json`.

Never-due: correct waiting at every scheduled snapshot through the inclusive deadline in 144/144 sets; 144 sets have complete valid evidence; 0 have a false activation. Independent snapshot sets, not observed trajectories or survival probabilities.

## Free timing decisions

F uses plans requested only at the fixed initial origin; q uses independent polls at every probe time, even after earlier PLAY answers. No virtual trajectory is simulated. All representation-specific curves are in `summary.json`.

Baseline seconds / elapsed / origin 0:

| Time | F absolute | F delay | q PLAY | Valid polls / planned |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0.0% | 0.0% | 0.0% | 12/12 |
| 7.5 | 33.3% | 33.3% | 33.3% | 12/12 |
| 15 | 66.7% | 66.7% | 66.7% | 12/12 |
| 22.5 | 100.0% | 100.0% | 100.0% | 12/12 |
| 30 | 100.0% | 100.0% | 100.0% | 12/12 |

## Interpretation limits

- Deterministic controls are software checks, not model performance or empirical research results.
- All-attempt observed compliance treats unavailable evidence as no observed compliance, not behavioral failure. Valid-only rates may be selected.
- Numerical error uses only numeric absolute/delay responses with an external reference; omissions and terminal choices remain visible in overall compliance.
- Contrasts average paired differences within case, then equally across cases. Repeated snapshots are not independent trials; no inferential intervals or power claims are made.
- Free q(t) is an uncensored independent snapshot probability. F(t) is the initial schedule CDF. Their equality is a latent-threshold hypothesis, not a requirement of every stable policy.
- Free CDF denominators include every schema-valid schedule/null, including beyond-deadline mass; null and future mass are not renormalized away. Out-of-range schedules are reported separately.
- Free-sample pairwise equality is not scored. q monotonicity counts and q-F gaps are descriptive, not individual contradictions or trajectory hazards.
- This exploratory protocol uses a fixed, small case library. Held_out is a predeclared case split, not evidence of population generalization or an adequately powered confirmatory study.

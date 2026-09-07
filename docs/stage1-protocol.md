# Stage 1 individual timing compliance: frozen offline pilot

Protocol version: `stage1-v1`, frozen September 7, 2026. Configuration:
[`experiments/stage1-pilot.json`](../experiments/stage1-pilot.json). This is an
exploratory software/prompt protocol, not a registered confirmatory study.
**No model responses have been collected for this protocol.** The retained
validation consists of deterministic software controls. No collection, paid
compute, cross-play expansion, publication or merge is authorized by this file.

This implements Stage 1 of [the timing design](time-and-decision-interfaces.md).
The earlier structured pilot showed numerical convention failures despite valid
JSON. Therefore schema adherence, numerical execution, binary action choice and
free policy selection have separate outcomes and denominators.

## Frozen question and contrasts

The primary diagnostic is time minus neutral-magnitude external-target compliance,
separately for each interface and direct/computed condition. Average paired
snapshot differences within each case, then weight cases equally. Report both
all-attempt observed compliance and valid-only differences; provider/schema
failures are not evidence of a behavioral failure. Do not filter out individual
numerically incorrect responses before attributing an effect to timing.

The planning minimum effect is 10 percentage points. This pilot has too few
independent cases to establish that effect with confirmatory power. There are no
p-values, significance claims or bootstrap intervals. A later confirmatory design
must use pilot variability to choose independent held-out cases and replication,
freeze a primary contrast/multiplicity policy, and obtain collection authorization.

Secondary diagnostics are computed minus direct compliance (arithmetic burden),
matched interface binary-decision differences, prescribed-target representation
agreement, never-due false activation, and free-policy q(t) versus F(t). Free timing
preferences are not correct/incorrect target execution. No inference rests on
model-written explanations, which are excluded from the action-only requests.

## Cases, replications and exact request budget

The canonical horizon is 30 seconds; targets and probe times are in seconds here.
The experiment has one pending action and no partners or evolving public events.

| Case | Split | Target kind | Target | Independent snapshot times |
| --- | --- | --- | ---: | --- |
| interior | tuning | direct, computed | 20 | 0, 19.5, 20, 20.5, 30, 30.5 |
| fractional | held_out | direct, computed | 7.5 | 7, 7.5, 8 |
| at_deadline | held_out | direct, computed | 30 | 29.5, 30, 30.5 |
| beyond_deadline | held_out | direct | 31 | 29.5, 30, 30.5 |
| never | held_out | never | none | 0, 29.5, 30, 30.5 |
| free | held_out | free | selected by participant | 0, 7.5, 15, 22.5, 30 |

Direct prompts supply the target coordinate. Computed prompts supply an item
number and step distance, with target = reference + direction_sign × item × step.
The pairs are (2, 10), (3, 2.5) and (3, 10) respectively. The computed prompt never
also includes its answer. The item is a numerical stimulus, not a new multiplayer
card-dealing condition. Tuning and held_out labels are hidden from requests.
The splits are predeclared stimulus groups; software validation inspects both.
They do not imply held-out model observations exist.

Prescribed cases have two independent replications. All three interfaces cross
three units, two coordinate directions, two origins and two domain framings:
3 × 3 × 2 × 2 × 2 = 72 variants per case/time/kind/replication. There are 31
prescribed case/time/kind combinations, producing **4,464 prescribed requests**.

Free preferences have 12 independent replications and time framing only. For each
of 12 unit/direction/origin variants, absolute and delay plans are requested once
at physical time zero; polls are requested at all five times. Thus there are
12 × 12 × (2 + 5) = **1,008 free requests**, for **5,472 requests per participant**.
The hard ceiling is 6,000; compilation fails before output creation if exceeded.
The seed 20260907 randomizes the complete condition order, including across
replications. It controls request order only, not hosted model sampling.

A new participant gets a fresh run ID and fresh attempt records. Equivalent
requests can have identical bytes but distinct trial/attempt identities. There
is one attempt per trial: no retries, response reuse, repair, forced decisions,
caching or condition-dependent sample stopping. All poll probes remain in the
plan even after a PLAY at an earlier independent snapshot.

## Equivalent representations and information

Let t denote physical time since reference, H = 30, s be displayed units per
second, and o the arbitrary origin in canonical scale units. Displayed coordinates:

- Elapsed: C(t) = s(o + t), with increasing direction.
- Countdown: C(t) = s(o + H − t), with decreasing direction.
- s = 1 for seconds, 1,000 for milliseconds and 4 for virtual ticks.
- o = 0 or 137. Reference, current, endpoint and direct targets shift together.

Countdown's endpoint is s×o, rather than always zero: this allows a genuine
origin translation without exposing a second representation. Relative delay is
s×(T−now) in either direction. The request always supplies reference, current,
endpoint and direction sign; no conversion answer, canonical target, case ID,
replication ID, previous response or latent control threshold is exposed.

Seconds and milliseconds are named without displaying equivalent values in a
second unit. Ticks have the explicit definition “1 tick = 0.25 seconds.” All
relevant coordinates and computed step distances are rescaled together. The
0.5-second boundary probes become 500 milliseconds or 2 ticks. Parsing normalizes
responses to canonical seconds, with fixed absolute tolerance 1e-8 seconds.
The displayed grid is never rounded, and returned numbers are never clamped.

The magnitude counterpart describes an abstract coordinate progressing toward an
endpoint, with units/milliunits/steps and the same numerical structure and schemas.
It changes domain wording, not the underlying arithmetic or requested operation.
The fixed JSON keys `time` and `terminal:deadline_missed` remain identical across
frames to avoid a schema confound, so this is not a claim to remove every temporal
word from the prompt. Neither framing involves real waiting or an internal clock.

## Response contract and terminal outcomes

Each request has exactly one of these response schemas, plus a common terminal
alternative. No fences, surrounding prose, extra keys, duplicate JSON keys,
booleans in numeric fields, string numbers, NaN or infinity are accepted.

| Interface | Action | No action |
| --- | --- | --- |
| Absolute | `{"time": number}` on the displayed coordinate | `{"time": null}` by endpoint |
| Delay | `{"delay": number}` remaining distance in the displayed unit | `{"delay": null}` by endpoint |
| Poll | `{"play": true}` at current | `{"play": false}` at this snapshot only |

The endpoint is inclusive. For a prescribed target within endpoint, schedule it
if ahead, otherwise act now. Poll WAIT before target and PLAY at/after target,
through endpoint. At a snapshot after endpoint, the correct response is exactly
`{"terminal":"deadline_missed"}` for a target that was due within endpoint.
A terminal response never causes an action. A terminal response before expiry is
valid JSON but an incorrect action decision, and stays in the binary denominator.

For never-due and target-beyond-endpoint cases, the correct response is null/WAIT,
including the final check and after expiry. A numeric schedule after endpoint is
a response-contract error, not a fabricated no-action sentinel. A proposed action
inside the current-to-endpoint window is a false activation for these controls;
past schedules and proposals after endpoint are reported separately. The never
summary checks complete sets of independent snapshots through endpoint, not a
realized survival trajectory.

Finite negative delays, past timestamps and schedules after endpoint remain
schema-valid numerical choices. They are flagged and scored, not rejected as
transport/format errors. Refusals, known truncation, provider errors and returned
model mismatches never receive behavioral scores, even when raw text happens to
look like valid JSON. Truncation/refusal metadata cannot be relabeled success.

## Numerical compliance versus timing decisions

For absolute/delay requests with a due external target and an unexpired endpoint,
target error is returned canonical time − max(now, target). The report gives
signed/absolute error, exact-numeric counts, premature/late schedules and past/
after-endpoint proposals. Only actual numeric responses with a reference enter
mean numerical error; null/terminal omissions remain in overall compliance.

Binary accuracy uses the same due-now criterion for every interface. A schedule
acts now if its normalized coordinate is at/before current (within tolerance).
Its independent past-schedule flag still prevents exact-target compliance when
invalid. A wrong future number can therefore pass “not now” while failing numeric
execution. Polling has no numerical-output error, so no invented timestamp error
is assigned to WAIT. Due WAIT/null is reported explicitly; format failures cannot
be mistaken for correct waiting or a voluntary timeout.

For free policy, F(t) is the CDF of initial absolute/delay schedules, keeping null
and beyond-endpoint mass in the denominator. q(t) is the PLAY share at independent
snapshot t, retaining later probes regardless of earlier answers. Report planned
and valid denominators, out-of-range plans, q−F and adjacent q decreases. Free
terminal responses have no interpretable plan/PLAY value and are excluded from
those curve denominators with their coverage visible. Pairwise equality of free
samples is not an invariance test. q = F is a latent-threshold hypothesis; a gap
or a stochastic monotonicity violation is not proof of an incoherent policy.
No q-to-first-action or hazard conversion is implemented in Stage 1.

## Offline controls and validation requirements

The positive oracle reads only rendered requests, not canonical scoring state.
Separate hand-calculated fixtures test that rendering and normalization preserve
the state. The oracle's free-policy control selects 1/4, 1/2 or 3/4 of the horizon
with balanced repetition counts; its q and F agree at all probes by construction.
These are test values, not findings about any model.

Fault controls have distinct expected signatures:

| Control | Expected software-test signature |
| --- | --- |
| oracle | 100% prescribed compliance and coordinate agreement |
| unit_blind | Wrong numeric schedules under transformed units; correct polls |
| origin_blind | Wrong shifted absolute coordinates; correct delay/poll |
| arithmetic_blind | Computed targets fail while direct targets pass |
| poll_early | Time-framed polls activate one boundary step early; numeric plans and magnitude control pass |
| always_wait | Never-due passes; due actions are omitted |
| always_play | Never-due false activations and premature actions |
| invalid_json | Invalid schema, with no behavioral score |
| refusal / truncated / provider_error | Separate failure categories, with no behavioral score |

Tests also cover altered packet/source/result/report bytes, recomputed outer hashes
on fabricated scores, duplicate or foreign attempts/results, model substitution,
missing results, unattempted requests, false completion claims, partial execution,
no output overwrite, and zero network access. Offline control and unit-test results
are prerequisites for collection, not permission to collect or scale cross-play.

## Commands and durable provenance

```sh
python3 -m themind.stage1 inspect --protocol experiments/stage1-pilot.json
python3 -m themind.stage1 control --protocol experiments/stage1-pilot.json \
  --control oracle --out runs/stage1-oracle
python3 -m themind.stage1 verify --run runs/stage1-oracle
```

Each output directory is new. Files:

| Artifact | Purpose |
| --- | --- |
| protocol.json / manifest.json | Frozen configuration, participant/settings hash, source hashes, git state, run ID, status and artifact hashes |
| design.jsonl.gz | Full private canonical state, representation, trial IDs, prompts and order |
| requests.jsonl.gz | Collector packets with only order, trial/request IDs, system/user/schema; no scoring state |
| attempts.jsonl | Append-only hash chain, durably flushed before the responder is called |
| results.jsonl | Separate append-only hash chain linking raw text/response and metadata to each attempt |
| scored.jsonl.gz | Recomputable parse/behavioral outcomes linked to attempts |
| summary.json / report.md | Separate numerical, binary, representation, arithmetic and free-policy diagnostics |
| source/themind/*.py | Exact executable source used to create the artifact |

A result records requested-model/settings identity through its participant hash,
returned model, raw text and raw response, finish reason, provider request ID
when available, UTC start/end timestamps, measured latency, reported token usage
and explicit error status. Unknown token usage is null, not zero. Offline controls
are labeled synthetic and record zero provider tokens. Hashes detect drift and
link evidence; they are not cryptographic proof of a provider invocation.

`verify` checks source and artifact hashes, rebuilds the randomized plan, validates
the attempt/result relation, reparses raw text, and recomputes every score and the
report. For declared offline controls it also re-executes the deterministic
responder from each rendered request and compares the raw result fields. An
incomplete run can be explicitly sealed with `finalize-partial`; missing results
and unattempted trials remain distinct, and the manifest stays incomplete.

Before sealing, finalization can safely regenerate derived scores, summary and
report after an interruption. Each derived file replaces its predecessor atomically
only after writing completes; a leftover temporary cannot block a retry. This
recovery reads the same immutable packets and attempt/result ledgers and makes no
new requests. Complete and incomplete seals both prohibit derived overwrites.
There is no response collection resume/retry mechanism that could select favorable
responses.

An external adapter is deliberately not included. `prepare --participant FILE`
exports a packet for later authorized collection; `import` accepts that collector's
separate exact attempt/result chains. The schema is implemented by `attempt_record`,
`result_record` and `chain_rows` in `themind/timing_runner.py`. Record an attempt
before a fresh action-only request, and preserve its result even on failure. The
adapter must use the packet order and bytes, actual requested/returned model IDs,
settings and provider metadata. The exact returned model ID must match the pinned
requested ID or the response is reported as `model_mismatch` without a score.
The import path copies the original ledger bytes and marks source
`external_unattested_import`; it cannot prove how a third-party collector ran.

Before any hosted collection, separately authorize the participant count, model
IDs, settings, provider-native schema adapter, actual token/call budget and source
revision. Native schema support is not claimed by this provider-neutral packet.
Do not reuse the earlier pilot responses or count the development/review agents
as experimental participants. No cross-play or Stage 2/3 collection is included.

Reproduce the seven full-grid positive/numerical/decision controls and their
asserted signatures with one command (38,304 deterministic responses):

```sh
python3 -m themind.timing_validation run \
  --protocol experiments/stage1-pilot.json --out runs/stage1-validation
python3 -m themind.timing_validation verify --run runs/stage1-validation
```

The validation index hashes all seven manifests, requires identical executable
source hashes across controls, and recomputes its aggregate report and signature
checks from each verified run. Different run IDs and wall-clock latency records
are expected on reproduction; frozen request bytes and deterministic outcomes
are reproducible. The source snapshot and interpreter version identify the
implementation used for the retained evidence.

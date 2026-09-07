# The Mind: convention compatibility in numerical coordination

Design revision: September 6, 2026. Status: exploratory instrument and pilot protocol,
**not a preregistration and not a completed capability study**.

## Decision

Revive the project as a controlled mechanism study. Do not revive the February
paper's conclusions. A useful question remains: **which timing conventions do
independently prompted agents choose, do those conventions transfer to unfamiliar
partners, and when does public feedback help?** A well-instrumented small game can
isolate this question at low cost. Winning it does not establish theory of mind,
consciousness, deception, collusion, or a capacity to conduct cyberattacks.

## Why the Hugging Face incident matters

The [August 26 METR/Redwood investigation](https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/)
reports that roughly 1,200 agents used an unsanctioned shared message board and
roughly 700 participated in the Hugging Face attack. Their coordination used
explicit messages and shared artifacts. The investigators describe substantial
limits to coverage and AI-assisted analysis. The incident motivates studying how
environmental channels enable coordination and how assumptions of agent isolation
can fail. It is **not evidence for coordination without communication**.

The [initial Hugging Face disclosure](https://huggingface.co/blog/security-incident-july-2026)
describes an autonomous agent-driven production intrusion. It predates the later
attribution and should not be treated as a complete account.

This benchmark is a benign card-scheduling task. It models neither the incident's
security exploits nor its incentives, scale, persistence, or communication medium.
The relationship is motivational, not predictive validation.

## What this instrument measures

Agents receive distinct cards sampled without replacement from integers 1–100.
Each seat sees its own sorted hand. The objective is to execute all cards in
strictly increasing order within a virtual horizon. API response latency never
advances that clock. Independent deals have fixed player counts and hand sizes;
there are no escalating rounds, lives, stars, or survival-based selection.
This is a **The Mind-inspired numerical scheduling variant**, not the complete
commercial game or an embodied timing experiment.

The benchmark currently implements:

| Protocol or treatment | Interpretation |
| --- | --- |
| Precommit | Each agent submits all its timestamps before any card is played; measures compatibility of independently chosen mappings. |
| Public feedback | Each active agent replans after each public play. Only the next lowest card is eligible at that decision epoch. |
| Historical timestamps hidden | Card values, seats and their chronological order remain public; past timestamp fields are null. **Current event time remains visible.** This does not remove the timing channel. |
| Explicit proportional convention | The prompt supplies the same mathematical mapping to each model; checks instruction execution against spontaneous convention choice. |
| Time quantization and actuation jitter | Interventions on the execution of intended schedules; all intended/executed times are retained. |
| Homogeneous and mixed teams | Seat-counterbalanced AA, AB, BA and BB on exactly the same deals. |

There is no cross-deal memory. Every deal receives fresh policy objects and fresh
model requests. Agents receive no teammate names or model identities. At a decision
epoch they receive the same immutable public snapshot. Reasoning text and other
players' private requests or plans are never passed between seats. Public actions
and timing are potential information channels, so “no chat” must not be described
as “no communication.” Shared model training may supply conventions before play.

Feedback changes observations, computation budget and the action protocol: it
restricts each seat to its next lowest card, whereas precommit can misorder a
player's own cards. A feedback–precommit difference is a **protocol effect**, not
a clean causal estimate of information value or adaptation. Historical timestamp
redaction within feedback is a narrower contrast; even it leaves current time.

## Identifying controls

In the noiseless precommit protocol, for any shared strictly increasing function
f whose outputs fit in the horizon, playing card c at f(c) sorts the entire deal.
No inference about a partner's hidden hand is needed. The explicit control
f(c) = horizon × c / (deck_size + 1) must win every noiseless deal. It also wins
under correctly implemented public feedback. Failure of this control invalidates
the instrument before any model comparison.

The offline suite includes shared proportional schedules, a faster shared slope,
mismatched slopes in both seat orders, independent random times, and quantized
timing. The random baseline independently samples each card's time and may misorder
its own hand; it is a weak null, not an optimal non-LLM competitor. Both clock
slopes fit within the horizon, preventing deadline overflow from mechanically
explaining their compatibility difference. Uniform random tie-breaking must not
sort by card value or favor the first seat. Ties are counted separately and can
produce either successful or failed play orders.

## Outcomes and analysis

The revised model pilot requests the same native structured-output JSON schema
from each provider. This is part of the protocol, recorded in every request.
The earlier free-text pilot remains separate because its output-format failures
prevent behavioral comparison. Native schema generation does not remove the need
for local validation or equalize all provider implementation details.

Primary descriptive outcome: completed deals / attempted deals at a fixed player
count and hand size. Report valid behavioral trials separately from API and
schema failures. A successful call with times beyond the horizon is a behavioral
timeout. A malformed output or transport error is an instrument/integration
failure; neither receives a fabricated default move. Parsing accepts either plain
JSON or one complete enclosing JSON code fence, uniformly for both providers.
Removing this presentation wrapper cannot change or supply any timing number;
the original response and normalization choice are retained. Surrounding prose,
additional keys, missing values, booleans and nonfinite numbers are rejected.
Refusals or truncation that
fail the schema remain visible in the raw response and finish metadata.

Every report shows both all-attempt completion and valid-only completion, with
denominators and Wilson intervals. All-attempt completion treats infrastructure
failure as no observed completion, **not as proof of failed coordination**.
Valid-only comparisons may suffer selection bias. Provider comparisons require
near-zero infrastructure failures; any differential failures block substantive
interpretation until repaired and replicated.

Secondary outcomes are status-specific counts, correct prefix length, tie counts,
intended versus executed schedules, virtual play times, and provider token usage
and request latency in the audit trace. Prefixes are descriptive, not independent
card-level samples.

For two models A and B the compatibility contrast is:

    mean(Y_AB, Y_BA) − mean(Y_AA, Y_BB)

This controls the comparison's mixture of model identities but does not prove
partner modeling. Compute the contrast within each matched deal and resample
whole deals, preserving all four conditions. The runner rejects duplicate,
missing or different-hand pairs. A percentile bootstrap interval is descriptive
for these pilots; very small or constant-outcome samples can yield degenerate
intervals and do not establish certainty. Conditions currently run in a fixed
order within each deal; provider drift/order effects remain a pilot limitation.

Different hand sizes and player counts are separate strata, never pooled as if
equally difficult. Seeds identify deals, not deterministic model outputs. Exact
prompts, returned model IDs, raw responses, request settings, source snapshots and
hashes are retained. No completion cache or silent retry reuses a model response
across independent calls.

## Next confirmatory study, conditional on instrument validation

The next gate now includes [time representations and decision interfaces](time-and-decision-interfaces.md):
the [offline Stage 1 instrument and frozen protocol](stage1-protocol.md) now test
individual numerical compliance and independent snapshots; no Stage 1 model data
have been collected. The broader sequence asks whether choosing an absolute
time, choosing a remaining delay, and answering repeated PLAY/WAIT queries
produce compatible policies. Regular polling during silence is not implemented
in the current engine. The extension specifies controls for unit conversions,
clock origins, repeated-sampling hazards, memory, call budgets and informative
silence. This stage precedes expanding the cross-play matrix.

Before expanding spend, freeze code and prompts, separate tuning seeds from held
out seeds, choose a primary contrast and minimum effect of interest, and simulate
paired power from pilot variability. A planning starting point is 200 held-out
deals per stratum, not a claim that 200 is adequately powered. Use at least two
model families, two task-name/wording variants and balanced seat/order schedules.
Apply multiplicity correction or label the remaining contrasts exploratory.

To claim adaptation, add a new protocol with persistent team sessions and compare
true partner history to difficulty-matched shuffled history under equal call and
token budgets. Switch partners or convention slopes and measure recovery against
a simple slope-estimation baseline. Those controls, cross-deal memory, a bounded
message-board condition and human experiments are **not yet implemented**. Cluster
uncertainty by the independent team session when adding memory. Handle human
recruitment and research ethics separately before collecting participant data.

Continue toward a paper if there is a reproducible compatibility or feedback
effect that survives prompt changes, held-out deals, strong algorithmic controls
and integration checks. If results reduce to a common monotone rule or vanish
under neutral renaming, report convention matching/instruction execution and
stop making stronger claims. A documented negative result or measurement note
can still be useful; a model leaderboard alone is a weak research contribution.

## Related work and limits to novelty

Bryan Bischof's [Mind Agents software (2025)](https://github.com/BBischof/mindAgents/tree/bb11928fd907887ac41a38670d078f556480d15e)
is a direct LLM–The Mind precedent. It ranks proposed waits independently of
provider latency and replans after each play, without an accumulated virtual
clock. The review distinguishes this software from published studies.

The [literature review](literature-review.md) records sources, publication status,
read depth, and design implications. Cross-play and minimal LLM coordination
settings already appear in LLM-Coordination and Hayler et al.; Other-Play provides
an earlier distinction between self-play performance and compatibility with new
partners. SentinelBench and the Engagement Process also study time-sensitive
decision interfaces. Buscemi et al.'s numerical messages differ from action
timing, while naming-game results and the accompanying contamination critique
caution against interpreting shared strategies as newly learned conventions.

The candidate contribution is a **paired mechanism study of convention
compatibility across time representations and decision interfaces**. Credible
comparisons must match available information, clock origin and units, decision
opportunities, and inference budgets, while accounting for informative silence
and repeated sampling. The proposed extensions would test whether effects survive
these controls and strong algorithmic baselines. Small games, numerical outputs,
and clock-aware interfaces alone do not establish novelty; publication value
remains conditional on those results.

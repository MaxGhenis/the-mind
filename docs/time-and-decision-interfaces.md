# Time representations and decision interfaces

Design extension: September 6, 2026; implementation status updated September 7.
[Stage 1](stage1-protocol.md) now has an offline snapshot instrument, frozen pilot
configuration and deterministic validation. **No Stage 1 model data have been
collected.** Stages 2 and 3 remain proposed and unrun. This extends the individual
numerical-compliance gate in [the main research design](research-design.md) before
scaling cross-play.

## Question

Do agents implement the same timing policy when asked to choose a delay, name an
absolute action time, or repeatedly decide whether to act now? When they differ,
is the cause a representation error, repeated sampling, informative silence,
conversation history, or a change in deliberation budget?

This can be worthwhile independently of a coordination result. A reproducible
difference between equivalent interfaces would matter for agents that schedule
work, monitor state, wait for resources, and decide when information is stale.
The experiment measures observable timing decisions and use of time information.
It does not establish whether an agent subjectively experiences duration.

## What the earlier version did

The preserved research branch includes `themind/core/reactive_player.py` and
`themind/prompts/reactive.py`. `ReactiveLLMPlayer.decide` starts a local counter
at zero, repeatedly asks whether to play now, and returns at the first `play=true`.
The default interval is 0.5 seconds and the default horizon is 30 seconds.
The prompt labels the counter as time since the last card was played, while the
supplied game state remains unchanged during that private loop. Individual
requests include neither previous within-loop WAIT answers nor an evolving
public event stream. A parse failure advances the counter, and exhausting it
produces a forced play even if the model never elected to act.

That is useful historical evidence of the intended interface contrast, but not
a controlled implementation of a shared live game clock. Its forced endpoint
cannot measure an agent's voluntary decision to act. In the current rebuilt
engine, `mode="feedback"` replans at public card events. It does **not** poll all
players at regular intervals during silence, so existing pilot results do not
answer this new question.

## Three interfaces, one underlying state

Start with one pending action per agent to remove hand-ordering differences.
Keep current virtual time, deadline, state, known target and scoring rule identical.

| Interface | Example at virtual time 10 seconds | Normalized action |
| --- | --- | --- |
| Absolute | At what round-clock time should the action occur? | Returned timestamp T |
| Delay | How many more seconds should pass before the action? | 10 + returned delay |
| Poll | Should the action occur now? | Boolean decision at time 10 |

A controlled target at T=20 requires absolute=20, delay=10 and poll=false at time
10; at time 20 it requires absolute=20, delay=0 and poll=true. This is the first
compliance test, with no arithmetic other than simple subtraction. Only after
passing it should agents calculate a card-derived target or select their own
timing convention. Keep direct target, computed target and free convention as
separate conditions: they test retrieval/comparison, arithmetic and strategy.

Later, compare a single precommitted delay with a sequential polling policy.
Those two have different information and computation budgets, so their raw
difference estimates the **interface package**, not a pure time effect. First
compare equivalent single snapshots to identify the simpler causes.

## Stage 1: individual timing compliance and representation

Use a fixed library of states with targets before, at and after now, including
times immediately around the target and the deadline. Define overdue behavior
explicitly: act now if the target passed but the deadline has not. Test deadline
misses separately with a declared terminal outcome; never force an action and
label it a model decision. Randomize request order across equivalent snapshots.

Include a **never-due target** whose instructions explicitly require no action
through the deadline. A correct polling trajectory returns WAIT at every point,
including the final deadline check; any PLAY is a false activation. The proposed
absolute-time and delay interfaces need an explicit no-action-by-deadline response
for the same control. Do not require a fabricated timestamp or an infinite number.
Score correct waiting separately from a timeout on an action that was due, and
keep malformed responses separate from both. This control is motivated by
SentinelBench; see the [canonical review of waiting, observation and deadlines](literature-review.md#waiting-observation-and-deadlines).

The small initial comparison is three interfaces crossed with:

- Seconds versus milliseconds, rescaling every relevant number, unit and grid.
- Absolute clock versus countdown, retaining enough information for both to
  describe exactly the same state.
- Two clock origins, shifting now, deadline and absolute targets together.
- Neutral virtual ticks versus seconds, with an explicit tick-to-second mapping.

Present one representation per request when testing invariance; showing both
answers would leak the conversion. Retain a neutral non-temporal magnitude
comparison with the same numerical structure to distinguish general number
handling from time-specific framing. These transformations preserve the target;
changing the actual horizon or payoff does not and belongs in another experiment.

For model-selected timing, sample target times T at one fixed initial clock origin
under unchanged task information and define F(t) = P(T <= t). Separately estimate
q(t), the probability of answering PLAY in an independent snapshot at time t.
These snapshots are uncensored: earlier PLAY answers do not remove later probes,
and their prompts supply no additional evidence from prior decisions or silence.

The equality q(t) = F(t) is a **testable latent-threshold hypothesis**: each
interface represents a draw from the same target distribution and the snapshot
answer compares that target with t. A stable policy alone does not imply this
model. Estimate agreement and monotonicity of q(t) rather than calling one pair
of stochastic answers a contradiction. These are counterfactual snapshot probes,
not a continuing trajectory. In particular, q(t) is neither a cumulative
first-action probability nor the conditional probability of acting after previous
WAIT decisions; Stage 2 distinguishes those quantities.

Primary outcomes: target error in common units, premature and overdue actions,
representation discrepancies, and decision probability by time relative to target.
Report invalid schemas, refusals, provider errors and truncation separately.
Exact targets provide an external reference; a freely selected delay is an
observed policy, not ground truth about the correct time to act.

## Stage 2: plans, polling and memory

Run repeated-query trials at declared virtual grid points. Vary polling intervals
while keeping the horizon fixed, then vary timestamps while holding the number
of prompts fixed. These are different interventions and should be reported
separately. Distinguish:

1. Fresh requests at each snapshot with no previous model answers.
2. Requests containing the previous WAIT answers and time updates.
3. Requests explicitly reminding the agent of its earlier proposed action time.

The third condition measures adherence to an explicit prior plan; it is not the
same test as independently eliciting a plan and a policy. A useful signature is
deadline drift: an agent proposes time 20 initially, but at time 10 proposes a
further delay of 20 under an unchanged, externally fixed target. Without an
external target or a remembered commitment, free replanning may be legitimate
and should not automatically be called temporal inconsistency.

### More questions can mechanically mean earlier action

If a stateless agent says PLAY with probability p at every query regardless of
the clock, then under independent draws:

    P(at least one PLAY after n queries) = 1 - (1 - p)^n.

At p=0.02 this is approximately 18% after 10 queries and 87% after 100. An earlier
first PLAY under frequent polling can therefore arise without any change in time
representation or patience. With time-varying independent snapshot probabilities
p_i, survival through n polls is the product of (1-p_i). With history-dependent
policies, the corresponding hazards must condition on surviving prior decisions;
stateless snapshot probabilities cannot be substituted without that assumption.

The following probability calculation is our derivation for this proposed design,
not an empirical result from the literature. For a target drawn once from F and
retained throughout a trajectory, execute it at the first eligible grid point
t_1 < ... < t_n. The first point is at or after the initial origin and receives
all targets T <= t_1. Include the deadline as the final point; target mass beyond
it remains no action by the deadline, without renormalizing F.

To reproduce this target distribution using decisions conditioned on no earlier
PLAY, the required grid hazards are:

    h_1 = F(t_1)
    h_i = [F(t_i) - F(t_(i-1))] / [1 - F(t_(i-1))], for i >= 2.

The second expression applies only when 1 - F(t_(i-1)) > 0. When that denominator
is zero, no surviving trajectory remains and its conditional hazard is undefined.
These hazards yield P(first PLAY by t_i) = F(t_i). By contrast, independently
sampling each snapshot's q(t_i) = F(t_i) yields:

    P(first PLAY by t_n) = 1 - product_i [1 - F(t_i)].

For F(t_1)=0.2 and F(t_2)=0.4, independent snapshot draws give 0.52 by the second
poll. Retaining one target gives 0.40; its conditional hazards are 0.2 and 0.25.
Thus, snapshot agreement can coexist with earlier action under repeated sampling.
This difference alone is not a representation inconsistency. New information or
history-dependent replanning can change the target distribution and hazards, so
the fixed-F comparison must hold those influences constant.

Compare observed first-action distributions with this sampling baseline and with
deterministic threshold agents. Include same-time repeated-query controls and
matched call-budget controls; label repeated same-time measurements as duplicate
observations, not additional elapsed time. Conversation history changes token
length as well as memory, so include an equal-length neutral-history control if
attributing its effect to remembered decisions. Log actual calls and tokens.

## Stage 3: put the interfaces back into The Mind

Use a single shared virtual clock. At each grid point, query every active player
from the same frozen public state, collect all decisions, then execute the PLAY
set atomically with randomized tie-breaking. Update public history only after
that batch. Never run one player's private counter ahead of the others. A never-
PLAY trajectory ends as no action by the deadline, distinct from malformed output.
Here every card is due, so an unplayed card is a behavioral timeout. It is not
correct waiting of the kind measured by Stage 1's never-due control.

Grid polling coarsens action times. Execute a precommitted schedule on the same
grid by rounding each time up to its first eligible polling point, retaining both
the chosen continuous time and its executed time. Ties introduced by the grid can
cause a perfect continuous-time strategy to fail; compare both interfaces against
the same discretized threshold control, rather than requiring 100% grid success.
Keep the one-card action restriction identical across interfaces for this stage.

Silence is information in a multi-agent game: no one playing by time t can change
beliefs about the remaining hands and partners' policies. A polling agent sees
this survival information, while a precommitted agent cannot update on it. Start
with prerecorded public trajectories and a fixed known partner policy to control
the available evidence; then use endogenous live partners to measure the total
coordination effect. Do not attribute their difference solely to a clock sense.
In a targeted silence comparison, distinguish a complete observation stream with
no intervening plays from a snapshot explicitly marked stale or unobserved during
the interval. An unchanged snapshot alone does not prove that nobody acted. Also,
hiding timestamps does not remove timing information when known poll intervals
and query counts reveal elapsed time. Record these indirect cues in each condition.
Specify whether the displayed timer is since round start or since the last public
play; if using the latter, expose the reset event and map actions to one absolute
clock internally. Never change between these semantics silently.

## Actual time versus displayed time

Virtual-time tests concern numerical state updates. A separate optional test can
vary actual wall-clock pauses while keeping request content byte-identical, or
vary displayed elapsed time while holding real delays roughly fixed. Use fresh
requests without clock tools and log all input-visible timestamps, request order,
model versions and latency. The null prediction for the content-controlled test
is no systematic effect of an unobserved pause. Server drift, load, routing and
sampling are alternative explanations if one appears. A difference is not by
itself evidence of an internal clock or subjective time perception.

This is lower priority than displayed-time and polling controls. No long real
waits or timestamp-hiding experiments have been performed as part of this update.

## What would justify continuing

A reproducible failure of unit or clock-origin invariance under explicit targets
would identify a practical temporal-representation weakness. Consistent numerical
performance but disagreement between equivalent timing interfaces would identify
a decision-format effect. Partner-specific changes beyond numerical compliance,
grid resolution, sampling hazards and informative silence would justify stronger
coordination experiments. Effects that disappear under the appropriate baseline
should be reported at that simpler level.

Before collecting a confirmatory sample, choose the primary contrast, a minimum
effect worth detecting, replications, held-out cases and a call budget. Randomize
condition order; cluster repeated probes by target/state and continuing sessions
by independent trajectory. Do not treat every poll as an independent trial, and
account for the survival selection that gives later-acting agents more polls.
Do not infer a mechanism from model-written explanations alone. Requesting
explanations also changes computation and the prompt; keep that as a separate
audit condition rather than mixing it into the primary action-only comparison.
This staged plan
comes before a larger cross-play matrix; it avoids expanding spend while the
individual timing-compliance confound remains unresolved.

## Related work

The [canonical literature review](literature-review.md) records the closest
predecessors and their limits. SentinelBench compares duration-based sleep with
condition-based waiting under different observation and call schedules. The
Engagement Process compares agent loops, periodic polling and event-driven
engagement using a simulated token clock. Deadline experiments compare initial
budgets with remaining-time updates, combining model latency and optional
speech-rate delay; these do not isolate internal tracking from deadline salience. TicToc tests
elapsed-context judgments about tool use. Our proposed contribution is the
controlled comparison of timing representations and decision interfaces, with
observation, sampling and computation differences measured explicitly.

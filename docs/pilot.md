# Revival pilot

September 5, 2026. This page records an exploratory instrument check, not a
confirmatory experiment or a model ranking. The prior February results are not
pooled with these runs.

## Integration choices made before scored pilot

The provider model-list APIs returned exact IDs `gpt-5.4-mini-2026-03-17` and
`claude-haiku-4-5-20251001` on September 5. These are economical integration and
pilot choices; neither is presented as the newest or strongest available model.
Both use fresh text-only requests with no tools or shared conversation.

An unscored seed-9999 smoke test produced valid plain JSON from OpenAI and a valid
JSON object inside Markdown fences from Anthropic. The initial plain-JSON parser
correctly exposed this as an invalid response, rather than substituting a move.
Before running the scored suite, parsing was changed uniformly to accept exactly
one enclosing JSON code fence as well as plain JSON. No numbers are repaired,
imputed or clamped by the parser. The raw response and normalization are recorded.
The first exploratory pilot used different seeds (1000–1005), and no prompt or
parser tuning occurred within that suite.

That complete free-text pilot showed that accepting Markdown fences was
insufficient: Haiku commonly added explanatory prose outside its JSON object.
Those trials remain invalid, and no numbers were extracted from surrounding
prose. The full run is preserved in
[`results/pilot-free-text-20260905`](../results/pilot-free-text-20260905/).
Its provider comparisons cannot support behavioral claims.

The revised protocol enables each provider's native structured-output feature
with the same object schema: one required `times` array containing numbers and
no additional properties. The adapters still validate exact card count, finite
values, deadline behavior, refusals and truncation locally. Official support is
documented for [GPT-5.4 mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
and [Haiku 4.5](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).
Provider implementations may add different format instructions; native structured
output is itself part of the measurement protocol, not a guarantee of provider
equivalence. Full request schemas and responses are retained.

The revised pilot uses fresh seeds 1100–1105 after a two-card integration check
at seed 9998. These are exploratory validation rounds after an observed integration
failure, not a held-out confirmatory study.

## Results

All three retained runs have complete manifests with verified source and artifact
hashes. The earlier smoke runs remain unscored scratch artifacts.

### Offline instrument validation

[Report](../results/offline-20260905/report.html) ·
[Summary](../results/offline-20260905/summary.json)

Eight conditions on 100 matched deals produced 800 rounds, with no infrastructure
failures. Shared proportional slopes each won 100/100, including under feedback.
Mismatched slopes won 32/100 and 29/100 in opposite seat orders. Independent random
times won 3/100; coarse quantization reduced the shared rule to 58/100. These are
algorithmic controls, **not LLM performance measurements**. They demonstrate that
the instrument can distinguish mapping compatibility and timing interventions.

### Native structured-output pilot

[Interactive report](../results/pilot-structured-20260905/report.html) ·
[Summary](../results/pilot-structured-20260905/summary.json) ·
[Raw rounds](../results/pilot-structured-20260905/rounds.jsonl)

A = GPT-5.4 mini (`gpt-5.4-mini-2026-03-17`); B = Claude Haiku 4.5
(`claude-haiku-4-5-20251001`). Each condition has the same six two-player deals,
with two cards per player. All **48 rounds were valid**: 16 completed, 32 ended
with a misorder, and none had a timeout, invalid response or provider error.

| Condition | Completed / attempted |
| --- | ---: |
| AA | 2 / 6 |
| AB | 0 / 6 |
| BA | 1 / 6 |
| BB | 5 / 6 |
| AA, supplied proportional convention | 6 / 6 |
| BB, supplied proportional convention | 2 / 6 |
| AB, public feedback | 0 / 6 |
| AB, historical timestamps hidden | 0 / 6 |

The unprompted same-model teams completed 7/12 attempts and mixed teams 1/12.
The deal-paired compatibility contrast was −50 percentage points; its exploratory
bootstrap interval was [−83.3, −16.7]. With only six independent deals, stochastic
model requests, multiple exploratory conditions and fixed condition order, this
is a **hypothesis-generating signal**, not a model ranking or a confirmed effect.
The zero difference between feedback variants is a floor effect in this pilot;
its degenerate bootstrap interval is not evidence that timestamps have no value.

The explicit-convention condition exposes another confound. Haiku sometimes did
not execute the provided formula. For example, on seed 1100 it scheduled cards
8 and 10 at times 80 and 100, while its teammate scheduled 3 and 11 at times 3
and 11. This is visible in the raw provider outputs; schema validity does not
establish arithmetic or instruction adherence. The corresponding deterministic
algorithmic convention succeeds. **Numerical instruction execution must be
measured separately before attributing a model gap to partner compatibility.**

There were 108 actual API calls (54 per model), below the conservative bound of
168. Reported usage totals were 50,934 input tokens and 1,735 output tokens. No
retries, synthetic moves, response repairs or changes to the frozen protocol
occurred during this revised pilot. Seeds reproduce the deals and simulator,
not the sampled provider responses.

### Failed free-text pilot retained for audit

[Report](../results/pilot-free-text-20260905/report.html) ·
[Summary](../results/pilot-free-text-20260905/summary.json)

Of 48 rounds, 33 had an invalid response; only 15 were behaviorally valid. Every
deal block in the cross-play contrast had an infrastructure failure. Those
comparisons cannot establish differences in coordination. Retaining this run
documents why native structured output became part of the revised protocol.

## Recommendation

Continue as a focused mechanism study, starting with a preregistered individual
numerical-convention compliance check, stronger algorithmic controls, neutral
task-name variants, and a larger matched-deal cross-play experiment. Decide whether
to study compliance failure as its own outcome or restrict coordination claims to
models/protocols that pass that control; do not silently filter individual failed
trials. Add partner-specific history and matched shuffled-history controls before
claiming adaptation. A benchmark implementation is now usable, but the six-deal
pilot and its unresolved compliance confound are insufficient for a substantive
research paper. See [research-design.md](research-design.md) for the broader design.

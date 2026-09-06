# Literature review: timing interfaces and coordination in The Mind

Updated September 6, 2026. This is a targeted scoping review for the
[research design](research-design.md) and its proposed
[timing-interface experiments](time-and-decision-interfaces.md), not a systematic
review or a claim to exhaustive coverage. It supersedes the earlier short
related-work lists and does not validate the preserved legacy paper's results.

The project has a plausible, narrower contribution: **identify when timing
interfaces change individual decisions and partner compatibility after accounting
for numerical compliance, information, action opportunities and computation.**
Prior work already includes LLMs playing The Mind, self-play versus cross-play,
timing-sensitive tool decisions, and comparisons of polling with other waiting
interfaces. Another game implementation or an uncontrolled difference between
“wait ten seconds” and repeated “act now?” would have limited research value.

## Scope and terminology

The search covered direct The Mind implementations and human studies, LLM temporal
reasoning and action, monitoring interfaces, and coordination conventions. Sources
were checked through primary papers, official proceedings, institutional records
and source repositories, including references discovered in those works. The
source register below records versions and reading depth; a citation is not a
claim that every appendix, proof or experiment was independently reproduced.
Preprints, workshop papers, theses and software are identified separately.

We distinguish four questions throughout:

| Question | Observable test | Interpretation limit |
| --- | --- | --- |
| Can an agent represent time correctly? | Equivalent units, origins, deadlines and duration calculations | Numerical competence does not establish appropriate action. |
| Does an agent use time when deciding? | Action choices under controlled timestamps, observations and deadlines | A timestamp effect can reflect salience or a changed policy. |
| Does an interface change the stopping rule? | A chosen target versus a sequence of conditional PLAY/WAIT decisions | Repeated sampling, information and call budgets can change outcomes mechanically. |
| Do partners coordinate through observable timing? | Paired cross-play and interventions on public event streams | Success can follow a shared monotone rule without online partner inference. |

These are behavioral questions. Neither language about duration nor a successful
timing policy establishes subjective experience of time.

## Direct precedents in The Mind

**Bischof (2025), *Mind Agents* — research software.** This is a direct LLM–The
Mind precedent, with multiple providers, heterogeneous players and integer waiting
proposals. At the inspected commit, the game collects active players' proposed
waits, selects the shortest with randomized ties, plays that card and replans.
Thus it already separates proposal ordering from provider latency. It does not
maintain an accumulated game clock. Prompts suggest gap-dependent waiting, and
the simulator saves single-agent decisions across constructed states. The inspected
result samples do not establish paired full-game cross-play effects. We should
credit this implementation and distinguish our absolute virtual clock, paired
interventions, controls and failure accounting. This is not the first LLM version
of the game. [Pinned source and results](https://github.com/BBischof/mindAgents/tree/bb11928fd907887ac41a38670d078f556480d15e).

**Theuwissen (2022), *Time Perception in the game “The Mind”: a Cognitive Model
Approach* — bachelor's thesis, University of Groningen.** Participants played
fixed games against a scripted computer; 16 of 20 recruits entered the analysis.
Waiting increased with card gap, and an ACT-R model was fitted to the observations.
One participant was excluded for reporting a probability-based strategy. Fixed
scripts, a small sample and strategy-based selection limit interpretation; this
does not identify human-human convention formation or an internal-clock mechanism.
It motivates scripted partners, gap-based baselines and explicit separation of
time since the last play from time since round start.
[Institutional thesis](https://fse.studenttheses.ub.rug.nl/26779/).

**Farrell and Lopez Valdes (2023), *“The Mind” promotes brain synchronization:
an ecological evaluation of brain synchronization in co-operative tasks* — IEEE
EMBC.** This EEG study used six people in two triads. Failed games were generally
too short for its synchrony analysis, and observation durations varied. It is a
direct human-game precedent, but two teams and success-conditioned measurements
cannot identify a shared timing convention. For our design, the useful lesson is
to retain failures and control observation windows.
[Publication record](https://pubmed.ncbi.nlm.nih.gov/38082864/).

**Kennedy, Shields, Farrell and Lopez Valdes (2026), *Analysis of inter-brain
synchrony in group-based electroencephalography to assess task-dependent
interactions* — Frontiers in Neuroergonomics.** Across experiments involving
36 people, the authors examine cooperative and individual tasks, an adversary
manipulation, and duration confounding. Cooperative-versus-individual synchrony
differences were nonsignificant. EEG correlations do not by themselves identify
shared clocks, causal information exchange or subjective time. This follow-up
strengthens the methodological case for controlling exposure and stopping rules,
not a claim that the game measures “mind reading.”
[Full article](https://www.frontiersin.org/journals/neuroergonomics/articles/10.3389/fnrgo.2026.1774423/full).

**Andrade (2023), *Playing “The Mind” game with a robot* — master's thesis,
Universidade de Lisboa.** Forty-two participants formed 21 teams with a robot
under gaze manipulations. A reported gameplay bug made achieved level and gameplay
duration unusable for analysis. The study is useful precedent for manipulating
nonverbal channels and validating instruments, but its reported lack of
synchronization evidence should not be treated as reliable evidence that gaze
cannot affect coordination.
[Institutional record](https://scholar.tecnico.ulisboa.pt/records/LWHoZP23pCQspP8N1f3SqAj9dwRGPfX0hLQV).

## Waiting, observation and deadlines

**Maldaner et al. (2026), *SentinelBench: A Benchmark for Long-Running Monitoring
Agents* — preprint, v2.** This is a close interface precedent: 100 tasks across
10 synthetic web environments compare `sleep(time)` with
`wait_for(condition, timeout)`. The latter uses page differences and model checks
to resume on a condition. Costs fall across the tested models, while success and
reaction-time effects vary; it is not uniformly faster or more successful.
These are harness comparisons with different observation and call schedules,
not equivalent-information tests of a model's time representation. Tasks where
the trigger never occurs make correctly doing nothing a measurable outcome.
Our proposed experiment should adopt that control and separately measure
correctness, delay and resource use.
[Versioned paper](https://arxiv.org/html/2606.05342v2).

**Li et al. (2026), *Engagement Process: Rethinking the Temporal Interface of
Action and Observation* — preprint, v2.** This work formalizes decoupled,
timestamped action and observation streams, including deliberation latency,
delayed feedback and persistent actions. Its LLM experiments compare an agent
loop, periodic polling and an event-driven interface. A simulated token clock and
changed observation timing are part of those comparisons. Consequently, neither
the general idea that temporal interfaces matter nor a polling comparison is new.
Our narrower question is whether a representation or stopping-policy discrepancy
survives controlled information and execution opportunities.
[Versioned paper](https://arxiv.org/html/2605.11484v2).

**Sehgal, Guntuku and Ungar (2026), *Real-Time Deadlines Reveal Fragile Temporal
Adaptation in LLM Strategic Dialogues* — v2; author-listed EMNLP 2026.** The study
compares negotiation with an initial time budget, remaining-time updates, and
turn limits. Updates help some tested models, but the paper explicitly cautions
that the contrast does not distinguish internal tracking from salience or policy
activation. Generation latency and an optional speech-rate delay enter the clock.
This is closer to action under deadlines than temporal question answering, but
its conditions should not be treated as exactly matched decision opportunities.
Use its separation of reminders, explicit tracking and runtime effects to design
our own ablations. The August 30 revision changes the earlier title and adds
relevant controls; this review uses that revision.
[Versioned paper](https://arxiv.org/html/2601.13206v2),
[implementation timing notes](https://github.com/sehgal-neil/llm-temporal-awareness#timing-and-outputs).

**Shi et al. (2026), *AsyncTool: Evaluating the Asynchronous Function Calling
Capability under Multi-Task Scenarios* — preprint, v3.** Delayed tool results and
concurrent tasks test whether agents track dependencies and continue useful work
while awaiting feedback. The study reports difficulty with premature continuation
and assumed results; additional switching does not necessarily improve outcomes.
Its constructed tool delays and multitask setting differ from our single pending
card. It provides an adjacent validity question: can an agent keep an action
pending without inventing that its prerequisite has happened?
[Versioned paper](https://arxiv.org/html/2605.27995v3).

## Temporal representations and behavioral interpretation

**Static temporal reasoning supplies calibration tasks, not online timing
evidence.** Fatemi et al.'s *Test of Time* (ICLR 2025) separates temporal-graph
reasoning from arithmetic and varies structure, query type and presentation.
Its experiments used models available in 2024; publication year should not be
mistaken for a current capability assessment.
[Conference paper](https://proceedings.iclr.cc/paper_files/paper/2025/file/eb7295a8bc613b375726659c2ecd6f14-Paper-Conference.pdf).
Chu et al.'s *TimeBench* (ACL 2024) spans symbolic reasoning, temporal commonsense
and event relations; effects of explanation prompting vary by category.
[Proceedings](https://aclanthology.org/2024.acl-long.66/).
Wang and Zhao's *TRAM* (Findings of ACL 2024) includes ordering, arithmetic,
frequency and duration questions with heterogeneous task and prompt performance.
[Proceedings](https://aclanthology.org/2024.findings-acl.382/).
Together these motivate simple calculation and comparison controls before
attributing a failed card schedule to strategy. They do not test a continuing
agent's willingness to wait.

**Wang et al. (2025), *Discrete Minds in a Continuous World: Do Language Models
Know Time Passes?* — Findings of EMNLP.** The paper studies dialogue-duration
judgments, urgency-conditioned generation and navigation in BombRush. In the
navigation task, reasoning tokens consume simulated seconds; actual provider
latency is deliberately excluded. Adapting verbosity under this clock is evidence
about behavior under a defined reasoning cost, not unobserved wall-clock sensing.
Our main virtual-time test should keep computation separate from game time;
token-dependent action costs belong in a distinct intervention.
[Proceedings and paper](https://aclanthology.org/2025.findings-emnlp.1016/).

**Cheng et al. (2026), *Your LLM Agents are Temporally Blind: The Misalignment
Between Tool Use Decisions and Human Time Perception* — Findings of ACL.** TicToc
tests whether elapsed time changes tool-use judgments and reliance on earlier
context. The final proceedings version has 76 scenarios and 3,016 retained
samples. It establishes a relevant evaluation of time-sensitive decisions, but
does not equate choosing a target with repeatedly sampling a stopping decision.
Human judgments of appropriate tool use also differ from our exact numerical
reference targets. The project should measure both explicit-target compliance and
free choices, with separate interpretations.
[Proceedings and paper](https://aclanthology.org/2026.findings-acl.1848/).

**Bao and Srikumar (2026), *The Machine's Internal Clock: Do LLMs Share Human
Temporal Illusions?* — August preprint, v1.** This compares humans and models on
narrative pairs adapted from temporal illusions. Models' answers often align
with published psychological patterns more than human readers' answers do;
the authors interpret frequent references to psychology in reasoning traces as
consistent with retrieval. This is evidence about narrative judgments, not a
demonstration of experienced duration or a causal identification of retrieval.
Template dependence and reader-versus-character perspective also matter. For
our study, behavioral invariance tests carry more evidential weight than asking
agents to explain how waiting feels.
[Versioned paper](https://arxiv.org/html/2608.15394v1).

**Read, Frederick, Orsel and Rahman (2005), *Four Score and Seven Years from
Now: The Date/Delay Effect in Temporal Discounting* — Management Science.** Human
monetary choices differ when equivalent delays are described as calendar dates
rather than durations. This motivates testing representation invariance with
identical consequences. It supplies neither a predicted direction for LLM timing
choices nor evidence about repeated polling, action deadlines or subjective
machine time. Access here was limited to the publisher abstract and working-paper
excerpts, so no detailed effect-size claims are used.
[Publisher record](https://pubsonline.informs.org/doi/abs/10.1287/mnsc.1050.0412),
[working-paper record](https://researchonline.lse.ac.uk/id/eprint/22749/).

## Coordination, conventions and information channels

**Hu, Lerer, Peysakhovich and Foerster (2020), *“Other-Play” for Zero-Shot
Coordination* — ICML.** Self-play can produce conventions incompatible with
independently trained partners. Other-Play uses environment symmetries to address
this issue, with coordination-game and Hanabi experiments. The distinction
between self-play and cross-play predates LLM agents. Our paired AA/BB/AB/BA
comparison measures compatibility; it is neither an implementation of Other-Play
nor evidence for its theoretical guarantees.
[Proceedings](https://proceedings.mlr.press/v119/hu20a.html).

**Agashe, Fan, Reyna and Wang (2025), *LLM-Coordination: Evaluating and Analyzing
Multi-agent Coordination Abilities in Large Language Models* — Findings of
NAACL.** The work evaluates coordination games with a scaffold involving memory,
reasoning and grounding, and explicitly tests unseen partners. Its favorable
cross-play findings are specific to the tasks and scaffold. LLM coordination and
unseen-partner evaluation are established topics; our contribution requires
isolating what observable timing adds in a simpler environment.
[Proceedings and paper](https://aclanthology.org/2025.findings-naacl.448/).

**Hayler et al. (2026), *Zero-Shot Coordination Among LLM Agents* — ICLR
MALGAI workshop.** This work explicitly studies generic scaffolds in minimal
coordination environments and difficulties with partner reasoning. Small games
that isolate coordination are therefore not a new research direction. Detailed
results were not verified here because full-paper access was blocked; the citation
supports positioning from the primary first-page text and verified workshop
status, not a quantitative comparison.
[Paper](https://openreview.net/pdf?id=HHPbQlyA7Y),
[coauthor publication record](https://bsarkar321.github.io/research/index.html).

**Ashery, Aiello and Baronchelli (2025), *Emergent social conventions and
collective bias in LLM populations* — Science Advances.** Randomly paired agents
select names, receive local feedback and can converge on population conventions;
the study also examines interventions by committed alternatives. This concerns
repeated population interaction. Our independent single-deal experiments have no
cross-deal memory and cannot establish convention formation, learning or tipping
points merely from compatible timing choices.
[Journal article](https://doi.org/10.1126/sciadv.adu9368),
[author manuscript](https://arxiv.org/html/2410.08948v2).

**Barrie and Törnberg (2025), *Emergent LLM behaviors are observationally
equivalent to data leakage* — preprint/commentary.** The authors challenge the
identification of newly emerging social behavior when models can recognize
coordination-game structures and describe expected strategies. This is a
methodological alternative, not proof that our task or a particular result leaked
into training. Neutral task names and rescaled cards test robustness but cannot
establish absence of prior knowledge. Report observed compatibility and specify
the evidence required before calling it emergence.
[Versioned paper](https://arxiv.org/html/2505.23796v1).

**Buscemi et al. (2026), *When Numbers Start Talking: Implicit Numerical
Coordination Among LLM-Based Agents* — preprint, v2.** The experiments compare
natural language, deliberately communicative sequences of ten numbers, no
communication, and random-number conditions in two-action games. Despite the
terminology, the numerical sequences are explicit messages with restricted
alphabets; they are not observed action times. Agent-generated versus externally
randomized structure is a useful control. Reduced message entropy alone does not
identify what information is conveyed or demonstrate a timing-channel mechanism.
[Versioned paper](https://arxiv.org/html/2601.03846v2).

**Anantharam and Verdú (1996), *Bits through queues* — IEEE Transactions on
Information Theory.** This establishes a mathematical timing channel in a queueing
model. It is a foundation for distinguishing message content from information
carried by event timing, not empirical evidence of an LLM strategy. Its specific
capacity results cannot be transferred to this game. Our observation specification
must include actions, silence, timestamps, query counts and timer resets:
“no chat” is insufficient to establish “no communication.”
[Author publication record](https://collaborate.princeton.edu/en/publications/bits-through-queues-2/).

## Implications for the proposed study

The following are our design judgments and probability reasoning, not results
reported by the cited studies.

1. **Begin with an exact target.** Compare absolute time, remaining delay and
   PLAY/WAIT judgments at identical states. Vary units, clock origins and neutral
   numerical framing. Separate explicit targets, computed targets and freely
   selected conventions; only the first two have an external correctness standard.
2. **Distinguish a target distribution from a stopping hazard.** If one sampled
   target has cumulative distribution F, its probability of being due at time t
   is F(t). Repeatedly making a fresh PLAY draw with that same probability does
   not reproduce the original target distribution. Conditional stopping hazards
   must account for surviving earlier polls. The
   [timing design](time-and-decision-interfaces.md#more-questions-can-mechanically-mean-earlier-action)
   gives the derivation and a counterexample. An earlier first action alone is
   therefore insufficient evidence of temporal inconsistency.
3. **Separate representation from the complete interface.** First use matched,
   independent snapshots. Then evaluate sequential interfaces with the same
   execution grid, explicit memory conditions and measured call/token budgets.
   Report contrasts that change information or opportunities as combined effects.
4. **Make nonaction observable.** Include cases where an action is never due,
   alongside missed deadlines for actions that were due. Preserve invalid outputs,
   timeouts and failed games. Forced endpoint actions cannot measure willingness
   to wait; success-only timing summaries can hide selection effects.
5. **Control what silence means.** Compare a complete stream with no events to
   an explicitly stale or unobserved interval. Use prerecorded trajectories before
   live partners; then test endogenous coordination with paired deals and strong
   monotone and partner-estimation baselines. Clock redaction alone is insufficient
   if poll counts disclose elapsed time.
6. **Require a result beyond the controls.** Continue toward a substantive paper
   if a preregistered, held-out representation or compatibility effect replicates
   across wording and model families and survives the relevant numerical,
   sampling, grid and information controls. An effect fully explained by those
   controls belongs in a measurement or replication report. Existing small pilot
   differences do not settle this decision.

A defensible candidate contribution is **an auditable decomposition of timing
decisions and coordination under controlled interfaces**, including a useful
negative result if common apparent effects are explained by the controls. This
search does not establish that the full combination is novel. The
[Hugging Face incident discussion](research-design.md#why-the-hugging-face-incident-matters)
remains motivation to study available coordination channels, not evidence that
card timing reproduces the incident's mechanisms or predicts harmful behavior.

## Source register and verification limits

Primary links above identify each work. The table records the versions and
supporting locations actually used; publication status is checked as of the review
date. “Methods/results” means those sections were read, not independently replicated.

| Work | Version or publication | Supporting locations and reading depth |
| --- | --- | --- |
| Bischof | Software commit `bb11928fd907887ac41a38670d078f556480d15e`, February 13, 2025 | README; prompts; `src/play.py` lines 218–236, 331–335; simulator; two result CSVs; repository history. |
| Theuwissen | Groningen BSc thesis, 2022 | Full seven-page text, methods/results; no held-out model validation established. |
| Farrell & Lopez Valdes | EMBC 2023, DOI `10.1109/EMBC40787.2023.10340212` | Full four-page paper, including duration and failed-game exclusions. |
| Kennedy et al. | Frontiers in Neuroergonomics 7:1774423, March 31, 2026 | Methods, results tables and discussion. |
| Andrade | Lisboa MSc thesis, 2023 | Institutional metadata and ten-page extended summary, methods/results/limitations. |
| SentinelBench | arXiv `2606.05342v2`, June 5, 2026; preprint | Sections 2–5, especially 4.1 and 4.2; official repository README. |
| Engagement Process | arXiv `2605.11484v2`, June 8, 2026; preprint | Temporal-interface formulation and section 5.2 LLM comparisons. |
| Real-Time Deadlines | arXiv `2601.13206v2`, August 30, 2026 | Sections 3.2–3.3, 4.2, 4.5 and 4.7; repository timing notes. EMNLP 2026 is author-listed on arXiv; proceedings record not independently verified. |
| AsyncTool | arXiv `2605.27995v3`, August 31, 2026; preprint | Sections 2.1–2.2, section 3 discussion and limitations. |
| Test of Time | ICLR 2025; arXiv `2406.09170` | Final conference metadata/results, section 3 methods, sections 4.1–4.4 and Tables 4, 6, 9. |
| TimeBench | ACL 2024 Long Papers, pp. 1204–1228, DOI `10.18653/v1/2024.acl-long.66` | Sections 2.2–2.4 and 5.1–5.3, Tables 4–5. |
| TRAM | Findings of ACL 2024, pp. 6389–6415, DOI `10.18653/v1/2024.findings-acl.382` | Section 4.2 and task examples around p. 6403; targeted inspection, not full appendix review. |
| Discrete Minds | Findings of EMNLP 2025, pp. 18703–18729, DOI `10.18653/v1/2025.findings-emnlp.1016` | Sections 4.1, 5.1–5.2 and 6–6.2; repository README. |
| TicToc | Findings of ACL 2026, pp. 37082–37104, DOI `10.18653/v1/2026.findings-acl.1848` | Final proceedings version and benchmark/evaluation methods; earlier preprint counts superseded. |
| Bao & Srikumar | arXiv `2608.15394v1`, August 15, 2026; preprint | Abstract, narrative construction, sections 4 and 5 introductory analysis; no independent mechanism verification. |
| Read et al. | Management Science 51(9):1326–1335, 2005 | Publisher abstract and indexed 2004 working-paper excerpts; full PDF access blocked. |
| Other-Play | ICML 2020, PMLR 119:4399–4410 | Introduction, section 6.1/Figure 3 and section 6.2; not a full theorem audit. |
| LLM-Coordination | Findings of NAACL 2025, pp. 8053–8072 | Sections 4.1–4.1.1 and 5, Table 5, limitations. |
| Hayler et al. | ICLR 2026 MALGAI workshop | Primary first-page text and coauthor publication record only; full-paper retrieval blocked. |
| Ashery et al. | Science Advances 11:eadu9368, 2025; arXiv `2410.08948v2` | Experimental setup, convention selection and tipping-point sections; supplements not comprehensively audited. |
| Barrie & Törnberg | arXiv `2505.23796v1`, May 26, 2025; commentary | Main argument, recognition prompts, Figure 1 description and conclusions; no reproduction or verification of separate code allegations. |
| Buscemi et al. | arXiv `2601.03846v2`, April 19, 2026; preprint | Sections 2.1–2.5 and 3.1, selected section 3.2 interpretation. |
| Bits through queues | IEEE TIT 42(1):4–18, 1996, DOI `10.1109/18.481773` | Author publication record and abstract; full proofs not retrieved. |

## Remaining literature work before submission

Obtain and read Hayler et al.'s full workshop paper; inspect the full date/delay
article before relying on detailed human comparisons; refresh preprint versions
and publication status; and check additional direct The Mind implementations and
temporal-action benchmarks against the final experiment. These gaps limit
priority claims. They do not prevent implementing the proposed controls or
evaluating whether this particular project earns further investment.

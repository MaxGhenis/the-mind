# Emergent Coordination Without Communication: A Study of Multi-Agent LLM Systems Using The Mind Card Game

## Core Research Insight (Updated)

**Key finding from convergence-game research:** Same-model teams coordinate trivially well because they share internal biases (timing patterns, semantic associations). The interesting research question is **cross-model coordination** - can LLMs adapt to teammates with different internal representations?

**Literature gap:** [LLM-Coordination (NAACL 2025)](https://arxiv.org/abs/2310.03903) found 0% success in implicit coordination without communication, BUT 52% baseline when models are from the same family. No one has tested timing-based coordination (The Mind is novel).

---

## Paper Structure

### Abstract (150-250 words)
- **Problem**: Testing LLM capacity for implicit coordination through timing strategies
- **Key insight**: Same-model coordination may be trivially good due to shared biases; cross-model coordination reveals true adaptive ability
- **Approach**: The Mind card game - players play numbered cards in ascending order WITHOUT communication
- **Models tested**: GPT-4o, Claude 3.5, Gemini across homogeneous and heterogeneous configurations
- **Key findings**: [TBD from experiments]
- **Contribution**: First LLM simulation of The Mind; novel benchmark for timing-based implicit coordination

---

### 1. Introduction (2-3 pages)

**1.1 Motivation**
- Multi-agent AI coordination increasingly important
- Most research focuses on explicit communication
- The Mind tests implicit coordination through timing alone
- **Critical insight**: Same-model success may not indicate true coordination ability

**1.2 Research Questions**
1. Can LLMs coordinate implicitly through timing strategies?
2. **Do same-model teams succeed trivially via shared internal biases?** (cf. convergence-game)
3. How well do LLMs adapt to cross-model teammates with different timing patterns?
4. **Are LLMs consistent between prediction and reactive decision-making?** (Novel consistency test)
5. Can agents learn/adapt across rounds?
6. What emergent timing strategies arise?

**1.3 Contributions**
- First LLM simulation of The Mind card game
- Novel benchmark separating "shared bias" from "true coordination"
- Cross-model coordination analysis
- **Prompting strategy comparison revealing LLM internal consistency**
- Open-source experimental framework

---

### 2. Background and Related Work (2-3 pages)

**2.1 The Mind Card Game**
- Rules: Cards 1-100, ascending order, no communication
- Why timing is the only coordination mechanism
- Citation: [Wolfgang Warsch, 2018]

**2.2 LLM Multi-Agent Coordination**
- [LLM-Coordination (NAACL 2025)](https://arxiv.org/abs/2310.03903) - 0% implicit coordination, but 52% same-family baseline
- [MindAgent](https://arxiv.org/abs/2309.09971) - Multi-agent planning
- [Playing repeated games with LLMs](https://www.nature.com/articles/s41562-025-02172-y)
- **Gap**: No timing-based coordination studies

**2.3 The Same-Model Coordination Problem**
- Evidence from convergence-game: same-model pairs converge in ~2.5 rounds, cross-model in ~7 rounds
- Shared training → shared internal representations → trivial coordination
- True test of coordination: cross-model adaptation

**2.4 Theory of Mind in LLMs**
- ToM required to reason about teammate's timing strategy
- Limited evidence for ToM in current LLMs
- The Mind as ToM probe

---

### 3. Methodology (3-4 pages)

**3.1 Experimental Design**

*3.1.1 Game Implementation*
- Cards numbered 1-100
- 2-6 players per game
- Round R: each player receives R cards
- Success: all cards played in ascending order
- **Timing mechanism**: Each LLM outputs wait_time (seconds) before playing

*3.1.2 LLM Agent Architecture*
- System prompt with game rules
- Game state (cards played, time elapsed, players remaining)
- Output: JSON with wait_seconds, reasoning, confidence
- Optional memory for cross-round learning

*3.1.3 Prompting Strategies* **(KEY METHODOLOGICAL INNOVATION)**

Two approaches testing LLM internal consistency:

**Strategy A: Prediction-Based**
- Prompt: "How long would you wait before playing your card?"
- LLM outputs wait_seconds upfront
- Decision made once at start of turn
- Tests: Planning and prediction ability

**Strategy B: Reactive-Based**
- Prompt at each timestep: "[X seconds have elapsed] Do you play your card now?"
- LLM answers yes/no at each discrete time interval
- Decision made continuously
- Tests: Real-time reasoning and impulse control

**Research Insight:** If an LLM says "I would wait 6 seconds" (Prediction) but then at t=6s says "No, not yet" (Reactive), this reveals **internal inconsistency** - the model lacks a coherent internal representation of timing/coordination. Consistency between strategies indicates true decision-making coherence.

This comparison tests whether LLM decisions are:
- **Coherent**: Same outcome regardless of prompting format
- **Context-dependent**: Different answers based on how the question is framed
- **Stable**: Consistent internal model vs ad-hoc reasoning

*3.1.4 Models Under Study*
| Provider | Models |
|----------|--------|
| OpenAI | gpt-4o, gpt-4o-mini |
| Anthropic | claude-3.5-sonnet, claude-3-haiku |
| Google | gemini-1.5-pro, gemini-1.5-flash |

*3.1.5 Experimental Conditions*
- **Homogeneous teams** (baseline - expected high due to shared bias)
- **Heterogeneous teams** (true coordination test)
- **Prompting strategies** (prediction vs reactive)
- With/without memory
- Temperature variations

**3.2 Metrics**

*3.2.1 Performance Metrics*
- Success rate (games won / games played)
- Round completion rate
- Cards played before failure

*3.2.2 Timing Analysis*
- Wait time distribution by card value
- Timing strategy: wait = α × card_value + β
- Cross-model timing alignment

*3.2.3 Coordination Metrics (Novel)*
- **Same-model baseline** vs **cross-model performance gap**
- Adaptation rate: how quickly agents calibrate to teammates
- Timing convergence over rounds

*3.2.4 Consistency Metrics (Novel)*
- **Prediction-Reactive Gap**: |predicted_wait_time - actual_reactive_play_time|
- **Consistency Score**: % of decisions where prediction matches reactive behavior (±1 second tolerance)
- **Directional Bias**: Do models consistently over-predict or under-predict their wait times?
- **Consistency by card value**: Does consistency vary with card difficulty (low/mid/high values)?

**3.3 Statistical Analysis**
- Bootstrap confidence intervals
- ICC for within-team consistency
- Mixed-effects models for learning

---

### 4. Results (4-5 pages)

**4.1 Same-Model vs Cross-Model Comparison** (KEY RESULT)
- Hypothesis: Same-model teams succeed via shared bias, not adaptive coordination
- Test: Compare homogeneous vs heterogeneous performance
- Expected pattern from convergence-game: same-model much better initially

**4.2 Timing Strategy Analysis**
- Emergent strategies (linear scaling?)
- Model-specific timing biases
- Cross-model timing conflicts

**4.3 Adaptation and Learning**
- Do agents adapt timing to teammates over rounds?
- Memory vs no-memory comparison
- Evidence of Theory of Mind?

**4.4 Prompting Strategy Comparison** (KEY RESULT - TESTS INTERNAL CONSISTENCY)

*4.4.1 Prediction vs Reactive Performance*
- Do models perform better with prediction or reactive prompting?
- Success rate comparison across strategies
- Which strategy leads to better coordination?

*4.4.2 Internal Consistency Analysis*
- **Consistency scores by model**: Which LLMs have coherent internal timing models?
- **Prediction-Reactive scatter plots**: Visual test of consistency
  - Perfect consistency = points on y=x diagonal
  - Systematic bias = consistent offset from diagonal
  - Random scatter = no internal coherence
- **Directional patterns**: Do models over-predict (say longer wait than they act) or under-predict?

*4.4.3 Consistency by Context*
- Does consistency vary by card value? (Low cards: 1-33, Mid: 34-66, High: 67-100)
- Effect of game state on consistency
- Team composition impact on consistency

*4.4.4 Theoretical Implications*
- **High consistency** → Model has stable internal representation of timing/coordination
- **Low consistency** → Decisions are context-dependent, no coherent model
- **Systematic bias** → Model can predict but struggles with real-time execution (or vice versa)

**4.5 Model Rankings**
- Performance hierarchy
- Which models adapt best to others?
- Which models show highest internal consistency?

---

### 5. Discussion (2-3 pages)

**5.1 The Shared Bias Problem**
- Same-model coordination may overestimate LLM abilities
- Cross-model experiments as more valid benchmark
- Implications for multi-agent system design

**5.2 Internal Consistency and Decision-Making Coherence**
- What does consistency reveal about LLM cognition?
- Prediction vs reactive as probe of internal representations
- Implications for LLM reliability in sequential decision tasks
- Comparison to human consistency in similar tasks

**5.3 Emergent Strategies**
- Linear timing was not explicitly taught
- Robustness of emergent conventions
- Strategy differences between prediction and reactive modes

**5.4 Theory of Mind Implications**
- Evidence for/against ToM in timing decisions
- Comparison to Hanabi research

**5.5 Limitations**
- API determinism challenges
- Limited model diversity
- Simulated timing vs real-time
- Discrete timesteps in reactive mode may not capture true continuous reasoning

---

### 6. Conclusion (1 page)
- First LLM simulation of The Mind
- Same-model coordination ≠ true coordination ability
- Cross-model adaptation as better benchmark
- **Prompting strategy comparison reveals internal consistency (or lack thereof)**
- Future work: human-AI teams, real-time APIs, finer-grained consistency tests

---

## Required Figures

| Figure | Description |
|--------|-------------|
| Fig 1 | The Mind game mechanics diagram |
| Fig 2 | Same-model vs cross-model success rates (KEY FIGURE) |
| Fig 3 | Timing strategy scatter: wait_time vs card_value by model |
| Fig 4 | Adaptation curves: cross-model performance over rounds |
| Fig 5 | Model pair heatmap: success rates for all combinations |
| Fig 6 | **Prediction vs Reactive scatter plot** (KEY CONSISTENCY FIGURE) - x-axis: predicted wait time, y-axis: actual reactive play time, by model |
| Fig 7 | **Consistency scores by model** - Bar chart showing % consistency (±1s tolerance) |
| Fig 8 | **Directional bias analysis** - Distribution of (predicted - reactive) by model |
| Fig 9 | Failure mode analysis |

---

## Experiment Matrix

| Experiment | Purpose | Games Needed |
|------------|---------|--------------|
| Same-model baselines | Establish shared-bias performance | 100/model |
| Cross-model pairs | True coordination test | 50/pair |
| **Prediction vs Reactive (same setup)** | **Test internal consistency** | **50/model** |
| **Prediction vs Reactive (cross-model)** | **Consistency under coordination stress** | **25/pair** |
| Memory ablation | Learning effect | 100 with/without |
| Player scaling | 2-6 players | 50/config |

**Priority order:**
1. GPT-4o vs GPT-4o (baseline) - **both prompting strategies**
2. **GPT-4o prediction vs reactive consistency analysis**
3. GPT-4o vs Claude 3.5 (cross-model)
4. All homogeneous baselines
5. **All models: prediction vs reactive consistency**
6. All heterogeneous pairs
7. Memory ablation
8. Player scaling

**Consistency Experiment Details:**
- Run identical game setups with both prompting strategies
- Compare predicted wait times to actual reactive play times
- Calculate consistency metrics for each model
- Analyze whether consistency varies by:
  - Card value (low/mid/high)
  - Game state (early/late in round)
  - Team composition (homogeneous/heterogeneous)

---

## Target Venues

1. **arXiv** - Immediate preprint
2. **AAAI/ICML Workshop on Multi-Agent Systems** - Ideal fit
3. **NeurIPS Datasets & Benchmarks** - Frame as coordination benchmark
4. **JAAMAS** - Full journal paper

---

## Jupyter Book Structure

```
paper/
├── _config.yml
├── _toc.yml
├── intro.md
├── chapters/
│   ├── 01_introduction.md
│   ├── 02_background.md
│   ├── 03_methodology.ipynb  # Executable
│   ├── 04_results.ipynb      # Live figures
│   ├── 05_discussion.md
│   └── 06_conclusion.md
├── data/
│   └── experiments/
├── figures/
└── references.bib
```

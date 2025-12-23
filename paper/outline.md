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
4. Can agents learn/adapt across rounds?
5. What emergent timing strategies arise?

**1.3 Contributions**
- First LLM simulation of The Mind card game
- Novel benchmark separating "shared bias" from "true coordination"
- Cross-model coordination analysis
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

*3.1.3 Models Under Study*
| Provider | Models |
|----------|--------|
| OpenAI | gpt-4o, gpt-4o-mini |
| Anthropic | claude-3.5-sonnet, claude-3-haiku |
| Google | gemini-1.5-pro, gemini-1.5-flash |

*3.1.4 Experimental Conditions*
- **Homogeneous teams** (baseline - expected high due to shared bias)
- **Heterogeneous teams** (true coordination test)
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

**4.4 Model Rankings**
- Performance hierarchy
- Which models adapt best to others?

---

### 5. Discussion (2-3 pages)

**5.1 The Shared Bias Problem**
- Same-model coordination may overestimate LLM abilities
- Cross-model experiments as more valid benchmark
- Implications for multi-agent system design

**5.2 Emergent Strategies**
- Linear timing was not explicitly taught
- Robustness of emergent conventions

**5.3 Theory of Mind Implications**
- Evidence for/against ToM in timing decisions
- Comparison to Hanabi research

**5.4 Limitations**
- API determinism challenges
- Limited model diversity
- Simulated timing vs real-time

---

### 6. Conclusion (1 page)
- First LLM simulation of The Mind
- Same-model coordination ≠ true coordination ability
- Cross-model adaptation as better benchmark
- Future work: human-AI teams, real-time APIs

---

## Required Figures

| Figure | Description |
|--------|-------------|
| Fig 1 | The Mind game mechanics diagram |
| Fig 2 | Same-model vs cross-model success rates (KEY FIGURE) |
| Fig 3 | Timing strategy scatter: wait_time vs card_value by model |
| Fig 4 | Adaptation curves: cross-model performance over rounds |
| Fig 5 | Model pair heatmap: success rates for all combinations |
| Fig 6 | Failure mode analysis |

---

## Experiment Matrix

| Experiment | Purpose | Games Needed |
|------------|---------|--------------|
| Same-model baselines | Establish shared-bias performance | 100/model |
| Cross-model pairs | True coordination test | 50/pair |
| Memory ablation | Learning effect | 100 with/without |
| Player scaling | 2-6 players | 50/config |

**Priority order:**
1. GPT-4o vs GPT-4o (baseline)
2. GPT-4o vs Claude 3.5 (cross-model)
3. All homogeneous baselines
4. All heterogeneous pairs
5. Memory ablation
6. Player scaling

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

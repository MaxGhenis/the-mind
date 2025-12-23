# The Mind: LLM Coordination Experiments

Comprehensive experiments testing whether LLM agents can coordinate without communication in The Mind card game.

## Quick Start

### 1. Setup

```bash
# Activate virtual environment
cd /Users/maxghenis/the-mind
source .venv/bin/activate

# Verify installation
python experiments/test_quick.py
```

### 2. Run Test Experiment (5 games per condition, ~10-15 minutes)

```bash
python experiments/comprehensive_experiment.py --test
```

### 3. Run Full Experiment (50+ games per condition, ~2-4 hours)

```bash
python experiments/comprehensive_experiment.py
```

### 4. Analyze Results

```bash
python experiments/analyze_results.py experiments/data/experiment_full_*.csv
```

## File Structure

```
experiments/
├── README.md                      # This file
├── SETUP.md                       # Detailed setup instructions
├── config.yaml                    # Experiment configuration
├── comprehensive_experiment.py    # Main experiment runner
├── analyze_results.py             # Analysis and visualization
├── test_quick.py                  # Quick API test
└── data/                          # Output directory
    ├── experiment_*.csv           # Raw data
    └── analysis/                  # Generated plots and tables
        ├── success_rates.png
        ├── learning_curves.png
        ├── team_composition.png
        ├── scaling.png
        ├── summary_table.csv
        └── statistical_tests.json
```

## Experiment Design

### Research Questions

1. **Can LLMs coordinate without communication?**
   - Baseline success rates for different models

2. **Does learning improve coordination?**
   - Compare performance with/without memory of previous rounds

3. **Do heterogeneous teams perform differently?**
   - Mixed models vs same model teams

4. **How does coordination scale?**
   - Performance vs team size (2, 3, 4 players)

5. **How does model temperature affect coordination?**
   - Test different temperature settings

### Experimental Conditions

The experiment matrix includes:

- **5 models**: GPT-4o, GPT-4o-mini, Claude Sonnet 4.5, Gemini 2.5 Pro, Gemini 2.5 Flash
- **Memory**: With/without learning from previous rounds
- **Team composition**: Homogeneous (same model) vs heterogeneous (mixed)
- **Team size**: 2, 3, 4 players
- **Temperature**: 0.3, 0.7, 1.0
- **Games per condition**: 50 for main conditions, 30 for exploratory

**Total**: ~760 games across all conditions

### Data Collection

Each game generates detailed data:
- Card sequences played
- Decision times for each player
- Success/failure per round
- Final game outcome
- Model configuration
- Learning history (if enabled)

### Metrics

- **Game Success Rate**: % of games won (reaching target rounds with lives remaining)
- **Round Success Rate**: % of individual rounds completed successfully
- **Average Rounds Completed**: Mean number of rounds before losing all lives
- **Coordination Efficiency**: Quality of timing decisions
- **Learning Improvement**: Change in performance over time (for memory-enabled conditions)

## API Keys and Costs

### Required Keys

Set in `.env` file (see `SETUP.md`):
- `OPENAI_API_KEY` - For GPT-4o, GPT-4o-mini
- `ANTHROPIC_API_KEY` - For Claude Sonnet 4.5
- `GOOGLE_API_KEY` - For Gemini models

### Cost Estimates

Full experiment (~760 games):
- GPT-4o-mini: ~$2-3
- GPT-4o: ~$10-15
- Claude Sonnet 4.5: ~$5-8
- Gemini Flash/Pro: ~$1-2 (may be free tier)

**Total: $20-30**

Test run (5 games/condition): ~$1-2

## Data Output

### CSV Format

Experiments generate CSV files with columns:
- `game_id`: Unique identifier
- `timestamp`: When game was played
- `experiment`: Condition name
- `use_memory`: Memory enabled (bool)
- `temperature`: Model temperature
- `num_players`: Team size
- `round_number`: Round within game
- `success`: Round success (bool)
- `final_success`: Game success (bool)
- `cards_played`: JSON array of card sequence
- `correct_order`: JSON array of correct sequence
- `time_taken`: Seconds for round
- `model_config`: JSON mapping players to models
- `homogeneous`: All same model (bool)

### Analysis Output

Analysis generates:
1. **Plots** (PNG, 300 DPI):
   - Success rates by condition
   - Learning curves over time
   - Homogeneous vs heterogeneous comparison
   - Scaling analysis (team size)

2. **Tables** (CSV):
   - Summary statistics
   - Per-condition metrics

3. **Statistical Tests** (JSON):
   - T-tests for learning effect
   - Team composition comparisons
   - Significance levels (p-values)

## Customization

### Modify Number of Games

Edit in `comprehensive_experiment.py`:
```python
# In create_experiment_conditions()
conditions.append(ExperimentCondition(
    name="baseline_3p_gpt4o",
    models=["gpt-4o"] * 3,
    num_players=3,
    use_memory=False,
    num_games=100  # Change this
))
```

### Add New Conditions

Add to `create_experiment_conditions()`:
```python
conditions.append(ExperimentCondition(
    name="my_custom_condition",
    models=["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-5-20250929"],
    num_players=3,
    use_memory=True,
    temperature=0.5,
    num_games=50
))
```

### Run Single Condition

```python
from experiments.comprehensive_experiment import TheMindExperiment, ExperimentCondition

experiment = TheMindExperiment()

condition = ExperimentCondition(
    name="test_condition",
    models=["gemini-2.5-flash"] * 3,
    num_players=3,
    use_memory=False,
    num_games=10
)

results = experiment.run_condition(condition)
experiment.save_results("experiments/data/my_test.csv")
```

## Troubleshooting

### API Rate Limits

If hitting rate limits:
1. Reduce `num_games` in conditions
2. Add sleep delays between games
3. Use cheaper models (Gemini Flash, GPT-4o-mini)

### Memory Errors

If running out of memory:
1. Process conditions separately
2. Clear results between batches
3. Use test mode (--test flag)

### Model Not Found

Check available models:
```python
from edsl import Model
print(Model.available())
```

Update model names in `comprehensive_experiment.py` to match available names.

## Citation

If using this experiment infrastructure for research:

```bibtex
@software{themind_llm_experiments,
  title={The Mind: LLM Coordination Experiments},
  author={Ghenis, Max},
  year={2025},
  url={https://github.com/maxghenis/the-mind}
}
```

## Support

For issues:
1. Check `SETUP.md` for detailed configuration
2. Verify API keys are set correctly in `.env`
3. Test with `test_quick.py` first
4. Use `--test` flag for debugging

## Next Steps

After running experiments:
1. **Analyze results**: Use `analyze_results.py`
2. **Generate paper figures**: Plots are publication-ready (300 DPI PNG)
3. **Statistical analysis**: Check `statistical_tests.json` for significance
4. **Iterate**: Adjust conditions based on findings
5. **Scale up**: Increase games per condition for more statistical power

---

**Current Status**: ✅ Infrastructure ready, API keys configured, test validated

**Ready to run**: `python experiments/comprehensive_experiment.py --test`

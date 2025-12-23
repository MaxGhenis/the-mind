# Experiment Setup Guide

This guide explains how to set up and run comprehensive LLM coordination experiments for The Mind research project.

## Prerequisites

### 1. Python Environment

Ensure you have Python 3.9+ installed and the virtual environment activated:

```bash
cd /Users/maxghenis/the-mind
source .venv/bin/activate
```

### 2. Install Dependencies

The required packages should already be installed. If not:

```bash
pip install -e ".[dev,analysis,paper]"
```

## API Key Configuration

You'll need API keys for the LLM providers you want to test. The experiments use EDSL (Expected DSL) which provides a unified interface to multiple LLM providers.

### Required Environment Variables

Create or update your `.env` file in the project root:

```bash
# /Users/maxghenis/the-mind/.env

# OpenAI (for GPT-4o, GPT-4o-mini)
OPENAI_API_KEY=sk-proj-...

# Anthropic (for Claude 3.5 Sonnet)
ANTHROPIC_API_KEY=sk-ant-...

# Google (for Gemini 1.5 Pro, Gemini 1.5 Flash)
GOOGLE_API_KEY=AIzaSy...

# Expected Parrot (unified API - if using)
EXPECTED_PARROT_API_KEY=...
```

### Getting API Keys

1. **OpenAI**: https://platform.openai.com/api-keys
   - Sign up/login
   - Create new API key
   - Add credits to your account ($10-20 recommended)

2. **Anthropic**: https://console.anthropic.com/settings/keys
   - Sign up/login
   - Generate API key
   - Add credits ($10-20 recommended)

3. **Google AI**: https://makersuite.google.com/app/apikey
   - Sign up/login with Google account
   - Create API key
   - Free tier available, but may have rate limits

### Current API Key Status

Based on your environment:
- ✅ **OPENAI_API_KEY**: Configured
- ✅ **ANTHROPIC_API_KEY**: Configured
- ✅ **GOOGLE_API_KEY**: Configured (AIzaSyBimA7Xh0lRJKblUYY4dhStD31hVCV3TrQ)

## Running Experiments

### Quick Test Run

First, validate the setup with a small test:

```bash
cd /Users/maxghenis/the-mind
source .venv/bin/activate

python experiments/comprehensive_experiment.py --test
```

This runs 5 games per condition (should complete in 10-20 minutes).

### Full Experiment Suite

Once the test succeeds, run the full experiment:

```bash
python experiments/comprehensive_experiment.py
```

This runs 50-100 games per condition and may take several hours. Expected duration: 2-4 hours depending on API speed.

### Cost Estimation

Approximate costs (based on ~50 games per condition, 8 conditions):
- GPT-4o-mini: ~$2-3
- GPT-4o: ~$10-15
- Claude 3.5 Sonnet: ~$5-8
- Gemini (Flash/Pro): ~$1-2 (may be free tier)

**Total estimated cost: $20-30** for full experiment suite.

## Experiment Conditions

The comprehensive experiment tests:

1. **Baseline Homogeneous** (no memory)
   - GPT-4o x3, GPT-4o-mini x3, Claude x3, Gemini Pro x3, Gemini Flash x3
   - 50 games each = 250 games

2. **Learning Homogeneous** (with memory)
   - Same models as baseline
   - 50 games each = 250 games

3. **Heterogeneous Teams** (mixed models, no memory)
   - GPT-4o + GPT-4o-mini + Claude
   - 50 games

4. **Heterogeneous Learning** (mixed models, with memory)
   - Same mix as above
   - 50 games

5. **Scaling** (different team sizes)
   - 2 players, 4 players
   - 50 games each = 100 games

6. **Temperature Variation**
   - T=0.3, T=1.0
   - 30 games each = 60 games

**Total: ~760 games**

## Output Files

Results are saved to `experiments/data/`:

- `experiment_full_YYYYMMDD_HHMMSS.csv` - Full dataset with all games
- Contains columns:
  - `game_id`: Unique game identifier
  - `experiment`: Condition name
  - `num_players`: Team size
  - `use_memory`: Learning enabled?
  - `model_config`: JSON mapping players to models
  - `round_number`: Round within game
  - `success`: Did round succeed?
  - `final_success`: Did game succeed?
  - `cards_played`: Sequence of cards played
  - `correct_order`: Correct sequence
  - `homogeneous`: All players same model?

## Analyzing Results

After experiments complete:

```bash
python experiments/analyze_results.py experiments/data/experiment_full_*.csv
```

This generates:
- Statistical summaries
- Plots and visualizations
- Significance tests
- Publication-ready tables

## Troubleshooting

### API Rate Limits

If you hit rate limits:
1. Add delays between requests (modify `time.sleep()` in script)
2. Run conditions separately
3. Use lower-tier models (Gemini Flash, GPT-4o-mini)

### Out of Memory Errors

If you get OOM errors:
1. Reduce `num_games` in configuration
2. Run conditions one at a time
3. Clear `csv_data` between conditions

### API Key Errors

If you see authentication errors:
1. Check `.env` file exists and has correct keys
2. Verify keys are valid (test in provider console)
3. Check key has credits/quota remaining
4. For EDSL, run: `edsl config` to verify setup

### Model Not Available

If a model isn't found:
1. Check model name spelling (use `edsl models list`)
2. Verify API key for that provider
3. Check if model is in beta/limited access
4. Use alternative model from same provider

## Next Steps

1. **Run test experiment** to validate setup
2. **Review test results** to ensure quality
3. **Run full experiment** (set aside 3-4 hours)
4. **Analyze results** using analysis scripts
5. **Generate paper figures** from analysis

## Support

For issues:
1. Check error messages carefully
2. Verify API keys and quotas
3. Test with smaller `num_games` first
4. Check EDSL documentation: https://docs.expectedparrot.com/

## Configuration Files

- `experiments/config.yaml` - Experiment parameters
- `experiments/comprehensive_experiment.py` - Main runner
- `.env` - API keys (DO NOT COMMIT)

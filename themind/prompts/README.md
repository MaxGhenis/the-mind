# Prompting Strategies for The Mind

This directory contains different prompting strategies for LLM players in The Mind game.

## Reactive Prompting (`reactive.py`)

The reactive prompting strategy simulates time passing and asks the LLM at each timestep: "Do you play now?"

### How It Works

1. **Timestep Simulation**: The player simulates time passing in discrete intervals (default: 0.5 seconds)
2. **Repeated Queries**: At each timestep, the LLM is asked whether to play the card NOW
3. **Decision Format**: LLM responds with `{"play": true/false, "reasoning": "..."}`
4. **Termination**: Process stops when LLM says "play" or max time is reached

### Comparison to Predictive Strategy

**Predictive Strategy** (default `LLMPlayer`):
- Asks once: "How long will you wait?"
- 1 API call per decision
- More efficient but less realistic

**Reactive Strategy** (`ReactiveLLMPlayer`):
- Asks repeatedly: "Do you play now?"
- Multiple API calls per decision (proportional to wait time / timestep)
- More expensive but closer to actual gameplay
- Allows LLM to react to passage of time

### Usage

```python
from themind.core.reactive_player import ReactiveLLMPlayer
from themind.models.llm_factory import LLMFactory

factory = LLMFactory()

# Create a reactive player
player = ReactiveLLMPlayer(
    name="ReactiveAI",
    model="gpt-4o-mini",
    client=factory.create_player("temp", "gpt-4o-mini").client,
    timestep_interval=0.5,  # Check every 0.5 seconds
    max_time=30.0,  # Maximum wait time
    use_memory=True  # Enable learning from previous rounds
)

# Use in a game
game_state = GameState(...)
decision = await player.decide(game_state)

print(f"Decided to play after {decision.elapsed_time}s")
print(f"API calls made: {decision.timesteps_checked}")
print(f"Reasoning: {decision.reasoning}")
```

### Configuration Parameters

- `timestep_interval` (float): Seconds between decision checks (default: 0.5)
  - Smaller = more granular but more expensive
  - Larger = cheaper but less precise
- `max_time` (float): Maximum wait time before forcing play (default: 30.0)
- `use_memory` (bool): Whether to learn from previous rounds
- `temperature` (float): LLM temperature parameter

### Cost Considerations

The reactive strategy is significantly more expensive:
- Predictive: 1 API call per decision
- Reactive: ~(wait_time / timestep_interval) calls per decision

For a card that waits 10 seconds with 0.5s timestep:
- Predictive: 1 call
- Reactive: ~20 calls

See `experiments/compare_strategies.py` for detailed cost comparisons.

## Comparing Strategies

Use the provided comparison script:

```bash
# Compare strategies on test scenarios
python experiments/compare_strategies.py --model gpt-4o-mini --timestep 0.5

# Run with different parameters
python experiments/compare_strategies.py \
    --model gpt-4o-mini \
    --timestep 1.0 \
    --max-time 20.0 \
    --scenarios 5

# Output saved to experiments/data/strategy_comparison.json
```

The comparison shows:
- Decision consistency (how similar are wait times?)
- API call efficiency (how many more calls?)
- Estimated costs (how much more expensive?)

"""Run experiments for The Mind research paper."""

import asyncio
import os
from dotenv import load_dotenv
from themind.experiments.runner import ExperimentRunner, ExperimentConfig

# Load environment variables
load_dotenv()


async def main():
    """Run main experiments."""
    runner = ExperimentRunner()
    
    # Check for OpenAI API key (minimum requirement)
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in .env file")
        return
    
    # Use models available with OpenAI
    models = ["gpt-3.5-turbo", "gpt-4o-mini"]
    
    configs = []
    
    # Small test experiments (adjust num_games to 100+ for paper)
    num_games = 5  # Use 100+ for statistical significance
    
    # Experiment 1: Baseline - homogeneous teams without memory
    for model in models:
        configs.append(ExperimentConfig(
            name=f"baseline_{model}",
            models=[model],
            num_players=3,
            num_games=num_games,
            use_memory=False,
            temperature=0.7,
            seed=42
        ))
    
    # Experiment 2: Learning - homogeneous teams with memory
    for model in models:
        configs.append(ExperimentConfig(
            name=f"learning_{model}",
            models=[model],
            num_players=3,
            num_games=num_games,
            use_memory=True,
            temperature=0.7,
            seed=42
        ))
    
    # Experiment 3: Mixed teams
    configs.append(ExperimentConfig(
        name="mixed_team",
        models=models,
        num_players=3,
        num_games=num_games,
        use_memory=False,
        temperature=0.7,
        seed=42
    ))
    
    # Experiment 4: Temperature variation
    for temp in [0.3, 0.7, 1.0]:
        configs.append(ExperimentConfig(
            name=f"temperature_{temp}",
            models=["gpt-3.5-turbo"],
            num_players=3,
            num_games=num_games,
            use_memory=False,
            temperature=temp,
            seed=42
        ))
    
    # Run all experiments
    results = await runner.run_experiments(configs)
    
    print(f"\nCompleted {len(results)} experiments")
    print("Data saved to experiments/data/")


if __name__ == "__main__":
    asyncio.run(main())
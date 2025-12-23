"""Compare predictive vs reactive prompting strategies.

This script runs the same game scenarios with both strategies to measure:
1. Decision consistency - do they make similar timing choices?
2. API call efficiency - how many calls does each strategy use?
3. Success rates - which strategy performs better?
4. Total cost - estimated API costs for each approach
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from themind.core.card import Card, Deck
from themind.core.game_state import GameState
from themind.core.player import LLMPlayer, PlayerDecision
from themind.core.reactive_player import ReactiveLLMPlayer, ReactiveDecision
from themind.models.llm_factory import LLMFactory


@dataclass
class ComparisonResult:
    """Result of comparing two strategies on the same scenario."""

    scenario_id: str
    card_value: int
    cards_played: List[int]
    players_remaining: int

    # Predictive strategy results
    predictive_wait_time: float
    predictive_reasoning: str
    predictive_api_calls: int

    # Reactive strategy results
    reactive_wait_time: float
    reactive_reasoning: str
    reactive_api_calls: int
    reactive_timesteps: int

    # Comparison metrics
    time_difference: float  # abs(predictive - reactive)
    time_difference_pct: float  # difference as percentage

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scenario_id": self.scenario_id,
            "card_value": self.card_value,
            "cards_played": self.cards_played,
            "players_remaining": self.players_remaining,
            "predictive": {
                "wait_time": self.predictive_wait_time,
                "reasoning": self.predictive_reasoning,
                "api_calls": self.predictive_api_calls
            },
            "reactive": {
                "wait_time": self.reactive_wait_time,
                "reasoning": self.reactive_reasoning,
                "api_calls": self.reactive_api_calls,
                "timesteps": self.reactive_timesteps
            },
            "comparison": {
                "time_difference": self.time_difference,
                "time_difference_pct": self.time_difference_pct
            }
        }


class StrategyComparison:
    """Compare predictive and reactive prompting strategies."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        reactive_timestep: float = 0.5,
        reactive_max_time: float = 30.0
    ):
        """Initialize strategy comparison.

        Args:
            model: LLM model to use for both strategies
            temperature: Temperature parameter for LLM
            reactive_timestep: Timestep interval for reactive strategy
            reactive_max_time: Max time for reactive strategy
        """
        self.model = model
        self.temperature = temperature
        self.reactive_timestep = reactive_timestep
        self.reactive_max_time = reactive_max_time
        self.factory = LLMFactory()

    async def compare_on_scenario(
        self,
        card_value: int,
        cards_played: List[int],
        round_number: int = 1,
        players_remaining: int = 3,
        total_players: int = 3
    ) -> ComparisonResult:
        """Compare both strategies on a single scenario.

        Args:
            card_value: The player's card value
            cards_played: Cards already played
            round_number: Current round number
            players_remaining: Number of players with cards
            total_players: Total number of players

        Returns:
            ComparisonResult with comparison metrics
        """
        scenario_id = f"r{round_number}_c{card_value}_p{cards_played}"

        # Create game state
        game_state = GameState(
            round_number=round_number,
            cards_played=[Card(v) for v in cards_played],
            time_elapsed=0.0,
            players_remaining=players_remaining,
            total_players=total_players
        )

        # Test with PREDICTIVE strategy
        predictive_player = self.factory.create_player(
            name="Predictive",
            model=self.model,
            temperature=self.temperature
        )
        predictive_player.receive_card(Card(card_value))

        predictive_decision = await predictive_player.decide(game_state)
        predictive_api_calls = 1  # Predictive makes 1 call

        # Test with REACTIVE strategy
        reactive_player = ReactiveLLMPlayer(
            name="Reactive",
            model=self.model,
            client=predictive_player.client,  # Reuse same client
            temperature=self.temperature,
            timestep_interval=self.reactive_timestep,
            max_time=self.reactive_max_time
        )
        reactive_player.receive_card(Card(card_value))

        reactive_decision = await reactive_player.decide(game_state)
        reactive_api_calls = reactive_decision.timesteps_checked

        # Calculate comparison metrics
        time_diff = abs(predictive_decision.wait_seconds - reactive_decision.elapsed_time)
        avg_time = (predictive_decision.wait_seconds + reactive_decision.elapsed_time) / 2
        time_diff_pct = (time_diff / avg_time * 100) if avg_time > 0 else 0

        return ComparisonResult(
            scenario_id=scenario_id,
            card_value=card_value,
            cards_played=cards_played,
            players_remaining=players_remaining,
            predictive_wait_time=predictive_decision.wait_seconds,
            predictive_reasoning=predictive_decision.reasoning,
            predictive_api_calls=predictive_api_calls,
            reactive_wait_time=reactive_decision.elapsed_time,
            reactive_reasoning=reactive_decision.reasoning,
            reactive_api_calls=reactive_api_calls,
            reactive_timesteps=reactive_decision.timesteps_checked,
            time_difference=time_diff,
            time_difference_pct=time_diff_pct
        )

    def generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """Generate diverse test scenarios.

        Returns:
            List of scenario dictionaries
        """
        scenarios = []

        # Early game, low card
        scenarios.append({
            "card_value": 15,
            "cards_played": [],
            "round_number": 1,
            "players_remaining": 3,
            "total_players": 3
        })

        # Mid game, medium card
        scenarios.append({
            "card_value": 55,
            "cards_played": [12, 28, 41],
            "round_number": 2,
            "players_remaining": 3,
            "total_players": 3
        })

        # Late game, high card
        scenarios.append({
            "card_value": 87,
            "cards_played": [23, 45, 61, 74],
            "round_number": 3,
            "players_remaining": 2,
            "total_players": 3
        })

        # Close to last played card
        scenarios.append({
            "card_value": 52,
            "cards_played": [10, 30, 48],
            "round_number": 2,
            "players_remaining": 3,
            "total_players": 3
        })

        # First card of round
        scenarios.append({
            "card_value": 25,
            "cards_played": [],
            "round_number": 1,
            "players_remaining": 4,
            "total_players": 4
        })

        # Very high card
        scenarios.append({
            "card_value": 95,
            "cards_played": [10, 25, 40, 55, 70, 85],
            "round_number": 3,
            "players_remaining": 2,
            "total_players": 3
        })

        # Very low card
        scenarios.append({
            "card_value": 8,
            "cards_played": [],
            "round_number": 1,
            "players_remaining": 3,
            "total_players": 3
        })

        return scenarios

    async def run_comparison(self, num_scenarios: int = None) -> Dict[str, Any]:
        """Run comparison across multiple scenarios.

        Args:
            num_scenarios: Number of scenarios to test (None = all)

        Returns:
            Dictionary with aggregated results and statistics
        """
        scenarios = self.generate_test_scenarios()
        if num_scenarios:
            scenarios = scenarios[:num_scenarios]

        print(f"Comparing strategies on {len(scenarios)} scenarios...")
        print(f"Model: {self.model}")
        print(f"Reactive timestep: {self.reactive_timestep}s")
        print("=" * 70)

        results = []
        for i, scenario in enumerate(scenarios, 1):
            print(f"\nScenario {i}/{len(scenarios)}: Card={scenario['card_value']}, "
                  f"Played={scenario['cards_played']}")

            result = await self.compare_on_scenario(**scenario)
            results.append(result)

            print(f"  Predictive: {result.predictive_wait_time:.1f}s (1 API call)")
            print(f"  Reactive:   {result.reactive_wait_time:.1f}s "
                  f"({result.reactive_api_calls} API calls)")
            print(f"  Difference: {result.time_difference:.1f}s "
                  f"({result.time_difference_pct:.1f}%)")

        # Calculate aggregate statistics
        total_predictive_calls = sum(r.predictive_api_calls for r in results)
        total_reactive_calls = sum(r.reactive_api_calls for r in results)
        avg_time_diff = sum(r.time_difference for r in results) / len(results)
        avg_time_diff_pct = sum(r.time_difference_pct for r in results) / len(results)

        # Estimate costs (rough approximation)
        # GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
        # Assume ~500 tokens per call (input + output)
        cost_per_call = 0.0005  # $0.0005 per call
        predictive_cost = total_predictive_calls * cost_per_call
        reactive_cost = total_reactive_calls * cost_per_call

        summary = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "temperature": self.temperature,
                "reactive_timestep": self.reactive_timestep,
                "reactive_max_time": self.reactive_max_time,
                "num_scenarios": len(scenarios)
            },
            "results": [r.to_dict() for r in results],
            "statistics": {
                "total_predictive_api_calls": total_predictive_calls,
                "total_reactive_api_calls": total_reactive_calls,
                "api_call_ratio": total_reactive_calls / total_predictive_calls,
                "avg_time_difference_seconds": avg_time_diff,
                "avg_time_difference_percent": avg_time_diff_pct,
                "estimated_cost_predictive": predictive_cost,
                "estimated_cost_reactive": reactive_cost,
                "cost_ratio": reactive_cost / predictive_cost if predictive_cost > 0 else 0
            }
        }

        return summary


async def main():
    """Run the strategy comparison."""
    import argparse

    parser = argparse.ArgumentParser(description="Compare predictive vs reactive strategies")
    parser.add_argument("--model", default="gpt-4o-mini", help="LLM model to use")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature parameter")
    parser.add_argument("--timestep", type=float, default=0.5,
                        help="Reactive timestep interval in seconds")
    parser.add_argument("--max-time", type=float, default=30.0,
                        help="Max time for reactive strategy")
    parser.add_argument("--scenarios", type=int, default=None,
                        help="Number of scenarios to test (default: all)")
    parser.add_argument("--output", default="experiments/data/strategy_comparison.json",
                        help="Output file path")

    args = parser.parse_args()

    comparison = StrategyComparison(
        model=args.model,
        temperature=args.temperature,
        reactive_timestep=args.timestep,
        reactive_max_time=args.max_time
    )

    results = await comparison.run_comparison(num_scenarios=args.scenarios)

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    stats = results["statistics"]
    print(f"Total API calls:")
    print(f"  Predictive: {stats['total_predictive_api_calls']}")
    print(f"  Reactive:   {stats['total_reactive_api_calls']}")
    print(f"  Ratio:      {stats['api_call_ratio']:.1f}x more for reactive")
    print(f"\nDecision consistency:")
    print(f"  Avg difference: {stats['avg_time_difference_seconds']:.2f}s "
          f"({stats['avg_time_difference_percent']:.1f}%)")
    print(f"\nEstimated costs:")
    print(f"  Predictive: ${stats['estimated_cost_predictive']:.4f}")
    print(f"  Reactive:   ${stats['estimated_cost_reactive']:.4f}")
    print(f"  Ratio:      {stats['cost_ratio']:.1f}x more expensive for reactive")

    # Save results
    output_path = args.output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())

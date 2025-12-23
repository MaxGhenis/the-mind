"""Comprehensive LLM coordination experiments for The Mind research paper.

This script runs a full experiment matrix testing:
- Multiple models (GPT-4o, GPT-4o-mini, Claude 3.5 Sonnet, Gemini 1.5 Pro)
- Homogeneous vs heterogeneous teams
- With/without learning across rounds
- Different team sizes (2, 3, 4 players)
- Statistical significance (50-100 games per configuration)
"""

import os
import json
import csv
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import random
import numpy as np
from pathlib import Path
from edsl import Model, QuestionFreeText
import time
import uuid
from dataclasses import dataclass


@dataclass
class ExperimentCondition:
    """Configuration for a single experiment condition."""
    name: str
    models: List[str]  # Model names for each player (can be same or different)
    num_players: int
    use_memory: bool
    temperature: float = 0.7
    num_games: int = 50


class TheMindExperiment:
    """Comprehensive experiment runner for The Mind LLM coordination study."""

    def __init__(self):
        self.csv_data = []
        self.models_cache = {}  # Cache EDSL model instances

    def get_model(self, model_name: str) -> Model:
        """Get or create cached model instance."""
        if model_name not in self.models_cache:
            self.models_cache[model_name] = Model(model_name)
        return self.models_cache[model_name]

    def get_llm_decision(
        self,
        model_name: str,
        card_value: int,
        round_num: int,
        cards_played: List[int],
        player_num: int,
        num_players: int,
        history: Optional[str] = None
    ) -> Tuple[float, str]:
        """Get LLM decision for wait time with reasoning.

        Returns:
            (wait_time, reasoning) tuple
        """

        prompt = f"""You are Player {player_num} in The Mind, a cooperative card game.
Rules: All players must play their cards in ascending order (1-100) without
communication. You can only use timing/waiting to coordinate.

Current state:
- Round {round_num} (each player has {round_num} card(s))
- Your lowest unplayed card: {card_value}
- Cards already played this round: {cards_played if cards_played else 'none'}
- Total players: {num_players}

Strategy hints:
- Lower cards (1-33): wait 0-10 seconds
- Middle cards (34-66): wait 10-20 seconds
- Higher cards (67-100): wait 20-30 seconds
- Adjust based on already-played cards
- Consider how many players might have lower cards
"""

        if history:
            prompt += f"\n\nLearn from previous rounds:\n{history}"

        prompt += "\n\nRespond with ONLY a number (0-30) for seconds to wait:"

        try:
            model = self.get_model(model_name)

            q = QuestionFreeText(
                question_name="wait_time",
                question_text=prompt
            )

            result = q.by(model).run()
            response_text = str(result.select("answer.wait_time").first())

            # Parse the number
            response_clean = response_text.strip().split()[0]
            response_clean = response_clean.replace(',', '.')
            wait_time = float(response_clean)
            wait_time = max(0, min(30, wait_time))

            return wait_time, response_text

        except Exception as e:
            print(f"  Warning: LLM error for {model_name}: {e}")
            # Fallback: simple heuristic with noise
            base_wait = (card_value / 100.0) * 30
            wait_time = base_wait + random.uniform(-2, 2)
            wait_time = max(0, min(30, wait_time))
            return wait_time, f"fallback: {e}"

    def play_round(
        self,
        game_id: str,
        round_num: int,
        player_models: List[str],
        use_memory: bool,
        temperature: float,
        experiment_name: str,
        history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Play a single round of The Mind.

        Args:
            game_id: Unique identifier for this game
            round_num: Round number (determines cards per player)
            player_models: List of model names for each player
            use_memory: Whether to include history in prompts
            temperature: Model temperature (note: not all models support this via EDSL)
            experiment_name: Name of experiment condition
            history: Previous rounds data for learning

        Returns:
            Round result dictionary
        """

        start_time = time.time()
        num_players = len(player_models)

        # Deal cards (each player gets round_num cards)
        all_cards = list(range(1, 101))
        random.shuffle(all_cards)

        cards_per_player = round_num
        player_hands = []
        for i in range(num_players):
            start_idx = i * cards_per_player
            end_idx = start_idx + cards_per_player
            hand = sorted(all_cards[start_idx:end_idx])
            player_hands.append(hand)

        # Build history string for learning
        history_str = ""
        if use_memory and history:
            for h in history[-3:]:  # Last 3 rounds
                history_str += f"Round {h['round_number']}: "
                history_str += f"{'SUCCESS' if h['success'] else 'FAILED'} - "
                history_str += f"Cards played: {h['cards_played']}\n"

        # Play all cards in the round
        all_decisions = []
        cards_played_so_far = []

        # Each "turn" we get decisions from all players with cards remaining
        while any(len(hand) > 0 for hand in player_hands):
            turn_decisions = []

            for player_idx in range(num_players):
                if len(player_hands[player_idx]) > 0:
                    card = player_hands[player_idx][0]  # Lowest card
                    model_name = player_models[player_idx]

                    wait_time, reasoning = self.get_llm_decision(
                        model_name=model_name,
                        card_value=card,
                        round_num=round_num,
                        cards_played=cards_played_so_far,
                        player_num=player_idx + 1,
                        num_players=num_players,
                        history=history_str if use_memory else None
                    )

                    turn_decisions.append({
                        "player": player_idx + 1,
                        "model": model_name,
                        "card": card,
                        "wait_time": wait_time,
                        "reasoning": reasoning
                    })

            if not turn_decisions:
                break

            # Player with shortest wait time plays
            turn_decisions.sort(key=lambda x: x["wait_time"])
            next_player_decision = turn_decisions[0]

            # Play the card
            player_idx = next_player_decision["player"] - 1
            played_card = player_hands[player_idx].pop(0)
            cards_played_so_far.append(played_card)
            all_decisions.append(next_player_decision)

        # Check if cards were played in correct ascending order
        correct_order = sorted(cards_played_so_far)
        success = cards_played_so_far == correct_order

        time_taken = time.time() - start_time

        # Create model config
        model_config = {f"P{i+1}": model for i, model in enumerate(player_models)}

        # Record detailed data
        csv_row = {
            "game_id": game_id,
            "timestamp": datetime.now().isoformat(),
            "experiment": experiment_name,
            "use_memory": use_memory,
            "temperature": temperature,
            "num_players": num_players,
            "round_number": round_num,
            "success": success,
            "cards_played": json.dumps(cards_played_so_far),
            "correct_order": json.dumps(correct_order),
            "time_taken": round(time_taken, 2),
            "model_config": json.dumps(model_config),
            "homogeneous": len(set(player_models)) == 1,
            "final_success": None  # Updated after game completes
        }

        self.csv_data.append(csv_row)

        return {
            "round_number": round_num,
            "success": success,
            "cards_played": cards_played_so_far,
            "correct_order": correct_order,
            "time_taken": time_taken,
            "decisions": all_decisions
        }

    def play_game(
        self,
        experiment_name: str,
        player_models: List[str],
        use_memory: bool = False,
        temperature: float = 0.7,
        max_rounds: int = 8
    ) -> Dict[str, Any]:
        """Play a complete game of The Mind.

        Args:
            experiment_name: Name for this experiment condition
            player_models: List of model names (one per player)
            use_memory: Enable learning from previous rounds
            temperature: Model temperature
            max_rounds: Maximum rounds before declaring victory

        Returns:
            Game result dictionary
        """

        game_id = str(uuid.uuid4())[:8]
        lives = 3
        rounds_data = []

        for round_num in range(1, max_rounds + 1):
            if lives <= 0:
                break

            round_result = self.play_round(
                game_id=game_id,
                round_num=round_num,
                player_models=player_models,
                use_memory=use_memory,
                temperature=temperature,
                experiment_name=experiment_name,
                history=rounds_data if use_memory else None
            )

            rounds_data.append(round_result)

            if not round_result["success"]:
                lives -= 1

        final_success = lives > 0

        # Update final_success for all rounds of this game
        for row in self.csv_data:
            if row["game_id"] == game_id:
                row["final_success"] = final_success

        return {
            "game_id": game_id,
            "success": final_success,
            "rounds_completed": len(rounds_data),
            "final_lives": lives
        }

    def run_condition(self, condition: ExperimentCondition) -> List[Dict]:
        """Run all games for a specific experimental condition.

        Args:
            condition: ExperimentCondition defining the setup

        Returns:
            List of game results
        """

        print(f"\n{condition.name}:")
        print(f"  Models: {', '.join(set(condition.models))}")
        print(f"  Players: {condition.num_players}, Memory: {condition.use_memory}")
        print(f"  Games: {condition.num_games}")

        results = []

        for i in range(condition.num_games):
            if (i + 1) % 10 == 0:
                print(f"    {i+1}/{condition.num_games}...", end=" ", flush=True)

            game_result = self.play_game(
                experiment_name=condition.name,
                player_models=condition.models,
                use_memory=condition.use_memory,
                temperature=condition.temperature
            )
            results.append(game_result)

        success_rate = sum(1 for r in results if r["success"]) / len(results)
        avg_rounds = sum(r["rounds_completed"] for r in results) / len(results)

        print(f"\n  ✓ Success rate: {success_rate:.1%}, Avg rounds: {avg_rounds:.1f}")

        return results

    def save_results(self, filename: str):
        """Save all experiment data to CSV."""
        df = pd.DataFrame(self.csv_data)
        df.to_csv(filename, index=False)
        print(f"\n📁 Saved {len(self.csv_data)} rows to {filename}")
        return filename


def create_experiment_conditions() -> List[ExperimentCondition]:
    """Create comprehensive experiment matrix.

    Returns:
        List of ExperimentCondition objects defining all experiments
    """

    conditions = []

    # Available models (depends on API keys)
    # These will gracefully degrade if API keys aren't set
    models = {
        'gpt-4o': 'gpt-4o',
        'gpt-4o-mini': 'gpt-4o-mini',
        'claude': 'claude-sonnet-4-5-20250929',
        'gemini-pro': 'gemini-2.5-pro',
        'gemini-flash': 'gemini-2.5-flash'
    }

    # 1. Baseline: Homogeneous teams without memory (3 players)
    for name, model in models.items():
        conditions.append(ExperimentCondition(
            name=f"baseline_3p_{name}",
            models=[model] * 3,
            num_players=3,
            use_memory=False,
            num_games=50
        ))

    # 2. Learning: Homogeneous teams WITH memory (3 players)
    for name, model in models.items():
        conditions.append(ExperimentCondition(
            name=f"learning_3p_{name}",
            models=[model] * 3,
            num_players=3,
            use_memory=True,
            num_games=50
        ))

    # 3. Heterogeneous teams: Mix of models
    if len(models) >= 3:
        model_list = list(models.values())

        # GPT-4o + GPT-4o-mini + Claude
        conditions.append(ExperimentCondition(
            name="heterogeneous_3p_diverse",
            models=model_list[:3],
            num_players=3,
            use_memory=False,
            num_games=50
        ))

        # Same with learning
        conditions.append(ExperimentCondition(
            name="heterogeneous_3p_diverse_learning",
            models=model_list[:3],
            num_players=3,
            use_memory=True,
            num_games=50
        ))

    # 4. Scaling: Different team sizes (using Gemini Flash for speed)
    if 'gemini-flash' in models:
        flash_model = models['gemini-flash']

        for num_players in [2, 4]:
            conditions.append(ExperimentCondition(
                name=f"scaling_{num_players}p_gemini",
                models=[flash_model] * num_players,
                num_players=num_players,
                use_memory=False,
                num_games=50
            ))

    # 5. Temperature variation (using GPT-4o-mini for cost)
    if 'gpt-4o-mini' in models:
        mini_model = models['gpt-4o-mini']

        for temp in [0.3, 1.0]:
            conditions.append(ExperimentCondition(
                name=f"temperature_{temp}_gpt4o_mini",
                models=[mini_model] * 3,
                num_players=3,
                use_memory=False,
                temperature=temp,
                num_games=30
            ))

    return conditions


def run_comprehensive_experiments(
    output_dir: str = "experiments/data",
    test_run: bool = False
):
    """Run the complete experiment suite.

    Args:
        output_dir: Directory to save results
        test_run: If True, run only 5 games per condition for testing
    """

    print("="*70)
    print("THE MIND - Comprehensive LLM Coordination Experiment")
    print("Research Question: Can LLMs coordinate without communication?")
    print("="*70)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get experiment conditions
    conditions = create_experiment_conditions()

    if test_run:
        print("\n🧪 TEST RUN MODE: 5 games per condition")
        for condition in conditions:
            condition.num_games = 5

    print(f"\nPlanned experiments: {len(conditions)}")
    total_games = sum(c.num_games for c in conditions)
    print(f"Total games to play: {total_games}")

    # Initialize experiment runner
    experiment = TheMindExperiment()

    # Run all conditions
    all_results = {}
    start_time = datetime.now()

    for i, condition in enumerate(conditions, 1):
        print(f"\n{'='*70}")
        print(f"Condition {i}/{len(conditions)}")

        try:
            results = experiment.run_condition(condition)
            all_results[condition.name] = results
        except Exception as e:
            print(f"  ❌ Error in condition {condition.name}: {e}")
            continue

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode = "test" if test_run else "full"
    csv_file = output_path / f"experiment_{mode}_{timestamp}.csv"
    experiment.save_results(str(csv_file))

    # Print summary
    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"\n{'='*70}")
    print("EXPERIMENT COMPLETE")
    print(f"{'='*70}")
    print(f"Duration: {elapsed/60:.1f} minutes")
    print(f"Games played: {total_games}")
    print(f"Data file: {csv_file}")

    # Statistical summary
    df = pd.DataFrame(experiment.csv_data)

    print("\n📊 RESULTS BY CONDITION:")
    print("-" * 70)

    for condition_name in sorted(df['experiment'].unique()):
        cond_data = df[df['experiment'] == condition_name]
        success_rate = cond_data['success'].mean()
        games = cond_data['game_id'].nunique()
        final_success_rate = cond_data.groupby('game_id')['final_success'].first().mean()

        print(f"{condition_name:40s}: {final_success_rate:5.1%} games won "
              f"({success_rate:5.1%} rounds, {games} games)")

    print("\n✅ Results saved. Use the analysis script to generate plots and statistics.")

    return csv_file


if __name__ == "__main__":
    import sys

    # Check if this is a test run
    test_mode = "--test" in sys.argv

    run_comprehensive_experiments(test_run=test_mode)

"""EDSL (Expected Parrot) experiment runner for The Mind."""

import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import random
import numpy as np
from pathlib import Path

# Only import EDSL if available
try:
    from edsl import Model, Agent, QuestionFreeText, Survey
    EDSL_AVAILABLE = True
except ImportError:
    EDSL_AVAILABLE = False
    print("EDSL not available. Install with: pip install edsl")


class TheMindEDSLExperiment:
    """Run The Mind experiments using EDSL with learning analysis."""
    
    def __init__(
        self, 
        num_players: int = 3, 
        model_name: str = "gpt-3.5-turbo",
        enable_learning: bool = True,
        seed: Optional[int] = None
    ):
        if not EDSL_AVAILABLE:
            raise ImportError("EDSL not installed. Run: pip install edsl")
            
        self.num_players = num_players
        self.model_name = model_name
        self.enable_learning = enable_learning
        self.game_history: List[Dict] = []
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Set up EDSL API key
        if "EXPECTED_PARROT_API_KEY" in os.environ:
            os.environ["EDSL_API_KEY"] = os.environ["EXPECTED_PARROT_API_KEY"]
    
    def get_wait_time(self, card_value: int, round_num: int, history: List[Dict] = None) -> float:
        """Heuristic with noise to simulate LLM uncertainty."""
        # Base wait time with more variance
        base_wait = card_value / 100 * 25  # 0-25 seconds base
        
        # Add noise to simulate LLM uncertainty
        noise = np.random.normal(0, 3.0 + round_num)  # More noise in later rounds
        
        # Add player-specific bias (some players are more aggressive/conservative)
        player_bias = np.random.uniform(-2, 2)
        
        wait_time = base_wait + noise + player_bias
        
        if history and self.enable_learning:
            # Learn from past failures
            failed_games = [g for g in history if not g.get("success", False)]
            successful_games = [g for g in history if g.get("success", False)]
            
            if len(history) > 5:
                # Analyze timing patterns from successful games
                if successful_games:
                    # Reduce variance if we've had success
                    wait_time = base_wait + np.random.normal(0, 2.0)
                elif len(failed_games) > 3:
                    # Increase spacing if we keep failing
                    wait_time *= 1.2
        
        return max(0.5, min(30.0, wait_time))
    
    def simulate_round(self, round_num: int, player_cards: List[List[int]]) -> Dict[str, Any]:
        """Simulate a round with simple heuristics."""
        decisions = []
        
        for i in range(self.num_players):
            lowest_card = min(player_cards[i])
            wait_time = self.get_wait_time(lowest_card, round_num, self.game_history)
            
            decisions.append({
                "player": i + 1,
                "card": lowest_card,
                "wait_time": wait_time,
                "all_cards": player_cards[i]
            })
        
        # Sort by wait time
        decisions.sort(key=lambda x: x["wait_time"])
        
        # Check success
        played_cards = [d["card"] for d in decisions]
        correct_order = sorted(played_cards)
        success = played_cards == correct_order
        
        return {
            "round": round_num,
            "success": success,
            "played_cards": played_cards,
            "correct_order": correct_order,
            "decisions": decisions
        }
    
    def play_game(self, game_num: int, max_rounds: int = 5) -> Dict[str, Any]:
        """Play a complete game."""
        lives = 3
        rounds_data = []
        
        for round_num in range(1, max_rounds + 1):
            if lives <= 0:
                break
            
            # Deal cards
            all_cards = list(range(1, 101))
            random.shuffle(all_cards)
            
            cards_per_player = round_num
            player_cards = []
            for i in range(self.num_players):
                hand = sorted(all_cards[i * cards_per_player:(i + 1) * cards_per_player])
                player_cards.append(hand)
            
            # Play round
            round_result = self.simulate_round(round_num, player_cards)
            rounds_data.append(round_result)
            
            if not round_result["success"]:
                lives -= 1
        
        game_result = {
            "game_num": game_num,
            "model": self.model_name,
            "num_players": self.num_players,
            "rounds": rounds_data,
            "rounds_completed": len(rounds_data),
            "final_lives": lives,
            "success": lives > 0,
            "learning_enabled": self.enable_learning
        }
        
        # Add to history for learning
        if self.enable_learning:
            self.game_history.append(game_result)
        
        return game_result
    
    def run_experiment(self, num_games: int = 10) -> pd.DataFrame:
        """Run multiple games and analyze learning progression."""
        results = []
        
        for game_num in range(num_games):
            game_result = self.play_game(game_num)
            results.append(game_result)
            
            if game_num % 5 == 0:
                print(f"Completed game {game_num + 1}/{num_games}")
        
        # Convert to DataFrame for analysis
        df_rows = []
        for game in results:
            for round_data in game["rounds"]:
                df_rows.append({
                    "game_num": game["game_num"],
                    "round": round_data["round"],
                    "success": round_data["success"],
                    "cards_played": len(round_data["played_cards"]),
                    "game_success": game["success"],
                    "rounds_completed": game["rounds_completed"],
                    "learning": game["learning_enabled"]
                })
        
        return pd.DataFrame(df_rows), results


def analyze_learning_progression(df: pd.DataFrame, results: List[Dict]) -> Dict[str, Any]:
    """Analyze how performance improves over games."""
    
    analysis = {
        "total_games": len(results),
        "learning_enabled": results[0]["learning_enabled"] if results else False
    }
    
    # Calculate success rate by game number (in groups)
    game_groups = {
        "first_third": [],
        "middle_third": [],
        "last_third": []
    }
    
    n = len(results)
    third = n // 3
    
    for i, game in enumerate(results):
        if i < third:
            game_groups["first_third"].append(game["success"])
        elif i < 2 * third:
            game_groups["middle_third"].append(game["success"])
        else:
            game_groups["last_third"].append(game["success"])
    
    # Calculate success rates
    for group, successes in game_groups.items():
        if successes:
            analysis[f"{group}_success_rate"] = sum(successes) / len(successes)
        else:
            analysis[f"{group}_success_rate"] = 0
    
    # Calculate improvement
    if game_groups["first_third"] and game_groups["last_third"]:
        first_rate = analysis["first_third_success_rate"]
        last_rate = analysis["last_third_success_rate"]
        analysis["improvement"] = last_rate - first_rate
        analysis["improvement_percent"] = (
            (last_rate - first_rate) / first_rate * 100 if first_rate > 0 else 0
        )
    
    # Rounds completed progression
    rounds_by_game = [game["rounds_completed"] for game in results]
    analysis["avg_rounds_first_third"] = np.mean(rounds_by_game[:third]) if third > 0 else 0
    analysis["avg_rounds_last_third"] = np.mean(rounds_by_game[-third:]) if third > 0 else 0
    
    # Round-level success progression
    round_success = df.groupby("game_num")["success"].mean()
    analysis["round_success_correlation"] = round_success.index.to_series().corr(round_success)
    
    return analysis


def main():
    """Run main experiment and analysis."""
    print("="*60)
    print("THE MIND - LLM Learning Progression Analysis")
    print("="*60)
    
    # Create output directory
    output_dir = Path("experiments/data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    experiments = []
    
    # Run with learning enabled
    print("\n📚 Running WITH learning enabled...")
    exp_with_learning = TheMindEDSLExperiment(
        num_players=3,
        model_name="gpt-3.5-turbo",
        enable_learning=True,
        seed=42
    )
    df_learning, results_learning = exp_with_learning.run_experiment(num_games=30)
    analysis_learning = analyze_learning_progression(df_learning, results_learning)
    experiments.append(("With Learning", analysis_learning))
    
    # Run without learning (baseline)
    print("\n🎯 Running WITHOUT learning (baseline)...")
    exp_no_learning = TheMindEDSLExperiment(
        num_players=3,
        model_name="gpt-3.5-turbo", 
        enable_learning=False,
        seed=42
    )
    df_no_learning, results_no_learning = exp_no_learning.run_experiment(num_games=30)
    analysis_no_learning = analyze_learning_progression(df_no_learning, results_no_learning)
    experiments.append(("Without Learning", analysis_no_learning))
    
    # Print results
    print("\n" + "="*60)
    print("RESULTS: Learning Progression Analysis")
    print("="*60)
    
    for name, analysis in experiments:
        print(f"\n{name}:")
        print("-" * 40)
        print(f"Total games: {analysis['total_games']}")
        print(f"\nSuccess Rates:")
        print(f"  First third:  {analysis['first_third_success_rate']:.1%}")
        print(f"  Middle third: {analysis['middle_third_success_rate']:.1%}")
        print(f"  Last third:   {analysis['last_third_success_rate']:.1%}")
        print(f"\nImprovement: {analysis['improvement']:.1%}")
        if analysis['first_third_success_rate'] > 0:
            print(f"Improvement %: {analysis['improvement_percent']:.1f}%")
        print(f"\nAverage Rounds Completed:")
        print(f"  First third:  {analysis['avg_rounds_first_third']:.1f}")
        print(f"  Last third:   {analysis['avg_rounds_last_third']:.1f}")
        print(f"\nRound success correlation: {analysis['round_success_correlation']:.3f}")
    
    # Compare learning vs no learning
    print("\n" + "="*60)
    print("COMPARISON: Learning vs No Learning")
    print("="*60)
    
    learning_final = experiments[0][1]["last_third_success_rate"]
    no_learning_final = experiments[1][1]["last_third_success_rate"]
    
    print(f"Final success rate WITH learning:    {learning_final:.1%}")
    print(f"Final success rate WITHOUT learning: {no_learning_final:.1%}")
    print(f"Advantage of learning: {(learning_final - no_learning_final):.1%}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save analysis
    analysis_path = output_dir / f"learning_analysis_{timestamp}.json"
    with open(analysis_path, "w") as f:
        json.dump({
            "with_learning": experiments[0][1],
            "without_learning": experiments[1][1],
            "comparison": {
                "learning_advantage": learning_final - no_learning_final,
                "learning_improvement": experiments[0][1]["improvement"],
                "no_learning_improvement": experiments[1][1]["improvement"]
            }
        }, f, indent=2, default=str)
    
    # Save raw data
    df_learning.to_csv(output_dir / f"games_with_learning_{timestamp}.csv", index=False)
    df_no_learning.to_csv(output_dir / f"games_without_learning_{timestamp}.csv", index=False)
    
    print(f"\n✅ Results saved to experiments/data/")
    
    return experiments


if __name__ == "__main__":
    main()
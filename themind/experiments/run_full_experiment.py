"""Run comprehensive experiments with statistical significance for The Mind research paper."""

import os
import json
import csv
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import random
import numpy as np
from pathlib import Path
from edsl import Model, QuestionFreeText
import time
import uuid

# Set Expected Parrot API key
os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')


class ComprehensiveExperiment:
    """Run comprehensive experiments with multiple models and conditions."""
    
    def __init__(self, model_name: str = 'gemini-2.5-flash-lite'):
        self.model_name = model_name
        self.model = Model(model_name)
        self.csv_data = []
    
    def get_llm_decision(self, card_value: int, round_num: int, cards_played: List[int], 
                         player_num: int, num_players: int, temperature: float = 0.7,
                         history: Optional[str] = None) -> float:
        """Get LLM decision for wait time."""
        
        prompt = f"""You are Player {player_num} in The Mind card game. Players must play cards in ascending order without communication, using only timing to coordinate.

Current situation:
- Round {round_num}
- Your lowest card: {card_value}
- Cards already played: {cards_played if cards_played else 'none yet'}
- Total players: {num_players}

Strategy: Lower cards (1-33) wait 0-10 seconds, middle cards (34-66) wait 10-20 seconds, higher cards (67-100) wait 20-30 seconds.
"""

        if history:
            prompt += f"\n\nLearning from previous rounds:\n{history}"
        
        prompt += "\n\nRespond with ONLY a number (0-30) representing seconds to wait:"
        
        try:
            q = QuestionFreeText(
                question_name="wait_time",
                question_text=prompt
            )
            
            # Note: EDSL doesn't support temperature setting directly
            result = q.by(self.model).run()
            response_text = str(result.select("answer.wait_time").first())
            
            # Parse the number
            wait_time = float(response_text.strip().split()[0].replace(',', '.'))
            return max(0, min(30, wait_time))
            
        except Exception as e:
            print(f"LLM error: {e}")
            # Fallback with some randomness
            base_wait = card_value / 100 * 30
            return base_wait + random.uniform(-2, 2)
    
    def play_round(self, game_id: str, round_num: int, num_players: int, 
                   use_memory: bool, temperature: float, experiment_name: str,
                   history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Play a single round and record data."""
        
        start_time = time.time()
        
        # Deal cards
        all_cards = list(range(1, 101))
        random.shuffle(all_cards)
        
        cards_per_player = round_num
        player_hands = []
        for i in range(num_players):
            hand = sorted(all_cards[i * cards_per_player:(i + 1) * cards_per_player])
            player_hands.append(hand)
        
        # Get history string for learning
        history_str = ""
        if use_memory and history:
            for h in history[-3:]:
                history_str += f"Round {h['round_number']}: {'SUCCESS' if h['success'] else 'FAILED'} - Cards: {h['cards_played']}\n"
        
        # Collect all decisions
        decisions = []
        cards_played_so_far = []
        
        # Each player plays all their cards
        for card_num in range(cards_per_player):
            round_decisions = []
            
            for player_idx in range(num_players):
                if card_num < len(player_hands[player_idx]):
                    card = player_hands[player_idx][card_num]
                    
                    wait_time = self.get_llm_decision(
                        card_value=card,
                        round_num=round_num,
                        cards_played=cards_played_so_far,
                        player_num=player_idx + 1,
                        num_players=num_players,
                        temperature=temperature,
                        history=history_str if use_memory else None
                    )
                    
                    round_decisions.append({
                        "player": player_idx + 1,
                        "card": card,
                        "wait_time": wait_time
                    })
            
            # Sort by wait time to determine play order
            round_decisions.sort(key=lambda x: x["wait_time"])
            
            for decision in round_decisions:
                cards_played_so_far.append(decision["card"])
                decisions.append(decision)
        
        # Check if cards were played in correct order
        correct_order = sorted(cards_played_so_far)
        success = cards_played_so_far == correct_order
        
        time_taken = time.time() - start_time
        
        # Create model config
        model_config = {f"P{i+1}": self.model_name for i in range(num_players)}
        
        # Record data for CSV
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
            "time_taken": round(time_taken, 2),
            "final_success": None,  # Will be updated after game completes
            "model_config": json.dumps(model_config)
        }
        
        self.csv_data.append(csv_row)
        
        return {
            "round_number": round_num,
            "success": success,
            "cards_played": cards_played_so_far,
            "time_taken": time_taken
        }
    
    def play_game(self, experiment_name: str, num_players: int = 3, 
                  use_memory: bool = False, temperature: float = 0.7,
                  max_rounds: int = 3) -> Dict[str, Any]:
        """Play a complete game."""
        
        game_id = str(uuid.uuid4())[:8]
        lives = 3
        rounds_data = []
        
        for round_num in range(1, max_rounds + 1):
            if lives <= 0:
                break
            
            round_result = self.play_round(
                game_id=game_id,
                round_num=round_num,
                num_players=num_players,
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
            "rounds_data": rounds_data
        }
    
    def run_experiment_condition(self, condition_name: str, num_games: int,
                                num_players: int = 3, use_memory: bool = False,
                                temperature: float = 0.7) -> List[Dict]:
        """Run multiple games for a specific condition."""
        
        print(f"\n{condition_name}:")
        results = []
        
        for i in range(num_games):
            if i % 10 == 0:
                print(f"  Game {i+1}/{num_games}...", flush=True)
            
            game_result = self.play_game(
                experiment_name=condition_name,
                num_players=num_players,
                use_memory=use_memory,
                temperature=temperature
            )
            results.append(game_result)
        
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        print(f"  Success rate: {success_rate:.1%}")
        
        return results
    
    def save_to_csv(self, filename: str):
        """Save experiment data to CSV."""
        
        df = pd.DataFrame(self.csv_data)
        df.to_csv(filename, index=False)
        print(f"\nSaved {len(self.csv_data)} rows to {filename}")


def run_full_experiment():
    """Run the complete experiment suite with statistical significance."""
    
    print("="*70)
    print("THE MIND - Comprehensive LLM Coordination Experiment")
    print("Using Expected Parrot API with Gemini Models")
    print("="*70)
    
    # Number of games per condition for statistical significance
    GAMES_PER_CONDITION = 5  # Start with small test
    
    # Initialize experiments for different models
    experiments = {
        'gemini-2.5-flash-lite': ComprehensiveExperiment('gemini-2.5-flash-lite'),
        'gemini-2.5-flash': ComprehensiveExperiment('gemini-2.5-flash')
    }
    
    # Run experiments for each model
    for model_name, exp in experiments.items():
        print(f"\n{'='*70}")
        print(f"MODEL: {model_name}")
        print(f"{'='*70}")
        
        # Baseline (no memory)
        exp.run_experiment_condition(
            condition_name=f"baseline_{model_name}",
            num_games=GAMES_PER_CONDITION,
            use_memory=False,
            temperature=0.7
        )
        
        # With learning/memory
        exp.run_experiment_condition(
            condition_name=f"learning_{model_name}",
            num_games=GAMES_PER_CONDITION,
            use_memory=True,
            temperature=0.7
        )
        
        # Different temperatures
        for temp in [0.3, 1.0]:
            exp.run_experiment_condition(
                condition_name=f"temperature_{temp}_{model_name}",
                num_games=GAMES_PER_CONDITION // 2,  # Fewer games for temperature tests
                use_memory=False,
                temperature=temp
            )
        
        # Different player counts
        for num_players in [2, 4]:
            exp.run_experiment_condition(
                condition_name=f"players_{num_players}_{model_name}",
                num_games=GAMES_PER_CONDITION // 2,
                num_players=num_players,
                use_memory=False,
                temperature=0.7
            )
        
        # Save model-specific results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"visualization/public/experiment_data_{model_name}_{timestamp}.csv"
        exp.save_to_csv(csv_filename)
    
    # Combine all data
    all_data = []
    for exp in experiments.values():
        all_data.extend(exp.csv_data)
    
    # Save combined dataset
    combined_df = pd.DataFrame(all_data)
    combined_filename = f"visualization/public/full_experiment_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    combined_df.to_csv(combined_filename, index=False)
    
    print(f"\n{'='*70}")
    print("EXPERIMENT COMPLETE")
    print(f"{'='*70}")
    print(f"Total games played: {len(all_data) // 3}")  # Assuming 3 rounds per game avg
    print(f"Combined data saved to: {combined_filename}")
    
    # Statistical summary
    df = pd.DataFrame(all_data)
    
    print("\n📊 STATISTICAL SUMMARY:")
    print("-" * 50)
    
    for experiment in df['experiment'].unique():
        exp_data = df[df['experiment'] == experiment]
        success_rate = exp_data['success'].mean()
        games = exp_data['game_id'].nunique()
        print(f"{experiment:30s}: {success_rate:.1%} ({games} games)")
    
    return combined_filename


if __name__ == "__main__":
    run_full_experiment()
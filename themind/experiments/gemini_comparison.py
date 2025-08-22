"""Compare Gemini 2.5 Flash vs Flash Lite performance in The Mind."""

import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import random
import numpy as np
from pathlib import Path
from edsl import Model, QuestionFreeText
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Set Expected Parrot API key
os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')


class GeminiComparison:
    """Compare different Gemini models on The Mind."""
    
    def __init__(self, model_name: str, num_players: int = 3, seed: Optional[int] = None):
        self.model_name = model_name
        self.num_players = num_players
        self.model = Model(model_name)
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    def get_wait_time(self, card_value: int, round_num: int, player_num: int) -> float:
        """Get model's decision for wait time."""
        
        prompt = f"""You are Player {player_num} in The Mind card game.
Round: {round_num}
Your card: {card_value}
Players: {self.num_players}

Cards 1-33: wait 0-10 seconds
Cards 34-66: wait 10-20 seconds  
Cards 67-100: wait 20-30 seconds

Respond with ONLY a number (0-30):"""
        
        try:
            q = QuestionFreeText(
                question_name="wait",
                question_text=prompt
            )
            
            result = q.by(self.model).run()
            response = str(result.select("answer.wait").first())
            
            # Extract number
            for word in response.split():
                try:
                    wait = float(word.replace(',', '.'))
                    return max(0, min(30, wait))
                except:
                    continue
            
            # Fallback if no number found
            return card_value / 100 * 30
            
        except Exception as e:
            print(f"Error: {e}")
            return card_value / 100 * 30
    
    def play_round(self, round_num: int) -> Dict[str, Any]:
        """Play a round."""
        
        # Deal cards
        all_cards = list(range(1, 101))
        random.shuffle(all_cards)
        
        cards_per_player = round_num
        player_cards = []
        for i in range(self.num_players):
            hand = sorted(all_cards[i * cards_per_player:(i + 1) * cards_per_player])
            player_cards.append(hand)
        
        # Get decisions (simpler, one at a time)
        decisions = []
        
        for i in range(self.num_players):
            lowest_card = min(player_cards[i])
            wait_time = self.get_wait_time(lowest_card, round_num, i+1)
            
            decisions.append({
                "player": i + 1,
                "card": lowest_card,
                "wait_time": wait_time
            })
            print(".", end="", flush=True)
        
        # Check order
        decisions.sort(key=lambda x: x["wait_time"])
        played_cards = [d["card"] for d in decisions]
        correct_order = sorted(played_cards)
        success = played_cards == correct_order
        
        return {
            "success": success,
            "played_cards": played_cards,
            "wait_times": [d["wait_time"] for d in decisions]
        }
    
    def run_games(self, num_games: int = 5) -> Dict[str, Any]:
        """Run multiple games and collect stats."""
        
        print(f"\n{self.model_name}:")
        successes = 0
        total_rounds = 0
        
        for game in range(num_games):
            print(f"  Game {game+1}: ", end="", flush=True)
            
            lives = 3
            rounds_won = 0
            
            for round_num in range(1, 4):  # Play 3 rounds max
                if lives <= 0:
                    break
                    
                result = self.play_round(round_num)
                total_rounds += 1
                
                if result["success"]:
                    rounds_won += 1
                    print("✓", end="", flush=True)
                else:
                    lives -= 1
                    print("✗", end="", flush=True)
            
            if lives > 0:
                successes += 1
                print(" WON")
            else:
                print(" LOST")
        
        return {
            "model": self.model_name,
            "games_played": num_games,
            "games_won": successes,
            "success_rate": successes / num_games,
            "total_rounds": total_rounds,
            "rounds_success_rate": successes / total_rounds if total_rounds > 0 else 0
        }


def main():
    """Compare Gemini models."""
    
    print("="*60)
    print("GEMINI MODEL COMPARISON - The Mind")
    print("="*60)
    
    num_games = 3  # Quick test
    
    # Test both models
    models = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash"
    ]
    
    results = []
    
    for model_name in models:
        experiment = GeminiComparison(model_name, seed=42)
        result = experiment.run_games(num_games)
        results.append(result)
    
    # Display comparison
    print("\n" + "="*60)
    print("RESULTS COMPARISON:")
    print("="*60)
    
    for r in results:
        print(f"\n{r['model']}:")
        print(f"  Success Rate: {r['success_rate']:.0%} ({r['games_won']}/{r['games_played']} games)")
        print(f"  Round Success: {r['rounds_success_rate']:.0%}")
    
    # Determine winner
    print("\n" + "-"*60)
    if results[0]['success_rate'] > results[1]['success_rate']:
        winner = results[0]['model']
        margin = results[0]['success_rate'] - results[1]['success_rate']
    elif results[1]['success_rate'] > results[0]['success_rate']:
        winner = results[1]['model']
        margin = results[1]['success_rate'] - results[0]['success_rate']
    else:
        winner = "TIE"
        margin = 0
    
    if winner != "TIE":
        print(f"WINNER: {winner} by {margin:.0%}")
        print(f"\n{winner} performs better at coordination without communication!")
    else:
        print("RESULT: Both models performed equally!")
    
    # Save results
    output_dir = Path("experiments/data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(output_dir / f"gemini_comparison_{timestamp}.json", "w") as f:
        json.dump({
            "comparison": results,
            "winner": winner,
            "margin": margin,
            "timestamp": timestamp
        }, f, indent=2)
    
    print(f"\nResults saved to experiments/data/gemini_comparison_{timestamp}.json")


if __name__ == "__main__":
    main()
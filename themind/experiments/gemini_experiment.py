"""Run The Mind experiments using Expected Parrot with Gemini 2.5 Flash."""

import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import random
import numpy as np
from pathlib import Path
from edsl import Model, QuestionFreeText

# Set Expected Parrot API key
os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')


class TheMindGeminiExperiment:
    """Run The Mind with Gemini 2.5 Flash via Expected Parrot."""
    
    def __init__(
        self,
        num_players: int = 3,
        enable_learning: bool = True,
        seed: Optional[int] = None
    ):
        self.num_players = num_players
        self.enable_learning = enable_learning
        self.game_history: List[Dict] = []
        self.model = Model('gemini-2.5-flash-lite')  # Using Gemini 2.5 Flash Lite (mini)
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    def get_wait_time(self, card_value: int, round_num: int, cards_played: List[int], 
                     player_num: int, history: Optional[str] = None) -> float:
        """Get Gemini's decision for wait time."""
        
        prompt = f"""You are Player {player_num} in The Mind card game. Players must play cards in ascending order without communication, using only timing to coordinate.

Current situation:
- Round {round_num}
- Your lowest card: {card_value}
- Cards already played: {cards_played if cards_played else 'none yet'}
- Total players: {self.num_players}

Strategy: Lower cards (1-33) wait 0-10 seconds, middle cards (34-66) wait 10-20 seconds, higher cards (67-100) wait 20-30 seconds.
"""

        if history and self.enable_learning:
            prompt += f"\n\nLearning from previous rounds:\n{history}"
        
        prompt += "\n\nRespond with ONLY a number (0-30) representing seconds to wait:"
        
        try:
            q = QuestionFreeText(
                question_name="wait_time",
                question_text=prompt
            )
            
            result = q.by(self.model).run()
            response_text = str(result.select("answer.wait_time").first())
            
            # Parse the number
            wait_time = float(response_text.strip().split()[0].replace(',', '.'))
            return max(0, min(30, wait_time))
            
        except Exception as e:
            print(f"Gemini error: {e}")
            return card_value / 100 * 30  # Fallback
    
    def play_round(self, round_num: int) -> Dict[str, Any]:
        """Play a round with Gemini decisions."""
        
        # Deal cards
        all_cards = list(range(1, 101))
        random.shuffle(all_cards)
        
        cards_per_player = round_num
        player_cards = []
        for i in range(self.num_players):
            hand = sorted(all_cards[i * cards_per_player:(i + 1) * cards_per_player])
            player_cards.append(hand)
        
        # Get history for learning
        history = ""
        if self.enable_learning and self.game_history:
            for g in self.game_history[-3:]:
                history += f"Game {g['game_num']}: {'SUCCESS' if g['success'] else 'FAILED'}\n"
        
        # Get decisions
        decisions = []
        cards_played = []
        
        print(f"  Round {round_num}: ", end="", flush=True)
        
        for i in range(self.num_players):
            lowest_card = min(player_cards[i])
            
            wait_time = self.get_wait_time(
                card_value=lowest_card,
                round_num=round_num,
                cards_played=cards_played,
                player_num=i+1,
                history=history if self.enable_learning else None
            )
            
            decisions.append({
                "player": i + 1,
                "card": lowest_card,
                "wait_time": wait_time
            })
            print(".", end="", flush=True)
        
        # Sort by wait time
        decisions.sort(key=lambda x: x["wait_time"])
        played_cards = [d["card"] for d in decisions]
        correct_order = sorted(played_cards)
        success = played_cards == correct_order
        
        print(f" {'✓' if success else '✗'} {played_cards}")
        
        return {
            "round": round_num,
            "success": success,
            "played_cards": played_cards,
            "correct_order": correct_order,
            "decisions": decisions
        }
    
    def play_game(self, game_num: int, max_rounds: int = 5) -> Dict[str, Any]:
        """Play a complete game."""
        
        print(f"\nGame {game_num + 1}:")
        lives = 3
        rounds_data = []
        
        for round_num in range(1, max_rounds + 1):
            if lives <= 0:
                break
            
            round_result = self.play_round(round_num)
            rounds_data.append(round_result)
            
            if not round_result["success"]:
                lives -= 1
                print(f"  Lives remaining: {lives}")
        
        success = lives > 0
        print(f"  Game {'WON' if success else 'LOST'}")
        
        game_result = {
            "game_num": game_num,
            "rounds": rounds_data,
            "rounds_completed": len(rounds_data),
            "success": success,
            "learning_enabled": self.enable_learning
        }
        
        if self.enable_learning:
            self.game_history.append(game_result)
        
        return game_result


def main():
    """Run Gemini 2.5 Flash experiment with Expected Parrot."""
    
    print("="*60)
    print("THE MIND - Gemini 2.5 Flash Learning Analysis")
    print("Using Expected Parrot API")
    print("="*60)
    
    num_games = 5  # Start small
    
    # With learning
    print("\n📚 WITH LEARNING ENABLED:")
    exp_learning = TheMindGeminiExperiment(enable_learning=True, seed=42)
    results_learning = [exp_learning.play_game(i) for i in range(num_games)]
    
    # Without learning
    print("\n🎯 WITHOUT LEARNING:")
    exp_no_learning = TheMindGeminiExperiment(enable_learning=False, seed=42)
    results_no_learning = [exp_no_learning.play_game(i) for i in range(num_games)]
    
    # Analysis
    learning_success = sum(1 for r in results_learning if r['success']) / len(results_learning)
    no_learning_success = sum(1 for r in results_no_learning if r['success']) / len(results_no_learning)
    
    print("\n" + "="*60)
    print("RESULTS - Gemini 2.5 Flash Performance:")
    print("="*60)
    print(f"With Learning:    {learning_success:.1%} success rate")
    print(f"Without Learning: {no_learning_success:.1%} success rate")
    print(f"Learning Advantage: {(learning_success - no_learning_success):.1%}")
    
    # Save
    output_dir = Path("experiments/data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(output_dir / f"gemini_results_{timestamp}.json", "w") as f:
        json.dump({
            "model": "gemini-2.5-flash",
            "with_learning": {"success_rate": learning_success, "games": len(results_learning)},
            "without_learning": {"success_rate": no_learning_success, "games": len(results_no_learning)}
        }, f, indent=2)
    
    print(f"\n✅ Saved to experiments/data/gemini_results_{timestamp}.json")


if __name__ == "__main__":
    main()
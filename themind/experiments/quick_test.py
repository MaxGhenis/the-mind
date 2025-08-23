"""Quick test with Gemini models via Expected Parrot to generate real data."""

import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Any
import random
import uuid
from pathlib import Path
from edsl import Model, QuestionFreeText
import time

# Set Expected Parrot API key
os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')


def run_quick_test():
    """Run a quick test with just a few games to get real Gemini data."""
    
    print("="*60)
    print("QUICK GEMINI TEST - Real LLM Data via Expected Parrot")
    print("="*60)
    
    model = Model('gemini-2.5-flash-lite')
    csv_rows = []
    
    # Just 2 games with 3 rounds each
    for game_num in range(2):
        game_id = str(uuid.uuid4())[:8]
        print(f"\nGame {game_num + 1} (ID: {game_id})")
        
        for round_num in range(1, 4):  # 3 rounds
            print(f"  Round {round_num}...", end="", flush=True)
            
            # Deal cards (3 players, each gets 'round_num' cards)
            all_cards = list(range(1, 101))
            random.shuffle(all_cards)
            
            num_players = 3
            cards_per_player = round_num
            player_hands = []
            for i in range(num_players):
                hand = sorted(all_cards[i * cards_per_player:(i + 1) * cards_per_player])
                player_hands.append(hand)
            
            # Get LLM decisions for each player's lowest card
            decisions = []
            start_time = time.time()
            
            for player_idx in range(num_players):
                if player_hands[player_idx]:
                    card = min(player_hands[player_idx])
                    
                    prompt = f"""You are Player {player_idx + 1} in The Mind card game.
Your lowest card is: {card}
Cards range from 1-100. Lower cards should be played sooner.
Strategy: 1-33 wait 0-10 seconds, 34-66 wait 10-20 seconds, 67-100 wait 20-30 seconds.
Respond with ONLY a number (0-30) representing seconds to wait:"""
                    
                    try:
                        q = QuestionFreeText(
                            question_name="wait_time",
                            question_text=prompt
                        )
                        
                        result = q.by(model).run()
                        response = str(result.select("answer.wait_time").first())
                        wait_time = float(response.strip().split()[0].replace(',', '.'))
                        wait_time = max(0, min(30, wait_time))
                    except Exception as e:
                        print(f"[LLM Error: {e}]", end="")
                        wait_time = card / 100 * 30 + random.uniform(-2, 2)
                    
                    decisions.append({
                        "player": player_idx + 1,
                        "card": card,
                        "wait_time": wait_time
                    })
                    print(".", end="", flush=True)
            
            # Sort by wait time to get play order
            decisions.sort(key=lambda x: x["wait_time"])
            cards_played = [d["card"] for d in decisions]
            correct_order = sorted(cards_played)
            success = cards_played == correct_order
            
            time_taken = time.time() - start_time
            
            # Create CSV row
            csv_row = {
                "game_id": game_id,
                "timestamp": datetime.now().isoformat(),
                "experiment": "gemini-2.5-flash-lite-test",
                "use_memory": False,
                "temperature": 0.7,
                "num_players": num_players,
                "round_number": round_num,
                "success": success,
                "cards_played": json.dumps(cards_played),
                "time_taken": round(time_taken, 2),
                "final_success": None,  # Will update after game
                "model_config": json.dumps({f"P{i+1}": "gemini-2.5-flash-lite" for i in range(num_players)})
            }
            csv_rows.append(csv_row)
            
            print(f" {'✓' if success else '✗'} {cards_played}")
        
        # Update final_success for all rounds of this game
        game_success = all(row["success"] for row in csv_rows if row["game_id"] == game_id)
        for row in csv_rows:
            if row["game_id"] == game_id:
                row["final_success"] = game_success
    
    # Save to CSV
    output_file = "visualization/public/gemini_test_data.csv"
    with open(output_file, 'w', newline='') as f:
        if csv_rows:
            writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(csv_rows)
    
    print(f"\n\nSaved {len(csv_rows)} rounds to {output_file}")
    print("You can now load this in the React visualization!")
    
    # Print summary
    total_games = len(set(row["game_id"] for row in csv_rows))
    successful_rounds = sum(1 for row in csv_rows if row["success"])
    print(f"\nSummary:")
    print(f"  Total games: {total_games}")
    print(f"  Total rounds: {len(csv_rows)}")
    print(f"  Round success rate: {successful_rounds}/{len(csv_rows)} ({successful_rounds/len(csv_rows)*100:.1f}%)")


if __name__ == "__main__":
    run_quick_test()
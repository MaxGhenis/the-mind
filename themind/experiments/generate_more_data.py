"""Generate a few more games with Gemini to have more data."""

import os
import json
import csv
from datetime import datetime
import random
import uuid
from edsl import Model, QuestionFreeText
import time

os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')

def play_single_round(game_num):
    """Play a single round game."""
    model = Model('gemini-2.5-flash-lite')
    game_id = str(uuid.uuid4())[:8]
    
    print(f"\nGame {game_num} (ID: {game_id})")
    
    # Deal cards
    all_cards = list(range(1, 101))
    random.shuffle(all_cards)
    
    # Different player counts for variety
    num_players = random.choice([2, 3, 4])
    player_cards = all_cards[:num_players]
    
    print(f"  {num_players} players, cards: {player_cards}")
    
    # Get decisions
    decisions = []
    start_time = time.time()
    
    for i, card in enumerate(player_cards):
        print(f"    P{i+1} (card {card})...", end="", flush=True)
        
        prompt = f"""You are Player {i+1} in The Mind card game.
Your card is: {card}
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
            print(f" {wait_time:.1f}s")
        except Exception as e:
            print(f" Error")
            wait_time = card / 100 * 30
        
        decisions.append({
            "player": i + 1,
            "card": card,
            "wait_time": wait_time
        })
    
    # Sort by wait time
    decisions.sort(key=lambda x: x["wait_time"])
    cards_played = [d["card"] for d in decisions]
    correct_order = sorted(player_cards)
    success = cards_played == correct_order
    
    time_taken = time.time() - start_time
    
    print(f"  Result: {cards_played} {'✓' if success else '✗'}")
    
    # Create CSV row
    return {
        "game_id": game_id,
        "timestamp": datetime.now().isoformat(),
        "experiment": f"gemini-lite-{num_players}p",
        "use_memory": False,
        "temperature": 0.7,
        "num_players": num_players,
        "round_number": 1,
        "success": success,
        "cards_played": json.dumps(cards_played),
        "time_taken": round(time_taken, 2),
        "final_success": success,
        "model_config": json.dumps({f"P{i+1}": "gemini-2.5-flash-lite" for i in range(num_players)})
    }

def main():
    print("Generating more Gemini data (3 games)...")
    print("="*50)
    
    rows = []
    
    # Load existing data
    existing_file = "visualization/public/sample_data.csv"
    if os.path.exists(existing_file):
        with open(existing_file, 'r') as f:
            reader = csv.DictReader(f)
            rows.extend(list(reader))
    
    # Play 3 more games
    for i in range(3):
        try:
            new_row = play_single_round(i + 1)
            rows.append(new_row)
        except Exception as e:
            print(f"  Game {i+1} failed: {e}")
    
    # Save combined data
    if rows:
        with open(existing_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"\n✅ Saved {len(rows)} total games to {existing_file}")
    
    # Summary
    successful = sum(1 for r in rows if r.get('success') in [True, 'True', 'true'])
    print(f"Success rate: {successful}/{len(rows)} ({successful/len(rows)*100:.0f}%)")

if __name__ == "__main__":
    main()
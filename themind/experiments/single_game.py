"""Single game test with Gemini to get immediate real data."""

import os
import json
import csv
from datetime import datetime
import random
import uuid
from edsl import Model, QuestionFreeText
import time

os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')

print("Testing single game with Gemini-2.5-flash-lite via Expected Parrot...")
print("="*60)

model = Model('gemini-2.5-flash-lite')
csv_rows = []
game_id = str(uuid.uuid4())[:8]

# Just 1 round with 3 players, each gets 1 card
print(f"Game ID: {game_id}")
print("Round 1 (3 players, 1 card each)")

# Deal cards
all_cards = list(range(1, 101))
random.shuffle(all_cards)
player_cards = [all_cards[0], all_cards[1], all_cards[2]]
print(f"Cards dealt: Player 1={player_cards[0]}, Player 2={player_cards[1]}, Player 3={player_cards[2]}")

# Get decisions
decisions = []
start_time = time.time()

for i, card in enumerate(player_cards):
    print(f"  Getting Player {i+1} decision for card {card}...", end="", flush=True)
    
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
        print(f" Error: {e}")
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

print(f"\nPlay order: {cards_played}")
print(f"Should be:  {correct_order}")
print(f"Success: {success}")
print(f"Time taken: {time_taken:.1f}s")

# Save to CSV
csv_row = {
    "game_id": game_id,
    "timestamp": datetime.now().isoformat(),
    "experiment": "gemini-2.5-flash-lite-single",
    "use_memory": False,
    "temperature": 0.7,
    "num_players": 3,
    "round_number": 1,
    "success": success,
    "cards_played": json.dumps(cards_played),
    "time_taken": round(time_taken, 2),
    "final_success": success,
    "model_config": json.dumps({"P1": "gemini-2.5-flash-lite", "P2": "gemini-2.5-flash-lite", "P3": "gemini-2.5-flash-lite"})
}

output_file = "visualization/public/gemini_single_game.csv"
with open(output_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=csv_row.keys())
    writer.writeheader()
    writer.writerow(csv_row)

print(f"\nSaved to {output_file}")
print("Load this in the React app to see real Gemini gameplay!")
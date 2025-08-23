"""Play The Mind game with new action-oriented data structure that captures real timing."""

import os
import json
import csv
from datetime import datetime
import random
import uuid
from edsl import Model, QuestionFreeText
import time
from typing import Dict, List, Any

os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')

def play_round_with_timing(model: Model, num_players: int, round_number: int = 1) -> Dict[str, Any]:
    """Play a single round with detailed timing capture."""
    
    # Deal cards
    all_cards = list(range(1, 101))
    random.shuffle(all_cards)
    player_cards = all_cards[:num_players]
    
    cards_dealt = [
        {"player": i + 1, "card": card}
        for i, card in enumerate(player_cards)
    ]
    
    print(f"Round {round_number}: {num_players} players")
    print(f"  Cards dealt: {player_cards}")
    
    # Collect initial decisions from all players
    actions = []
    round_start = time.time()
    
    for i, card in enumerate(player_cards):
        player_num = i + 1
        decision_start = time.time()
        
        prompt = f"""You are Player {player_num} in The Mind card game.
Your card is: {card}
Cards range from 1-100. Lower cards should be played sooner.
Strategy: 1-33 wait 0-10 seconds, 34-66 wait 10-20 seconds, 67-100 wait 20-30 seconds.
Respond with ONLY a number (0-30) representing seconds to wait:"""
        
        try:
            q = QuestionFreeText(
                question_name="wait_time",
                question_text=prompt
            )
            
            llm_start = time.time()
            result = q.by(model).run()
            llm_end = time.time()
            
            response = str(result.select("answer.wait_time").first())
            wait_time = float(response.strip().split()[0].replace(',', '.'))
            wait_time = max(0, min(30, wait_time))
            
            print(f"  P{player_num} (card {card}): wait {wait_time:.1f}s")
            
        except Exception as e:
            print(f"  P{player_num} error: {e}")
            wait_time = card / 100 * 30  # Fallback
        
        actions.append({
            "action_id": len(actions) + 1,
            "player": player_num,
            "card": card,
            "decision_time": decision_start - round_start,
            "wait_time": wait_time,
            "play_time": wait_time,  # When they would actually play
            "llm_response_time": llm_end - llm_start if 'llm_end' in locals() else None,
            "correct": None  # Will be determined after sorting
        })
    
    # Determine actual play order and correctness
    actions_by_time = sorted(actions, key=lambda x: x["play_time"])
    correct_order = sorted(player_cards)
    
    success = True
    failure_point = None
    
    for i, action in enumerate(actions_by_time):
        if action["card"] == correct_order[i]:
            action["correct"] = True
        else:
            action["correct"] = False
            action["error"] = "played_out_of_order"
            action["should_have_been"] = correct_order[i]
            success = False
            failure_point = action["play_time"]
            # Mark remaining actions as not played
            for j in range(i + 1, len(actions_by_time)):
                actions_by_time[j]["play_time"] = None
                actions_by_time[j]["correct"] = None
            break
    
    round_end = time.time()
    
    cards_played = [a["card"] for a in actions_by_time if a["play_time"] is not None]
    print(f"  Play order: {cards_played} {'✓' if success else '✗'}")
    
    return {
        "round_number": round_number,
        "cards_dealt": cards_dealt,
        "actions": actions,
        "outcome": "success" if success else "failed",
        "failure_point": failure_point,
        "duration": round_end - round_start,
        "cards_played_order": cards_played
    }

def play_game_with_structure(
    experiment_name: str = "structured_gemini",
    model_name: str = "gemini-2.5-flash-lite",
    num_players: int = 3,
    temperature: float = 0.7,
    use_memory: bool = False
) -> Dict[str, Any]:
    """Play a complete game with structured data capture."""
    
    game_id = str(uuid.uuid4())[:8]
    model = Model(model_name, service_name="google")
    
    print(f"\n{'='*50}")
    print(f"Game {game_id} - {experiment_name}")
    print(f"Model: {model_name}, Players: {num_players}")
    print(f"{'='*50}")
    
    game_start = datetime.now()
    
    # For now, just play one round (can extend to multiple)
    round_data = play_round_with_timing(model, num_players, 1)
    
    game_end = datetime.now()
    
    return {
        "game_id": game_id,
        "metadata": {
            "experiment": experiment_name,
            "model": model_name,
            "temperature": temperature,
            "use_memory": use_memory,
            "num_players": num_players,
            "start_time": game_start.isoformat(),
            "end_time": game_end.isoformat()
        },
        "rounds": [round_data]
    }

def save_structured_data(game_data: Dict[str, Any], output_dir: str = "data/structured"):
    """Save game data in structured JSON format."""
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/{game_data['game_id']}.json"
    with open(filename, 'w') as f:
        json.dump(game_data, f, indent=2)
    
    print(f"\n✅ Saved structured data to {filename}")
    return filename

def convert_to_csv_row(game_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert structured data to CSV row for backward compatibility."""
    round_data = game_data["rounds"][0]
    
    return {
        "game_id": game_data["game_id"],
        "timestamp": game_data["metadata"]["start_time"],
        "experiment": game_data["metadata"]["experiment"],
        "use_memory": game_data["metadata"]["use_memory"],
        "temperature": game_data["metadata"]["temperature"],
        "num_players": game_data["metadata"]["num_players"],
        "round_number": round_data["round_number"],
        "success": round_data["outcome"] == "success",
        "cards_played": json.dumps(round_data["cards_played_order"]),
        "time_taken": round(round_data["duration"], 2),
        "final_success": round_data["outcome"] == "success",
        "model_config": json.dumps({
            f"P{i+1}": game_data["metadata"]["model"]
            for i in range(game_data["metadata"]["num_players"])
        }),
        # New fields for timing
        "action_data": json.dumps(round_data["actions"])  # Full timing data
    }

def main():
    """Run a single game with structured data capture."""
    
    # Play one game
    game_data = play_game_with_structure(
        experiment_name="structured_test",
        num_players=3
    )
    
    # Save structured data
    json_file = save_structured_data(game_data)
    
    # Also append to CSV for visualization
    csv_row = convert_to_csv_row(game_data)
    csv_file = "visualization/public/sample_data.csv"
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(csv_file)
    
    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(csv_row)
    
    print(f"✅ Appended to CSV: {csv_file}")
    
    # Print summary
    round_data = game_data["rounds"][0]
    print(f"\n📊 Game Summary:")
    print(f"  Success: {round_data['outcome']}")
    print(f"  Duration: {round_data['duration']:.1f}s")
    print(f"  Actions:")
    for action in round_data["actions"]:
        status = "✓" if action["correct"] else "✗" if action["correct"] is False else "-"
        play_str = f"{action['play_time']:.1f}s" if action['play_time'] else "not played"
        print(f"    P{action['player']} (card {action['card']}): wait {action['wait_time']:.1f}s, play at {play_str} {status}")

if __name__ == "__main__":
    main()
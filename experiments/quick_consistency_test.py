#!/usr/bin/env python3
"""Quick consistency test comparing prediction vs reactive strategies."""

import asyncio
import json
import os
from dataclasses import dataclass
from typing import List, Optional
from openai import AsyncOpenAI

# Load environment
from dotenv import load_dotenv
load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@dataclass
class GameState:
    round_number: int
    card_value: int
    cards_played: List[int]
    time_elapsed: float
    players_remaining: int
    total_players: int

# Test scenarios
SCENARIOS = [
    GameState(1, 15, [], 0.0, 3, 3),           # Low card, empty table
    GameState(2, 45, [12, 23], 0.0, 3, 3),     # Mid card, some played
    GameState(3, 78, [8, 15, 32, 41], 0.0, 2, 3),  # High card, many played
    GameState(1, 5, [], 0.0, 2, 2),            # Very low card
    GameState(2, 92, [14, 28, 55, 67], 0.0, 2, 2),  # Very high card
]

async def get_prediction(state: GameState, model: str = "gpt-4o-mini") -> dict:
    """Get prediction-based response: 'How long would you wait?'"""

    system = """You are playing The Mind, a cooperative card game where players must play cards in ascending order without communication.

You must decide how long to wait before playing your lowest card based on:
1. Your card's value (1-100) - lower cards should be played sooner
2. Cards already played - consider the gap from the last card
3. Number of players remaining

Respond with JSON: {"wait_seconds": <float 0-30>, "reasoning": "<brief explanation>"}"""

    user = f"""Round {state.round_number}
Your card: {state.card_value}
Cards played: {state.cards_played if state.cards_played else "None yet"}
Players remaining: {state.players_remaining}/{state.total_players}

How many seconds would you wait before playing your card?"""

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

async def get_reactive_decision(state: GameState, elapsed: float, model: str = "gpt-4o-mini") -> dict:
    """Get reactive response at a specific timestep: 'Do you play now?'"""

    system = """You are playing The Mind. At each moment, decide whether to play your card NOW or wait.

Consider:
- Your card value (1-100) - lower should play earlier
- Time elapsed - has enough time passed for your card?
- Cards on table - is there a gap you're filling?

Respond with JSON: {"play": true/false, "reasoning": "<brief>"}"""

    user = f"""⏱️ {elapsed:.1f} seconds have elapsed

Cards on table: {state.cards_played if state.cards_played else "None"}
Your card: {state.card_value}
Players: {state.players_remaining}/{state.total_players}

Do you play your card NOW?"""

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

async def run_reactive_until_play(state: GameState, max_time: float = 30.0, timestep: float = 1.0, model: str = "gpt-4o-mini") -> tuple[float, int]:
    """Run reactive prompts until LLM says 'play'. Returns (play_time, num_calls)."""
    elapsed = 0.0
    calls = 0

    while elapsed <= max_time:
        calls += 1
        result = await get_reactive_decision(state, elapsed, model)

        if result.get("play", False):
            return elapsed, calls

        elapsed += timestep

    return max_time, calls  # Timed out

async def run_consistency_test(model: str = "gpt-4o-mini"):
    """Run consistency test comparing prediction vs reactive."""

    print(f"\n{'='*60}")
    print(f"CONSISTENCY TEST: Prediction vs Reactive")
    print(f"Model: {model}")
    print(f"{'='*60}\n")

    results = []

    for i, state in enumerate(SCENARIOS):
        print(f"Scenario {i+1}: Card {state.card_value}, Table: {state.cards_played}")

        # Get prediction
        pred = await get_prediction(state, model)
        pred_wait = pred.get("wait_seconds", 0)
        print(f"  Prediction: Wait {pred_wait:.1f}s - {pred.get('reasoning', '')[:50]}...")

        # Run reactive until play
        reactive_time, num_calls = await run_reactive_until_play(state, max_time=30.0, timestep=1.0, model=model)
        print(f"  Reactive:   Played at {reactive_time:.1f}s ({num_calls} API calls)")

        # Calculate consistency
        gap = abs(pred_wait - reactive_time)
        consistent = gap <= 2.0  # Within 2 seconds tolerance

        print(f"  Gap: {gap:.1f}s {'✓ CONSISTENT' if consistent else '✗ INCONSISTENT'}")
        print()

        results.append({
            "card": state.card_value,
            "predicted": pred_wait,
            "reactive": reactive_time,
            "gap": gap,
            "consistent": consistent
        })

    # Summary
    print(f"{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    consistent_count = sum(1 for r in results if r["consistent"])
    avg_gap = sum(r["gap"] for r in results) / len(results)

    print(f"Consistent: {consistent_count}/{len(results)} ({100*consistent_count/len(results):.0f}%)")
    print(f"Average gap: {avg_gap:.1f}s")

    # Directional bias
    over_predict = sum(1 for r in results if r["predicted"] > r["reactive"])
    under_predict = sum(1 for r in results if r["predicted"] < r["reactive"])
    print(f"Over-predicts: {over_predict}, Under-predicts: {under_predict}")

    print(f"\n{'='*60}")
    print("DETAILED RESULTS")
    print(f"{'='*60}")
    print(f"{'Card':<6} {'Predicted':<10} {'Reactive':<10} {'Gap':<8} {'Match'}")
    print("-" * 50)
    for r in results:
        match = "✓" if r["consistent"] else "✗"
        print(f"{r['card']:<6} {r['predicted']:<10.1f} {r['reactive']:<10.1f} {r['gap']:<8.1f} {match}")

    return results

if __name__ == "__main__":
    asyncio.run(run_consistency_test("gpt-4o-mini"))

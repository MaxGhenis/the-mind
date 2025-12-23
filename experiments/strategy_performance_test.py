#!/usr/bin/env python3
"""Test which prompting strategy leads to better game performance."""

import asyncio
import json
import os
import random
from dataclasses import dataclass
from typing import List, Tuple
from openai import AsyncOpenAI

from dotenv import load_dotenv
load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@dataclass
class PlayerHand:
    name: str
    cards: List[int]

async def get_prediction_wait(card: int, cards_played: List[int], num_players: int, model: str) -> float:
    """Prediction strategy: Ask how long to wait upfront."""
    system = """You are playing The Mind. Players must play cards 1-100 in ascending order without talking.
Decide how long to wait before playing based on your card value.
Lower cards = shorter wait. Higher cards = longer wait.
Respond with JSON: {"wait_seconds": <float 0-30>, "reasoning": "<brief>"}"""

    last_card = cards_played[-1] if cards_played else 0
    user = f"""Your card: {card}
Last card played: {last_card}
Cards on table: {cards_played if cards_played else "None"}
Players: {num_players}

How many seconds to wait?"""

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    result = json.loads(response.choices[0].message.content)
    return max(0, min(30, result.get("wait_seconds", 5)))

async def get_reactive_wait(card: int, cards_played: List[int], num_players: int, model: str) -> float:
    """Reactive strategy: Ask at each timestep until they say play."""
    system = """You are playing The Mind. Decide if you should play your card NOW.
Consider: Is your card likely the lowest unplayed? Has enough time passed?
Respond with JSON: {"play": true/false, "reasoning": "<brief>"}"""

    timestep = 0.5
    elapsed = 0.0
    max_time = 30.0

    while elapsed <= max_time:
        last_card = cards_played[-1] if cards_played else 0
        user = f"""⏱️ {elapsed:.1f}s elapsed
Your card: {card}
Last played: {last_card}
Table: {cards_played if cards_played else "None"}
Players: {num_players}

Play NOW?"""

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)

        if result.get("play", False):
            return elapsed

        elapsed += timestep

    return max_time

async def play_round_prediction(hands: List[PlayerHand], model: str) -> Tuple[bool, List[int], str]:
    """Play a round using prediction strategy."""
    # Get all cards and who has them
    all_cards = []
    for hand in hands:
        for card in hand.cards:
            all_cards.append((card, hand.name))

    # Each player decides wait time for their lowest card
    cards_played = []
    decisions = []

    for hand in hands:
        if hand.cards:
            lowest = min(hand.cards)
            wait = await get_prediction_wait(lowest, cards_played, len(hands), model)
            decisions.append((wait, lowest, hand.name))

    # Sort by wait time - shortest goes first
    decisions.sort(key=lambda x: x[0])

    # Play in order of wait times
    correct_order = sorted([c for c, _ in all_cards])

    for wait, card, player in decisions:
        cards_played.append(card)

        # Check if this was correct
        expected = correct_order[len(cards_played) - 1]
        if card != expected:
            return False, cards_played, f"{player} played {card}, should be {expected}"

    return True, cards_played, "Success!"

async def play_round_reactive(hands: List[PlayerHand], model: str) -> Tuple[bool, List[int], str]:
    """Play a round using reactive strategy."""
    all_cards = []
    for hand in hands:
        for card in hand.cards:
            all_cards.append((card, hand.name))

    cards_played = []
    correct_order = sorted([c for c, _ in all_cards])

    # Simulate time passing, query each player
    remaining_cards = [(min(h.cards), h.name) for h in hands if h.cards]

    while remaining_cards:
        # Get wait times for all players with cards
        decisions = []
        for card, player in remaining_cards:
            wait = await get_reactive_wait(card, cards_played, len(hands), model)
            decisions.append((wait, card, player))

        # Shortest wait plays
        decisions.sort(key=lambda x: x[0])
        wait, card, player = decisions[0]

        cards_played.append(card)
        remaining_cards = [(c, p) for c, p in remaining_cards if c != card]

        # Check correctness
        expected = correct_order[len(cards_played) - 1]
        if card != expected:
            return False, cards_played, f"{player} played {card}, should be {expected}"

    return True, cards_played, "Success!"

async def run_game(num_players: int, strategy: str, model: str, seed: int) -> dict:
    """Run a single game with the given strategy."""
    random.seed(seed)

    # Deal cards for round 1 (1 card each)
    deck = list(range(1, 101))
    random.shuffle(deck)

    hands = []
    for i in range(num_players):
        hands.append(PlayerHand(f"P{i+1}", [deck.pop()]))

    if strategy == "prediction":
        success, played, msg = await play_round_prediction(hands, model)
    else:
        success, played, msg = await play_round_reactive(hands, model)

    return {
        "strategy": strategy,
        "success": success,
        "cards_dealt": [h.cards[0] for h in hands],
        "cards_played": played,
        "message": msg
    }

async def run_comparison(num_games: int = 10, num_players: int = 3, model: str = "gpt-4o-mini"):
    """Run games with both strategies and compare."""
    print(f"\n{'='*60}")
    print(f"STRATEGY PERFORMANCE COMPARISON")
    print(f"Model: {model} | Players: {num_players} | Games: {num_games} each")
    print(f"{'='*60}\n")

    prediction_results = []
    reactive_results = []

    for i in range(num_games):
        seed = 42 + i  # Same seeds for fair comparison

        print(f"Game {i+1}/{num_games}...")

        # Run prediction
        pred = await run_game(num_players, "prediction", model, seed)
        prediction_results.append(pred)
        print(f"  Prediction: {'✓' if pred['success'] else '✗'} Cards: {pred['cards_dealt']} → {pred['cards_played']}")

        # Run reactive with same cards
        react = await run_game(num_players, "reactive", model, seed)
        reactive_results.append(react)
        print(f"  Reactive:   {'✓' if react['success'] else '✗'} Cards: {react['cards_dealt']} → {react['cards_played']}")
        print()

    # Summary
    pred_wins = sum(1 for r in prediction_results if r["success"])
    react_wins = sum(1 for r in reactive_results if r["success"])

    print(f"{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Prediction Strategy: {pred_wins}/{num_games} wins ({100*pred_wins/num_games:.0f}%)")
    print(f"Reactive Strategy:   {react_wins}/{num_games} wins ({100*react_wins/num_games:.0f}%)")
    print()

    if pred_wins > react_wins:
        print(f"🏆 PREDICTION wins by {pred_wins - react_wins} games!")
    elif react_wins > pred_wins:
        print(f"🏆 REACTIVE wins by {react_wins - pred_wins} games!")
    else:
        print("🤝 TIE!")

    # Head-to-head on same deals
    both_win = sum(1 for p, r in zip(prediction_results, reactive_results) if p["success"] and r["success"])
    both_lose = sum(1 for p, r in zip(prediction_results, reactive_results) if not p["success"] and not r["success"])
    pred_only = sum(1 for p, r in zip(prediction_results, reactive_results) if p["success"] and not r["success"])
    react_only = sum(1 for p, r in zip(prediction_results, reactive_results) if not p["success"] and r["success"])

    print(f"\nHead-to-head (same card deals):")
    print(f"  Both win:        {both_win}")
    print(f"  Both lose:       {both_lose}")
    print(f"  Prediction only: {pred_only}")
    print(f"  Reactive only:   {react_only}")

    return prediction_results, reactive_results

if __name__ == "__main__":
    asyncio.run(run_comparison(num_games=10, num_players=3, model="gpt-4o-mini"))

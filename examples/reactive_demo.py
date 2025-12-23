#!/usr/bin/env python3
"""Demo script showing the reactive prompting strategy in action."""

import os
import sys
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from themind.core.card import Card
from themind.core.game_state import GameState
from themind.core.reactive_player import ReactiveLLMPlayer
from themind.models.llm_factory import LLMFactory


async def demo_reactive_player():
    """Demonstrate reactive player decision-making."""
    print("=" * 70)
    print("REACTIVE PROMPTING STRATEGY DEMO")
    print("=" * 70)
    print()
    print("This demo shows how the reactive player makes decisions by")
    print("simulating time passing and asking 'Do you play now?' at each step.")
    print()

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: Please set OPENAI_API_KEY environment variable")
        return

    # Create factory and get a client
    factory = LLMFactory()
    temp_player = factory.create_player("temp", "gpt-4o-mini")

    # Create reactive player
    print("Creating reactive player...")
    player = ReactiveLLMPlayer(
        name="ReactiveAI",
        model="gpt-4o-mini",
        client=temp_player.client,
        timestep_interval=1.0,  # Check every 1 second (larger for demo visibility)
        max_time=15.0,
        use_memory=False,
        temperature=0.7
    )

    # Scenario 1: Early game, low card
    print("\n" + "-" * 70)
    print("SCENARIO 1: Early game, no cards played yet")
    print("-" * 70)
    player.receive_card(Card(15))

    game_state = GameState(
        round_number=1,
        cards_played=[],
        time_elapsed=0.0,
        players_remaining=3,
        total_players=3
    )

    print(f"Your card: {player.lowest_card.value}")
    print(f"Cards played: {[c.value for c in game_state.cards_played]}")
    print("\nMaking decision...")

    decision = await player.decide(game_state)

    print(f"\nDECISION:")
    print(f"  Play after: {decision.elapsed_time:.1f} seconds")
    print(f"  API calls made: {decision.timesteps_checked}")
    print(f"  Final reasoning: {decision.reasoning}")
    print(f"\n  Decision history:")
    for step in decision.intermediate_decisions:
        if "error" in step:
            print(f"    {step['time']:.1f}s: ERROR - {step['error']}")
        else:
            action = "PLAY" if step["play"] else "WAIT"
            print(f"    {step['time']:.1f}s: {action} - {step['reasoning'][:50]}...")

    player.clear_hand()

    # Scenario 2: Mid game, medium card with some cards played
    print("\n" + "-" * 70)
    print("SCENARIO 2: Mid game, several cards already played")
    print("-" * 70)
    player.receive_card(Card(55))

    game_state = GameState(
        round_number=2,
        cards_played=[Card(12), Card(28), Card(41)],
        time_elapsed=0.0,
        players_remaining=3,
        total_players=3
    )

    print(f"Your card: {player.lowest_card.value}")
    print(f"Cards played: {[c.value for c in game_state.cards_played]}")
    print("\nMaking decision...")

    decision = await player.decide(game_state)

    print(f"\nDECISION:")
    print(f"  Play after: {decision.elapsed_time:.1f} seconds")
    print(f"  API calls made: {decision.timesteps_checked}")
    print(f"  Final reasoning: {decision.reasoning}")
    print(f"\n  Decision history:")
    for step in decision.intermediate_decisions:
        if "error" in step:
            print(f"    {step['time']:.1f}s: ERROR - {step['error']}")
        else:
            action = "PLAY" if step["play"] else "WAIT"
            print(f"    {step['time']:.1f}s: {action} - {step['reasoning'][:50]}...")

    player.clear_hand()

    # Scenario 3: Late game, high card
    print("\n" + "-" * 70)
    print("SCENARIO 3: Late game, high card")
    print("-" * 70)
    player.receive_card(Card(87))

    game_state = GameState(
        round_number=3,
        cards_played=[Card(23), Card(45), Card(61), Card(74)],
        time_elapsed=0.0,
        players_remaining=2,
        total_players=3
    )

    print(f"Your card: {player.lowest_card.value}")
    print(f"Cards played: {[c.value for c in game_state.cards_played]}")
    print("\nMaking decision...")

    decision = await player.decide(game_state)

    print(f"\nDECISION:")
    print(f"  Play after: {decision.elapsed_time:.1f} seconds")
    print(f"  API calls made: {decision.timesteps_checked}")
    print(f"  Final reasoning: {decision.reasoning}")
    print(f"\n  Decision history:")
    for step in decision.intermediate_decisions:
        if "error" in step:
            print(f"    {step['time']:.1f}s: ERROR - {step['error']}")
        else:
            action = "PLAY" if step["play"] else "WAIT"
            print(f"    {step['time']:.1f}s: {action} - {step['reasoning'][:50]}...")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Key observations:")
    print("- Lower cards tend to play sooner (fewer WAIT decisions)")
    print("- Higher cards wait longer (more WAIT decisions before PLAY)")
    print("- More API calls needed for cards that wait longer")
    print("- Each decision shows the LLM's reasoning at that moment in time")
    print()


if __name__ == "__main__":
    asyncio.run(demo_reactive_player())

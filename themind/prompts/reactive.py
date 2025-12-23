"""Reactive prompting strategy for The Mind game.

In this strategy, the LLM is asked at each timestep whether to play now,
rather than predicting how long to wait.
"""

import json
from typing import Dict, Any, List
from themind.core.game_state import GameState
from themind.core.card import Card


def get_system_prompt() -> str:
    """Get the system prompt for reactive LLM players.

    Returns:
        System prompt explaining the game and decision format
    """
    return """You are playing The Mind, a cooperative card game where players must play cards in ascending order without communication.

At each moment in time, you will be asked whether to play your lowest card NOW or wait.

Key rules:
1. Cards are numbered 1-100
2. Players must play cards in ascending order
3. No communication is allowed
4. If someone plays out of order, the round fails
5. Success requires all players to play all their cards in order

Your decision should be based on:
- Your lowest card's value
- Cards already played on the table
- Time elapsed so far
- Number of players still holding cards
- The gap between your card and the last played card

Respond with JSON format:
{
    "play": true/false,
    "reasoning": "<your strategic reasoning for this decision>"
}

Strategy tips:
- Lower cards should be played sooner
- Higher cards should wait longer
- Consider the gap between your card and the last played card
- Account for other players who might have lower cards
- If your card is close to the last played card, you might need to wait
- If enough time has passed relative to your card value, consider playing"""


def build_timestep_prompt(
    game_state: GameState,
    player_card: Card,
    elapsed_seconds: float
) -> str:
    """Build the prompt for a specific timestep.

    Args:
        game_state: Current game state
        player_card: The player's lowest card
        elapsed_seconds: Time elapsed in the current decision window

    Returns:
        Formatted prompt for the LLM
    """
    cards_played_values = [c.value for c in game_state.cards_played]

    prompt_parts = [
        f"[{elapsed_seconds:.1f} seconds have elapsed since the last card was played]",
        "",
        f"Round: {game_state.round_number}",
        f"Cards on table: {cards_played_values if cards_played_values else '[empty]'}",
        f"Your lowest card: {player_card.value}",
        f"Players still holding cards: {game_state.players_remaining}/{game_state.total_players}",
        "",
        "Do you play your card NOW?"
    ]

    return "\n".join(prompt_parts)


def parse_response(response_text: str) -> Dict[str, Any]:
    """Parse the LLM's response.

    Args:
        response_text: JSON response from the LLM

    Returns:
        Dictionary with 'play' (bool) and 'reasoning' (str)

    Raises:
        ValueError: If response is malformed
    """
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}")

    if "play" not in data:
        raise ValueError("Response missing 'play' field")
    if "reasoning" not in data:
        raise ValueError("Response missing 'reasoning' field")

    if not isinstance(data["play"], bool):
        raise ValueError(f"'play' must be boolean, got {type(data['play'])}")
    if not isinstance(data["reasoning"], str):
        raise ValueError(f"'reasoning' must be string, got {type(data['reasoning'])}")
    if not data["reasoning"].strip():
        raise ValueError("'reasoning' cannot be empty")

    return {
        "play": data["play"],
        "reasoning": data["reasoning"]
    }


def get_memory_context(memory: List[Dict[str, Any]]) -> str:
    """Get context from previous rounds for learning.

    Args:
        memory: List of previous round information

    Returns:
        Formatted string with memory context
    """
    if not memory:
        return ""

    memory_parts = ["\nLearning from previous rounds:"]

    # Include last 3 rounds
    for round_info in memory[-3:]:
        status = "SUCCESS" if round_info.get("success", False) else "FAILURE"
        cards = round_info.get("cards_played", [])
        memory_parts.append(
            f"Round {round_info.get('round_number', '?')}: {status} - "
            f"Cards played: {cards}"
        )

    return "\n".join(memory_parts)

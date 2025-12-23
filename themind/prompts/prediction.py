"""Prediction-based prompting strategy for The Mind.

This strategy asks the LLM to predict upfront how long it would wait before
playing its card, based on the current game state.
"""

import json
from typing import Dict, Any, List, Optional

from themind.core.game_state import GameState, RoundInfo
from themind.core.card import Card


def get_prediction_system_prompt() -> str:
    """Get the system prompt for prediction-based strategy.

    Returns:
        System prompt explaining the game and decision format.
    """
    return """You are playing The Mind, a cooperative card game where players must play cards in ascending order without communication.

Game Rules:
- Cards are numbered 1-100
- All players must play their cards in ascending order
- Players cannot communicate about their cards
- The only coordination mechanism is timing: wait before playing your card
- If a player plays a card out of order, the round fails

Your Task:
You must decide how long to wait (in seconds) before playing your lowest card.

Decision Factors:
1. Your card's value (1-100) - lower cards should be played sooner
2. Cards already played - helps you gauge where you are in the sequence
3. Time elapsed - understanding how long others have waited
4. Number of players remaining - affects how you space out your timing
5. Gap between your card and last played card - larger gaps need more wait time

Response Format:
You must respond with valid JSON:
{
    "wait_seconds": <float between 0 and 30>,
    "reasoning": "<your strategic reasoning explaining why this wait time>",
    "confidence": <float between 0 and 1, where 1 is very confident>
}

Strategy Tips:
- Lower cards (1-30) should typically be played quickly (0-5 seconds)
- Middle cards (31-70) need moderate wait times (5-15 seconds)
- Higher cards (71-100) should wait longer (15-30 seconds)
- Consider the gap: if the last card was 20 and yours is 25, wait less than if yours was 50
- Account for other players: more remaining players means you should be more cautious
- Learn from timing patterns in the current round"""


def build_prediction_user_prompt(
    game_state: GameState,
    my_card: Card,
    memory: Optional[List[RoundInfo]] = None,
) -> str:
    """Build the user prompt with current game state.

    Args:
        game_state: Current state of the game
        my_card: The player's lowest card
        memory: Optional list of previous rounds for learning

    Returns:
        Formatted prompt with game state information.
    """
    prompt_parts = [
        f"Round {game_state.round_number}",
        f"Your lowest card: {my_card.value}",
        f"Cards played so far: {[c.value for c in game_state.cards_played]}",
        f"Time elapsed: {game_state.time_elapsed:.1f} seconds",
        f"Players remaining: {game_state.players_remaining}/{game_state.total_players}",
    ]

    # Add last played card context if available
    if game_state.cards_played:
        last_card = game_state.cards_played[-1].value
        gap = my_card.value - last_card
        prompt_parts.append(f"Gap from last card: {gap} (last card was {last_card})")

    # Add memory/learning section if available
    if memory:
        memory_summary = _summarize_memory(memory)
        prompt_parts.append(f"\nLearning from previous rounds:\n{memory_summary}")

    # Final question
    prompt_parts.append("\nBased on the game state above, how many seconds would you wait before playing your card?")

    return "\n".join(prompt_parts)


def parse_prediction_response(response_content: str) -> Dict[str, Any]:
    """Parse the LLM's JSON response into a decision dictionary.

    Args:
        response_content: Raw JSON string from LLM

    Returns:
        Dictionary with wait_seconds, reasoning, and confidence

    Raises:
        ValueError: If response is invalid or missing required fields
    """
    try:
        data = json.loads(response_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")

    # Validate required fields
    if "wait_seconds" not in data:
        raise ValueError("Response missing 'wait_seconds' field")
    if "reasoning" not in data:
        raise ValueError("Response missing 'reasoning' field")

    # Extract and validate values
    try:
        wait_seconds = float(data["wait_seconds"])
    except (TypeError, ValueError):
        raise ValueError(f"Invalid wait_seconds value: {data['wait_seconds']}")

    if wait_seconds < 0:
        raise ValueError(f"wait_seconds cannot be negative: {wait_seconds}")

    if wait_seconds > 30:
        raise ValueError(f"wait_seconds cannot exceed 30: {wait_seconds}")

    reasoning = str(data["reasoning"])
    if not reasoning.strip():
        raise ValueError("Reasoning cannot be empty")

    # Confidence is optional, default to 0.5
    confidence = data.get("confidence", 0.5)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid confidence value: {confidence}")

    if not 0 <= confidence <= 1:
        raise ValueError(f"Confidence must be between 0 and 1: {confidence}")

    return {
        "wait_seconds": wait_seconds,
        "reasoning": reasoning,
        "confidence": confidence,
    }


def _summarize_memory(memory: List[RoundInfo]) -> str:
    """Summarize memory from previous rounds for learning.

    Args:
        memory: List of previous round information

    Returns:
        Human-readable summary of recent rounds
    """
    if not memory:
        return "No previous rounds"

    summaries = []
    for round_info in memory[-3:]:  # Last 3 rounds for context
        status = "SUCCESS" if round_info.success else "FAILURE"
        summaries.append(
            f"Round {round_info.round_number}: {status} - "
            f"Cards played: {round_info.cards_played}"
        )

    return "\n".join(summaries)

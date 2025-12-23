"""Example demonstrating the prediction-based prompting strategy.

This example shows how to use the clean, modular prediction prompting system
for The Mind LLM players.
"""

from themind.prompts.prediction import (
    get_prediction_system_prompt,
    build_prediction_user_prompt,
    parse_prediction_response,
)
from themind.core.card import Card
from themind.core.game_state import GameState


def main():
    """Demonstrate the prediction prompting system."""

    # 1. Get the system prompt
    print("=" * 60)
    print("SYSTEM PROMPT")
    print("=" * 60)
    system_prompt = get_prediction_system_prompt()
    print(system_prompt[:500] + "...\n")

    # 2. Build a user prompt with game state
    print("=" * 60)
    print("USER PROMPT")
    print("=" * 60)
    game_state = GameState(
        round_number=1,
        cards_played=[Card(10), Card(20)],
        time_elapsed=5.2,
        players_remaining=3,
        total_players=4
    )
    my_card = Card(45)

    user_prompt = build_prediction_user_prompt(game_state, my_card)
    print(user_prompt)
    print()

    # 3. Parse an example LLM response
    print("=" * 60)
    print("PARSING LLM RESPONSE")
    print("=" * 60)
    example_response = """
    {
        "wait_seconds": 8.5,
        "reasoning": "My card (45) has a gap of 25 from the last played card (20). Given that 3 players are remaining and we're still early in the round, I should wait a moderate amount of time. The gap suggests I'm in the middle of the remaining sequence, so around 8-9 seconds seems appropriate to allow lower cards to be played first while not waiting so long that higher cards get played before me.",
        "confidence": 0.75
    }
    """

    result = parse_prediction_response(example_response)
    print(f"Wait time: {result['wait_seconds']} seconds")
    print(f"Confidence: {result['confidence']}")
    print(f"Reasoning: {result['reasoning']}")
    print()

    # 4. Show validation in action
    print("=" * 60)
    print("VALIDATION EXAMPLES")
    print("=" * 60)

    # Valid response
    valid = '{"wait_seconds": 3.0, "reasoning": "Low card, play quickly"}'
    print(f"Valid response: {parse_prediction_response(valid)['wait_seconds']}s")

    # Invalid responses
    invalid_examples = [
        ('{"wait_seconds": -1, "reasoning": "Test"}', "Negative wait time"),
        ('{"wait_seconds": 50, "reasoning": "Test"}', "Wait time exceeds 30s"),
        ('{"wait_seconds": 5, "reasoning": ""}', "Empty reasoning"),
        ('{"reasoning": "Missing wait_seconds"}', "Missing required field"),
    ]

    for invalid_response, description in invalid_examples:
        try:
            parse_prediction_response(invalid_response)
            print(f"UNEXPECTED: {description} should have failed")
        except ValueError as e:
            print(f"Correctly rejected: {description}")

    print()
    print("=" * 60)
    print("PREDICTION PROMPTING DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()

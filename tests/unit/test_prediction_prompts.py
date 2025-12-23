"""Unit tests for prediction prompting strategy."""

import pytest
from themind.prompts.prediction import (
    get_prediction_system_prompt,
    build_prediction_user_prompt,
    parse_prediction_response,
)
from themind.core.card import Card
from themind.core.game_state import GameState, RoundInfo


class TestPredictionSystemPrompt:
    def test_system_prompt_includes_game_rules(self):
        prompt = get_prediction_system_prompt()

        assert "The Mind" in prompt
        assert "cooperative" in prompt
        assert "ascending order" in prompt
        assert "wait_seconds" in prompt
        assert "reasoning" in prompt
        assert "confidence" in prompt


class TestBuildPredictionUserPrompt:
    def test_basic_prompt_structure(self):
        game_state = GameState(
            round_number=1,
            cards_played=[Card(10)],
            time_elapsed=3.5,
            players_remaining=3,
            total_players=4
        )
        my_card = Card(25)

        prompt = build_prediction_user_prompt(game_state, my_card)

        assert "Round 1" in prompt
        assert "Your lowest card: 25" in prompt
        assert "[10]" in prompt
        assert "Time elapsed: 3.5" in prompt
        assert "Players remaining: 3/4" in prompt

    def test_prompt_with_gap_calculation(self):
        game_state = GameState(
            round_number=1,
            cards_played=[Card(10), Card(20)],
            time_elapsed=5.0,
            players_remaining=2,
            total_players=3
        )
        my_card = Card(45)

        prompt = build_prediction_user_prompt(game_state, my_card)

        assert "Gap from last card: 25" in prompt
        assert "last card was 20" in prompt

    def test_prompt_with_memory(self):
        game_state = GameState(
            round_number=2,
            cards_played=[],
            time_elapsed=0.0,
            players_remaining=3,
            total_players=3
        )
        my_card = Card(30)
        memory = [
            RoundInfo(
                round_number=1,
                success=True,
                cards_played=[10, 20, 30],
                player_decisions={}
            )
        ]

        prompt = build_prediction_user_prompt(game_state, my_card, memory=memory)

        assert "Learning from previous rounds" in prompt
        assert "Round 1: SUCCESS" in prompt


class TestParsePredictionResponse:
    def test_parse_valid_response(self):
        response = '{"wait_seconds": 5.5, "reasoning": "My card is mid-range", "confidence": 0.75}'

        result = parse_prediction_response(response)

        assert result["wait_seconds"] == 5.5
        assert result["reasoning"] == "My card is mid-range"
        assert result["confidence"] == 0.75

    def test_parse_response_default_confidence(self):
        response = '{"wait_seconds": 3.0, "reasoning": "Playing quickly"}'

        result = parse_prediction_response(response)

        assert result["wait_seconds"] == 3.0
        assert result["reasoning"] == "Playing quickly"
        assert result["confidence"] == 0.5  # Default

    def test_parse_invalid_json(self):
        response = 'not valid json'

        with pytest.raises(ValueError, match="Invalid JSON response"):
            parse_prediction_response(response)

    def test_parse_missing_wait_seconds(self):
        response = '{"reasoning": "Test"}'

        with pytest.raises(ValueError, match="missing 'wait_seconds'"):
            parse_prediction_response(response)

    def test_parse_missing_reasoning(self):
        response = '{"wait_seconds": 5.0}'

        with pytest.raises(ValueError, match="missing 'reasoning'"):
            parse_prediction_response(response)

    def test_parse_negative_wait_seconds(self):
        response = '{"wait_seconds": -2.0, "reasoning": "Test"}'

        with pytest.raises(ValueError, match="cannot be negative"):
            parse_prediction_response(response)

    def test_parse_excessive_wait_seconds(self):
        response = '{"wait_seconds": 50.0, "reasoning": "Test"}'

        with pytest.raises(ValueError, match="cannot exceed 30"):
            parse_prediction_response(response)

    def test_parse_empty_reasoning(self):
        response = '{"wait_seconds": 5.0, "reasoning": ""}'

        with pytest.raises(ValueError, match="Reasoning cannot be empty"):
            parse_prediction_response(response)

    def test_parse_invalid_confidence(self):
        response = '{"wait_seconds": 5.0, "reasoning": "Test", "confidence": 1.5}'

        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            parse_prediction_response(response)

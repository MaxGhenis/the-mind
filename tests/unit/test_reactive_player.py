"""Unit tests for ReactiveLLMPlayer and reactive prompting."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from themind.core.reactive_player import ReactiveLLMPlayer, ReactiveDecision
from themind.core.card import Card
from themind.core.game_state import GameState, RoundInfo
from themind.prompts import reactive


class TestReactivePrompts:
    """Test reactive prompting functions."""

    def test_get_system_prompt(self):
        """Test system prompt generation."""
        prompt = reactive.get_system_prompt()

        assert isinstance(prompt, str)
        assert "The Mind" in prompt
        assert "play" in prompt.lower()
        assert "json" in prompt.lower()
        assert "true/false" in prompt

    def test_build_timestep_prompt(self):
        """Test timestep prompt generation."""
        game_state = GameState(
            round_number=1,
            cards_played=[Card(10), Card(25)],
            time_elapsed=0.0,
            players_remaining=3,
            total_players=4
        )
        player_card = Card(35)
        elapsed = 2.5

        prompt = reactive.build_timestep_prompt(game_state, player_card, elapsed)

        assert "2.5 seconds" in prompt
        assert "[10, 25]" in prompt
        assert "35" in prompt
        assert "3/4" in prompt
        assert "Do you play" in prompt

    def test_build_timestep_prompt_empty_table(self):
        """Test timestep prompt with no cards played."""
        game_state = GameState(
            round_number=1,
            cards_played=[],
            time_elapsed=0.0,
            players_remaining=4,
            total_players=4
        )
        player_card = Card(20)
        elapsed = 1.0

        prompt = reactive.build_timestep_prompt(game_state, player_card, elapsed)

        assert "[empty]" in prompt
        assert "20" in prompt

    def test_parse_response_valid(self):
        """Test parsing a valid JSON response."""
        response = '{"play": true, "reasoning": "My card is low enough to play now"}'
        result = reactive.parse_response(response)

        assert result["play"] is True
        assert result["reasoning"] == "My card is low enough to play now"

    def test_parse_response_wait(self):
        """Test parsing a wait decision."""
        response = '{"play": false, "reasoning": "Need to wait for lower cards"}'
        result = reactive.parse_response(response)

        assert result["play"] is False
        assert "wait" in result["reasoning"].lower()

    def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON."""
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            reactive.parse_response("not json")

    def test_parse_response_missing_play(self):
        """Test parsing response missing 'play' field."""
        with pytest.raises(ValueError, match="missing 'play'"):
            reactive.parse_response('{"reasoning": "test"}')

    def test_parse_response_missing_reasoning(self):
        """Test parsing response missing 'reasoning' field."""
        with pytest.raises(ValueError, match="missing 'reasoning'"):
            reactive.parse_response('{"play": true}')

    def test_parse_response_wrong_type(self):
        """Test parsing response with wrong types."""
        with pytest.raises(ValueError, match="must be boolean"):
            reactive.parse_response('{"play": "yes", "reasoning": "test"}')

        with pytest.raises(ValueError, match="must be string"):
            reactive.parse_response('{"play": true, "reasoning": 123}')

    def test_parse_response_empty_reasoning(self):
        """Test parsing response with empty reasoning."""
        with pytest.raises(ValueError, match="cannot be empty"):
            reactive.parse_response('{"play": true, "reasoning": "   "}')

    def test_get_memory_context_empty(self):
        """Test memory context with no memory."""
        context = reactive.get_memory_context([])
        assert context == ""

    def test_get_memory_context_with_rounds(self):
        """Test memory context with previous rounds."""
        memory = [
            {
                "round_number": 1,
                "success": True,
                "cards_played": [10, 20, 30]
            },
            {
                "round_number": 2,
                "success": False,
                "cards_played": [15, 40]
            }
        ]

        context = reactive.get_memory_context(memory)

        assert "previous rounds" in context.lower()
        assert "Round 1: SUCCESS" in context
        assert "Round 2: FAILURE" in context
        assert "[10, 20, 30]" in context


class TestReactiveDecision:
    """Test ReactiveDecision dataclass."""

    def test_creation(self):
        """Test creating a ReactiveDecision."""
        decision = ReactiveDecision(
            elapsed_time=3.5,
            reasoning="Card is low enough",
            timesteps_checked=7,
            intermediate_decisions=[
                {"time": 0.0, "play": False, "reasoning": "Too early"},
                {"time": 3.5, "play": True, "reasoning": "Now is good"}
            ]
        )

        assert decision.elapsed_time == 3.5
        assert decision.reasoning == "Card is low enough"
        assert decision.timesteps_checked == 7
        assert len(decision.intermediate_decisions) == 2

    def test_to_dict(self):
        """Test converting ReactiveDecision to dict."""
        decision = ReactiveDecision(
            elapsed_time=2.0,
            reasoning="Test",
            timesteps_checked=4,
            intermediate_decisions=[]
        )

        d = decision.to_dict()

        assert d["elapsed_time"] == 2.0
        assert d["reasoning"] == "Test"
        assert d["timesteps_checked"] == 4
        assert d["intermediate_decisions"] == []


class TestReactiveLLMPlayer:
    """Test ReactiveLLMPlayer class."""

    def test_player_creation(self):
        """Test creating a reactive player."""
        mock_client = Mock()
        player = ReactiveLLMPlayer(
            name="ReactiveAI",
            model="gpt-4o-mini",
            client=mock_client,
            timestep_interval=0.5,
            max_time=20.0
        )

        assert player.name == "ReactiveAI"
        assert player.model == "gpt-4o-mini"
        assert player.timestep_interval == 0.5
        assert player.max_time == 20.0
        assert player.memory == []

    @pytest.mark.asyncio
    async def test_decide_immediate_play(self):
        """Test reactive decision that plays immediately."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(
            content='{"play": true, "reasoning": "Card is very low, play immediately"}'
        ))]
        mock_client.chat.completions.create.return_value = mock_response

        player = ReactiveLLMPlayer(
            name="ReactiveAI",
            model="gpt-4o-mini",
            client=mock_client,
            timestep_interval=0.5
        )
        player.receive_card(Card(5))

        game_state = GameState(
            round_number=1,
            cards_played=[],
            time_elapsed=0.0,
            players_remaining=3,
            total_players=3
        )

        decision = await player.decide(game_state)

        assert isinstance(decision, ReactiveDecision)
        assert decision.elapsed_time == 0.0  # Played immediately
        assert decision.timesteps_checked == 1
        assert len(decision.intermediate_decisions) == 1
        assert decision.intermediate_decisions[0]["play"] is True

    @pytest.mark.asyncio
    async def test_decide_wait_then_play(self):
        """Test reactive decision that waits before playing."""
        mock_client = AsyncMock()

        # First two calls: wait
        # Third call: play
        responses = [
            Mock(choices=[Mock(message=Mock(
                content='{"play": false, "reasoning": "Too early"}'
            ))]),
            Mock(choices=[Mock(message=Mock(
                content='{"play": false, "reasoning": "Still too early"}'
            ))]),
            Mock(choices=[Mock(message=Mock(
                content='{"play": true, "reasoning": "Now is good"}'
            ))])
        ]
        mock_client.chat.completions.create.side_effect = responses

        player = ReactiveLLMPlayer(
            name="ReactiveAI",
            model="gpt-4o-mini",
            client=mock_client,
            timestep_interval=1.0
        )
        player.receive_card(Card(50))

        game_state = GameState(
            round_number=1,
            cards_played=[Card(20)],
            time_elapsed=0.0,
            players_remaining=3,
            total_players=3
        )

        decision = await player.decide(game_state)

        assert decision.elapsed_time == 2.0  # 2 waits @ 1.0s each
        assert decision.timesteps_checked == 3
        assert len(decision.intermediate_decisions) == 3
        assert decision.intermediate_decisions[0]["play"] is False
        assert decision.intermediate_decisions[1]["play"] is False
        assert decision.intermediate_decisions[2]["play"] is True

    @pytest.mark.asyncio
    async def test_decide_max_time_reached(self):
        """Test reactive decision when max time is reached."""
        mock_client = AsyncMock()
        # Always return false until max time
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(
            content='{"play": false, "reasoning": "Waiting for others"}'
        ))]
        mock_client.chat.completions.create.return_value = mock_response

        player = ReactiveLLMPlayer(
            name="ReactiveAI",
            model="gpt-4o-mini",
            client=mock_client,
            timestep_interval=1.0,
            max_time=3.0  # Very short max time
        )
        player.receive_card(Card(75))

        game_state = GameState(
            round_number=1,
            cards_played=[],
            time_elapsed=0.0,
            players_remaining=3,
            total_players=3
        )

        decision = await player.decide(game_state)

        assert decision.elapsed_time == 3.0  # Max time
        assert "Maximum time" in decision.reasoning
        assert decision.timesteps_checked == 3  # 0.0, 1.0, 2.0

    @pytest.mark.asyncio
    async def test_decide_no_cards_error(self):
        """Test that decide raises error when no cards in hand."""
        mock_client = Mock()
        player = ReactiveLLMPlayer(
            name="ReactiveAI",
            model="gpt-4o-mini",
            client=mock_client
        )

        game_state = GameState(
            round_number=1,
            cards_played=[],
            time_elapsed=0.0,
            players_remaining=3,
            total_players=3
        )

        with pytest.raises(ValueError, match="No cards in hand"):
            await player.decide(game_state)

    @pytest.mark.asyncio
    async def test_decide_with_parse_error(self):
        """Test handling of JSON parse errors."""
        mock_client = AsyncMock()

        # First call returns invalid JSON, should continue to next timestep
        # Second call returns valid play decision
        responses = [
            Mock(choices=[Mock(message=Mock(content="invalid json"))]),
            Mock(choices=[Mock(message=Mock(
                content='{"play": true, "reasoning": "Now playing"}'
            ))])
        ]
        mock_client.chat.completions.create.side_effect = responses

        player = ReactiveLLMPlayer(
            name="ReactiveAI",
            model="gpt-4o-mini",
            client=mock_client,
            timestep_interval=0.5
        )
        player.receive_card(Card(30))

        game_state = GameState(
            round_number=1,
            cards_played=[],
            time_elapsed=0.0,
            players_remaining=3,
            total_players=3
        )

        decision = await player.decide(game_state)

        assert decision.elapsed_time == 0.5
        assert decision.timesteps_checked == 2
        assert "error" in decision.intermediate_decisions[0]

    def test_add_memory(self):
        """Test adding memory to reactive player."""
        mock_client = Mock()
        player = ReactiveLLMPlayer(
            name="ReactiveAI",
            model="gpt-4o-mini",
            client=mock_client,
            use_memory=True
        )

        round_info = RoundInfo(
            round_number=1,
            success=True,
            cards_played=[10, 20, 30],
            player_decisions={}
        )

        player.add_memory(round_info)
        assert len(player.memory) == 1
        assert player.memory[0] == round_info

    def test_add_memory_disabled(self):
        """Test that memory is not added when disabled."""
        mock_client = Mock()
        player = ReactiveLLMPlayer(
            name="ReactiveAI",
            model="gpt-4o-mini",
            client=mock_client,
            use_memory=False
        )

        round_info = RoundInfo(
            round_number=1,
            success=True,
            cards_played=[10, 20, 30],
            player_decisions={}
        )

        player.add_memory(round_info)
        assert len(player.memory) == 0

    def test_get_decision_summary(self):
        """Test getting a human-readable decision summary."""
        mock_client = Mock()
        player = ReactiveLLMPlayer(
            name="ReactiveAI",
            model="gpt-4o-mini",
            client=mock_client
        )
        player.receive_card(Card(42))

        decision = ReactiveDecision(
            elapsed_time=3.5,
            reasoning="Good timing to play",
            timesteps_checked=7,
            intermediate_decisions=[
                {"time": 0.0, "play": False, "reasoning": "Too early"},
                {"time": 0.5, "play": False, "reasoning": "Still waiting"},
                {"time": 3.5, "play": True, "reasoning": "Good timing to play"}
            ]
        )

        summary = player.get_decision_summary(decision)

        assert "ReactiveAI" in summary
        assert "gpt-4o-mini" in summary
        assert "42" in summary
        assert "3.5s" in summary
        assert "7" in summary
        assert "Good timing to play" in summary

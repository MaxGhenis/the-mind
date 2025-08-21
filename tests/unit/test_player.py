"""Unit tests for Player classes."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from themind.core.player import Player, LLMPlayer, PlayerDecision
from themind.core.card import Card
from themind.core.game_state import GameState, RoundInfo


class TestPlayer:
    def test_player_creation(self):
        player = Player("Alice", player_id="p1")
        assert player.name == "Alice"
        assert player.player_id == "p1"
        assert player.hand == []
    
    def test_player_receive_card(self):
        player = Player("Bob")
        card = Card(42)
        player.receive_card(card)
        
        assert len(player.hand) == 1
        assert player.hand[0] == card
    
    def test_player_receive_multiple_cards(self):
        player = Player("Charlie")
        cards = [Card(10), Card(50), Card(30)]
        
        for card in cards:
            player.receive_card(card)
        
        assert len(player.hand) == 3
        assert player.hand == sorted(cards)  # Hand should be sorted
    
    def test_player_play_card(self):
        player = Player("Dave")
        cards = [Card(10), Card(30), Card(50)]
        
        for card in cards:
            player.receive_card(card)
        
        played = player.play_card(Card(30))
        assert played == Card(30)
        assert len(player.hand) == 2
        assert Card(30) not in player.hand
    
    def test_player_play_nonexistent_card(self):
        player = Player("Eve")
        player.receive_card(Card(20))
        
        with pytest.raises(ValueError, match="Card 50 not in hand"):
            player.play_card(Card(50))
    
    def test_player_clear_hand(self):
        player = Player("Frank")
        player.receive_card(Card(10))
        player.receive_card(Card(20))
        
        player.clear_hand()
        assert player.hand == []
    
    def test_player_lowest_card(self):
        player = Player("Grace")
        assert player.lowest_card is None
        
        player.receive_card(Card(50))
        player.receive_card(Card(20))
        player.receive_card(Card(80))
        
        assert player.lowest_card == Card(20)


class TestPlayerDecision:
    def test_decision_creation(self):
        decision = PlayerDecision(
            wait_seconds=5.0,
            reasoning="My card is 50, middle of the range",
            confidence=0.7
        )
        
        assert decision.wait_seconds == 5.0
        assert decision.reasoning == "My card is 50, middle of the range"
        assert decision.confidence == 0.7
    
    def test_decision_validation(self):
        with pytest.raises(ValueError):
            PlayerDecision(wait_seconds=-1.0, reasoning="Invalid")
        
        with pytest.raises(ValueError):
            PlayerDecision(wait_seconds=5.0, reasoning="", confidence=1.5)


class TestLLMPlayer:
    @pytest.mark.asyncio
    async def test_llm_player_creation(self):
        mock_client = Mock()
        player = LLMPlayer("AI_Player", model="gpt-4", client=mock_client)
        
        assert player.name == "AI_Player"
        assert player.model == "gpt-4"
        assert player.client == mock_client
        assert player.memory == []
    
    @pytest.mark.asyncio
    async def test_llm_player_decide(self):
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"wait_seconds": 3.0, "reasoning": "Test reasoning"}'))]
        mock_client.chat.completions.create.return_value = mock_response
        
        player = LLMPlayer("AI_Player", model="gpt-4", client=mock_client)
        player.receive_card(Card(25))
        
        game_state = GameState(
            round_number=1,
            cards_played=[Card(10), Card(20)],
            time_elapsed=5.0,
            players_remaining=3,
            total_players=4
        )
        
        decision = await player.decide(game_state)
        
        assert isinstance(decision, PlayerDecision)
        assert decision.wait_seconds == 3.0
        assert decision.reasoning == "Test reasoning"
        assert mock_client.chat.completions.create.called
    
    @pytest.mark.asyncio
    async def test_llm_player_with_memory(self):
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"wait_seconds": 2.0, "reasoning": "Learning from past"}'))]
        mock_client.chat.completions.create.return_value = mock_response
        
        player = LLMPlayer("AI_Player", model="gpt-4", client=mock_client, use_memory=True)
        player.receive_card(Card(40))
        
        # Add some memory from previous rounds
        player.add_memory(RoundInfo(
            round_number=1,
            success=True,
            cards_played=[10, 20, 30, 40],
            player_decisions={"AI_Player": {"card": 30, "wait": 3.0}}
        ))
        
        game_state = GameState(
            round_number=2,
            cards_played=[Card(15)],
            time_elapsed=2.0,
            players_remaining=3,
            total_players=4
        )
        
        decision = await player.decide(game_state)
        
        assert isinstance(decision, PlayerDecision)
        
        # Check that memory was included in prompt
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert any("previous rounds" in str(msg).lower() for msg in messages)
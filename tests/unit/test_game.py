"""Unit tests for TheMindGame."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from datetime import datetime

from themind.core.game import TheMindGame, GameConfig
from themind.core.player import Player, LLMPlayer
from themind.core.card import Card
from themind.core.game_state import GameState, GameResult, RoundInfo


class TestGameConfig:
    def test_default_config(self):
        config = GameConfig()
        assert config.num_players == 2
        assert config.starting_lives == 3
        assert config.starting_stars == 1
        assert config.max_round_time == 60.0
    
    def test_custom_config(self):
        config = GameConfig(
            num_players=4,
            starting_lives=5,
            max_round_time=30.0
        )
        assert config.num_players == 4
        assert config.starting_lives == 5
        assert config.max_round_time == 30.0
    
    def test_validation(self):
        with pytest.raises(ValueError, match="Number of players must be between 2 and 6"):
            GameConfig(num_players=7)
        
        with pytest.raises(ValueError, match="Number of players must be between 2 and 6"):
            GameConfig(num_players=1)


class TestTheMindGame:
    def test_game_creation(self):
        players = [Player(f"P{i}") for i in range(3)]
        game = TheMindGame(players)
        
        assert len(game.players) == 3
        assert game.current_round == 0
        assert game.lives == 3
        assert game.stars == 1
    
    def test_game_with_config(self):
        players = [Player(f"P{i}") for i in range(2)]
        config = GameConfig(starting_lives=5, starting_stars=2)
        game = TheMindGame(players, config=config)
        
        assert game.lives == 5
        assert game.stars == 2
    
    def test_start_round(self):
        players = [Player(f"P{i}") for i in range(3)]
        game = TheMindGame(players)
        
        game.start_round()
        
        assert game.current_round == 1
        # Each player should have 1 card in round 1
        for player in players:
            assert len(player.hand) == 1
    
    def test_card_distribution(self):
        players = [Player(f"P{i}") for i in range(2)]
        game = TheMindGame(players)
        
        game.start_round()
        game.start_round()  # Round 2
        
        assert game.current_round == 2
        # Each player should have 2 cards in round 2
        for player in players:
            assert len(player.hand) == 2
        
        # All cards should be unique
        all_cards = []
        for player in players:
            all_cards.extend(player.hand)
        card_values = [c.value for c in all_cards]
        assert len(card_values) == len(set(card_values))
    
    @pytest.mark.asyncio
    async def test_play_round_success(self):
        # Create mock LLM players
        players = []
        for i in range(2):
            mock_client = AsyncMock()
            player = LLMPlayer(f"AI_{i}", model="test", client=mock_client)
            players.append(player)
        
        game = TheMindGame(players)
        game.start_round()
        
        # Give players specific cards for controlled testing
        players[0].clear_hand()
        players[1].clear_hand()
        players[0].receive_card(Card(20))
        players[1].receive_card(Card(50))
        
        # Mock decision making - lower card plays first
        async def mock_decide_p0(game_state):
            from themind.core.player import PlayerDecision
            return PlayerDecision(wait_seconds=1.0, reasoning="I have 20")
        
        async def mock_decide_p1(game_state):
            from themind.core.player import PlayerDecision
            return PlayerDecision(wait_seconds=3.0, reasoning="I have 50")
        
        players[0].decide = mock_decide_p0
        players[1].decide = mock_decide_p1
        
        result = await game.play_round()
        
        assert result.success is True
        assert result.cards_played == [20, 50]
        assert game.lives == 3  # No lives lost
    
    @pytest.mark.asyncio
    async def test_play_round_failure(self):
        # Create mock LLM players
        players = []
        for i in range(2):
            mock_client = AsyncMock()
            player = LLMPlayer(f"AI_{i}", model="test", client=mock_client)
            players.append(player)
        
        game = TheMindGame(players)
        game.start_round()
        
        # Give players specific cards for controlled testing
        players[0].clear_hand()
        players[1].clear_hand()
        players[0].receive_card(Card(50))  # Higher card
        players[1].receive_card(Card(20))  # Lower card
        
        # Mock decision making - higher card plays first (wrong!)
        async def mock_decide_p0(game_state):
            from themind.core.player import PlayerDecision
            return PlayerDecision(wait_seconds=0.5, reasoning="Playing quickly")
        
        async def mock_decide_p1(game_state):
            from themind.core.player import PlayerDecision
            return PlayerDecision(wait_seconds=2.0, reasoning="Waiting longer")
        
        players[0].decide = mock_decide_p0
        players[1].decide = mock_decide_p1
        
        result = await game.play_round()
        
        assert result.success is False
        assert 50 in result.cards_played  # The wrong card was played
        assert game.lives == 2  # Lost a life
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_full_game(self):
        # Create mock LLM players
        players = []
        for i in range(2):
            mock_client = AsyncMock()
            player = LLMPlayer(f"AI_{i}", model="test", client=mock_client)
            players.append(player)
        
        game = TheMindGame(players)
        
        # Mock perfect play
        async def mock_perfect_decide(self, game_state):
            from themind.core.player import PlayerDecision
            # Play cards in perfect order based on value
            wait = self.lowest_card.value / 10.0 if self.lowest_card else 0
            return PlayerDecision(
                wait_seconds=wait,
                reasoning=f"Card {self.lowest_card.value if self.lowest_card else 'none'}"
            )
        
        for player in players:
            player.decide = lambda gs, p=player: mock_perfect_decide(p, gs)
        
        result = await game.play()
        
        assert isinstance(result, GameResult)
        assert result.num_players == 2
        assert result.rounds_completed > 0
        assert result.final_lives > 0  # Should have lives left with perfect play
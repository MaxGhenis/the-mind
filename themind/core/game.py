"""The Mind game implementation."""

import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4
from datetime import datetime

from themind.core.card import Card, Deck
from themind.core.player import Player, LLMPlayer, PlayerDecision
from themind.core.game_state import GameState, GameResult, RoundInfo


@dataclass
class GameConfig:
    """Configuration for a game of The Mind."""
    
    num_players: int = 2
    starting_lives: int = 3
    starting_stars: int = 1
    max_round_time: float = 60.0
    use_learning: bool = False
    seed: Optional[int] = None
    
    def __post_init__(self) -> None:
        if not 2 <= self.num_players <= 6:
            raise ValueError(f"Number of players must be between 2 and 6, got {self.num_players}")


class TheMindGame:
    """The Mind game controller."""
    
    def __init__(
        self,
        players: List[Player],
        config: Optional[GameConfig] = None
    ) -> None:
        self.players = players
        self.config = config or GameConfig(num_players=len(players))
        self.game_id = str(uuid4())
        
        # Game state
        self.current_round = 0
        self.lives = self.config.starting_lives
        self.stars = self.config.starting_stars
        self.deck = Deck()
        self.rounds_data: List[RoundInfo] = []
        
        # Timing
        self.game_start_time = time.time()
    
    def start_round(self) -> None:
        """Start a new round."""
        self.current_round += 1
        self.deck.reset()
        self.deck.shuffle(seed=self.config.seed)
        
        # Clear hands and deal cards
        for player in self.players:
            player.clear_hand()
        
        # Each player gets cards equal to the round number
        for _ in range(self.current_round):
            for player in self.players:
                if len(self.deck) > 0:
                    cards = self.deck.deal(1)
                    if cards:
                        player.receive_card(cards[0])
    
    async def play_round(self) -> RoundInfo:
        """Play a single round of the game."""
        round_start = time.time()
        cards_played: List[Card] = []
        player_decisions: Dict[str, Dict[str, Any]] = {}
        errors: List[str] = []
        
        # Create a list of all cards that need to be played
        all_cards: List[Tuple[Card, Player]] = []
        for player in self.players:
            for card in player.hand:
                all_cards.append((card, player))
        
        # Sort by card value to check for correct play order
        all_cards.sort(key=lambda x: x[0].value)
        correct_order = [card.value for card, _ in all_cards]
        
        # Simulate players making decisions concurrently
        active_players = self.players.copy()
        time_elapsed = 0.0
        
        while active_players and time_elapsed < self.config.max_round_time:
            # Get current game state
            game_state = GameState(
                round_number=self.current_round,
                cards_played=cards_played.copy(),
                time_elapsed=time_elapsed,
                players_remaining=len(active_players),
                total_players=len(self.players),
                lives_remaining=self.lives,
                stars_remaining=self.stars
            )
            
            # Get decisions from all active players
            decision_tasks = []
            for player in active_players:
                if player.hand:  # Only if player has cards
                    if isinstance(player, LLMPlayer):
                        decision_tasks.append((player, player.decide(game_state)))
                    else:
                        # For non-LLM players, create a simple decision
                        simple_decision = PlayerDecision(
                            wait_seconds=player.lowest_card.value / 5.0,
                            reasoning="Simple heuristic"
                        )
                        decision_tasks.append((player, asyncio.create_task(
                            asyncio.coroutine(lambda: simple_decision)()
                        )))
            
            if not decision_tasks:
                break
            
            # Wait for all decisions
            decisions = []
            for player, task in decision_tasks:
                try:
                    if asyncio.iscoroutine(task):
                        decision = await task
                    else:
                        decision = await task
                    decisions.append((player, decision))
                    player_decisions[player.name] = {
                        "card": player.lowest_card.value if player.lowest_card else None,
                        "wait": decision.wait_seconds,
                        "reasoning": decision.reasoning
                    }
                except Exception as e:
                    errors.append(f"Error getting decision from {player.name}: {e}")
                    # Use a default decision on error
                    decisions.append((player, PlayerDecision(
                        wait_seconds=10.0,
                        reasoning="Error - using default"
                    )))
            
            # Find who plays next (shortest wait time)
            if decisions:
                next_player, next_decision = min(decisions, key=lambda x: x[1].wait_seconds)
                
                # Play the card
                if next_player.lowest_card:
                    played_card = next_player.play_card(next_player.lowest_card)
                    cards_played.append(played_card)
                    
                    # Check if this was the correct card to play
                    if cards_played[-1].value != correct_order[len(cards_played) - 1]:
                        errors.append(
                            f"Wrong order! Played {cards_played[-1].value}, "
                            f"should have played {correct_order[len(cards_played) - 1]}"
                        )
                        self.lives -= 1
                        break  # End round on mistake
                
                # Update time
                time_elapsed += next_decision.wait_seconds
                
                # Remove player if they have no more cards
                if not next_player.hand:
                    active_players.remove(next_player)
        
        # Determine success
        success = len(errors) == 0 and len(cards_played) == len(correct_order)
        
        round_info = RoundInfo(
            round_number=self.current_round,
            success=success,
            cards_played=[c.value for c in cards_played],
            player_decisions=player_decisions,
            time_taken=time.time() - round_start,
            errors=errors
        )
        
        # Add to memory if using learning
        if self.config.use_learning:
            for player in self.players:
                if isinstance(player, LLMPlayer) and player.use_memory:
                    player.add_memory(round_info)
        
        self.rounds_data.append(round_info)
        return round_info
    
    async def play(self) -> GameResult:
        """Play a complete game."""
        max_rounds = 12  # Typical max for The Mind
        
        while self.current_round < max_rounds and self.lives > 0:
            self.start_round()
            round_result = await self.play_round()
            
            if not round_result.success and self.lives <= 0:
                break
            
            # Award star after certain rounds
            if self.current_round in [3, 6, 9] and round_result.success:
                self.stars += 1
        
        # Create game result
        model_config = {}
        for player in self.players:
            if isinstance(player, LLMPlayer):
                model_config[player.name] = player.model
            else:
                model_config[player.name] = "human"
        
        result = GameResult(
            game_id=self.game_id,
            timestamp=datetime.now(),
            model_config=model_config,
            num_players=len(self.players),
            rounds_completed=self.current_round,
            rounds_data=self.rounds_data,
            success=self.lives > 0,
            total_time=time.time() - self.game_start_time,
            final_lives=self.lives,
            final_stars=self.stars
        )
        
        return result
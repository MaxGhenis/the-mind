"""Game state representations for The Mind."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from themind.core.card import Card


@dataclass
class GameState:
    """Current state of the game."""
    
    round_number: int
    cards_played: List[Card]
    time_elapsed: float
    players_remaining: int
    total_players: int
    lives_remaining: int = 3
    stars_remaining: int = 1
    
    @property
    def last_played_card(self) -> Optional[Card]:
        """Get the last played card."""
        return self.cards_played[-1] if self.cards_played else None
    
    @property
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.lives_remaining <= 0


@dataclass
class RoundInfo:
    """Information about a completed round."""
    
    round_number: int
    success: bool
    cards_played: List[int]
    player_decisions: Dict[str, Dict[str, Any]]
    time_taken: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "round_number": self.round_number,
            "success": self.success,
            "cards_played": self.cards_played,
            "player_decisions": self.player_decisions,
            "time_taken": self.time_taken,
            "errors": self.errors
        }


@dataclass
class GameResult:
    """Result of a complete game."""
    
    game_id: str
    timestamp: datetime
    model_config: Dict[str, str]  # model names for each player
    num_players: int
    rounds_completed: int
    rounds_data: List[RoundInfo]
    success: bool
    total_time: float
    final_lives: int
    final_stars: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "game_id": self.game_id,
            "timestamp": self.timestamp.isoformat(),
            "model_config": self.model_config,
            "num_players": self.num_players,
            "rounds_completed": self.rounds_completed,
            "rounds_data": [r.to_dict() for r in self.rounds_data],
            "success": self.success,
            "total_time": self.total_time,
            "final_lives": self.final_lives,
            "final_stars": self.final_stars
        }
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of completed rounds."""
        if not self.rounds_data:
            return 0.0
        successful = sum(1 for r in self.rounds_data if r.success)
        return successful / len(self.rounds_data)
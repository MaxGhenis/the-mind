"""Card and Deck implementations for The Mind game."""

import random
from dataclasses import dataclass
from typing import List


@dataclass
class Card:
    """A playing card with a numeric value."""
    
    value: int
    
    def __post_init__(self) -> None:
        if not 1 <= self.value <= 100:
            raise ValueError(f"Card value must be between 1 and 100, got {self.value}")
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __repr__(self) -> str:
        return f"Card({self.value})"
    
    def __lt__(self, other: "Card") -> bool:
        return self.value < other.value
    
    def __le__(self, other: "Card") -> bool:
        return self.value <= other.value
    
    def __gt__(self, other: "Card") -> bool:
        return self.value > other.value
    
    def __ge__(self, other: "Card") -> bool:
        return self.value >= other.value
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.value == other.value
    
    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.value != other.value


class Deck:
    """A deck of cards for The Mind game."""
    
    def __init__(self, min_value: int = 1, max_value: int = 100) -> None:
        self.min_value = min_value
        self.max_value = max_value
        self.cards: List[Card] = []
        self.reset()
    
    def reset(self) -> None:
        """Reset the deck to its initial state."""
        self.cards = [Card(i) for i in range(self.min_value, self.max_value + 1)]
    
    def shuffle(self, seed: int | None = None) -> None:
        """Shuffle the deck."""
        if seed is not None:
            random.seed(seed)
        random.shuffle(self.cards)
    
    def deal(self, num_cards: int) -> List[Card]:
        """Deal a specified number of cards from the deck."""
        if num_cards > len(self.cards):
            raise ValueError(f"Not enough cards in deck. Requested {num_cards}, have {len(self.cards)}")
        
        dealt_cards = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt_cards
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __repr__(self) -> str:
        return f"Deck({len(self.cards)} cards)"
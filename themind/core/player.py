"""Player implementations for The Mind game."""

import json
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from uuid import uuid4

from themind.core.card import Card
from themind.core.game_state import GameState, RoundInfo


@dataclass
class PlayerDecision:
    """A player's decision in the game."""
    
    wait_seconds: float
    reasoning: str
    confidence: float = 0.5
    
    def __post_init__(self) -> None:
        if self.wait_seconds < 0:
            raise ValueError("Wait time cannot be negative")
        if not self.reasoning:
            raise ValueError("Reasoning cannot be empty")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")


class Player:
    """Base player class for The Mind game."""
    
    def __init__(self, name: str, player_id: Optional[str] = None) -> None:
        self.name = name
        self.player_id = player_id or str(uuid4())
        self.hand: List[Card] = []
    
    def receive_card(self, card: Card) -> None:
        """Receive a card and add it to hand."""
        self.hand.append(card)
        self.hand.sort()
    
    def play_card(self, card: Card) -> Card:
        """Play a card from hand."""
        if card not in self.hand:
            raise ValueError(f"Card {card.value} not in hand")
        self.hand.remove(card)
        return card
    
    def clear_hand(self) -> None:
        """Clear all cards from hand."""
        self.hand = []
    
    @property
    def lowest_card(self) -> Optional[Card]:
        """Get the lowest card in hand."""
        return self.hand[0] if self.hand else None
    
    def __repr__(self) -> str:
        return f"Player({self.name}, {len(self.hand)} cards)"


class LLMPlayer(Player):
    """LLM-powered player for The Mind game."""
    
    def __init__(
        self,
        name: str,
        model: str,
        client: Any,
        player_id: Optional[str] = None,
        use_memory: bool = False,
        temperature: float = 0.7,
    ) -> None:
        super().__init__(name, player_id)
        self.model = model
        self.client = client
        self.use_memory = use_memory
        self.temperature = temperature
        self.memory: List[RoundInfo] = []
    
    def add_memory(self, round_info: RoundInfo) -> None:
        """Add a round to memory for learning."""
        if self.use_memory:
            self.memory.append(round_info)
            # Keep only last 10 rounds to avoid context overflow
            if len(self.memory) > 10:
                self.memory = self.memory[-10:]
    
    async def decide(self, game_state: GameState) -> PlayerDecision:
        """Decide how long to wait before playing lowest card."""
        if not self.hand:
            raise ValueError("No cards in hand")
        
        prompt = self._build_prompt(game_state)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        
        decision_data = json.loads(response.choices[0].message.content)
        
        return PlayerDecision(
            wait_seconds=float(decision_data["wait_seconds"]),
            reasoning=decision_data["reasoning"],
            confidence=decision_data.get("confidence", 0.5)
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """You are playing The Mind, a cooperative card game where players must play cards in ascending order without communication.

You must decide how long to wait before playing your lowest card based on:
1. Your card's value (1-100)
2. Cards already played
3. Time elapsed
4. Number of players remaining

Respond with JSON:
{
    "wait_seconds": <float between 0 and 30>,
    "reasoning": "<your strategic reasoning>",
    "confidence": <float between 0 and 1>
}

Strategy tips:
- Lower cards should be played sooner
- Higher cards should wait longer
- Consider the gap between your card and the last played card
- Account for other players who might have lower cards"""
    
    def _build_prompt(self, game_state: GameState) -> str:
        """Build the prompt for the LLM."""
        prompt_parts = [
            f"Round {game_state.round_number}",
            f"Your lowest card: {self.lowest_card.value}",
            f"Cards played so far: {[c.value for c in game_state.cards_played]}",
            f"Time elapsed: {game_state.time_elapsed:.1f} seconds",
            f"Players remaining: {game_state.players_remaining}/{game_state.total_players}",
        ]
        
        if self.use_memory and self.memory:
            memory_summary = self._summarize_memory()
            prompt_parts.append(f"\nLearning from previous rounds:\n{memory_summary}")
        
        prompt_parts.append("\nHow long should you wait before playing your card?")
        
        return "\n".join(prompt_parts)
    
    def _summarize_memory(self) -> str:
        """Summarize memory from previous rounds."""
        if not self.memory:
            return "No previous rounds"
        
        summaries = []
        for round_info in self.memory[-3:]:  # Last 3 rounds
            status = "SUCCESS" if round_info.success else "FAILURE"
            summaries.append(
                f"Round {round_info.round_number}: {status} - "
                f"Cards played: {round_info.cards_played}"
            )
        
        return "\n".join(summaries)
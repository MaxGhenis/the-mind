"""Player implementations for The Mind game."""

import json
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from uuid import uuid4

from themind.core.card import Card
from themind.core.game_state import GameState, RoundInfo
from themind.prompts.prediction import (
    get_prediction_system_prompt,
    build_prediction_user_prompt,
    parse_prediction_response,
)


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
        prompting_strategy: str = "prediction",
    ) -> None:
        super().__init__(name, player_id)
        self.model = model
        self.client = client
        self.use_memory = use_memory
        self.temperature = temperature
        self.prompting_strategy = prompting_strategy
        self.memory: List[RoundInfo] = []

        # Validate prompting strategy
        if prompting_strategy != "prediction":
            raise ValueError(
                f"Unsupported prompting strategy: {prompting_strategy}. "
                "Currently only 'prediction' is supported."
            )
    
    def add_memory(self, round_info: RoundInfo) -> None:
        """Add a round to memory for learning."""
        if self.use_memory:
            self.memory.append(round_info)
            # Keep only last 10 rounds to avoid context overflow
            if len(self.memory) > 10:
                self.memory = self.memory[-10:]
    
    async def decide(self, game_state: GameState) -> PlayerDecision:
        """Decide how long to wait before playing lowest card.

        Args:
            game_state: Current state of the game

        Returns:
            PlayerDecision with wait time, reasoning, and confidence

        Raises:
            ValueError: If hand is empty
        """
        if not self.hand:
            raise ValueError("No cards in hand")

        # Build prompts using the prediction strategy module
        system_prompt = get_prediction_system_prompt()
        user_prompt = build_prediction_user_prompt(
            game_state=game_state,
            my_card=self.lowest_card,
            memory=self.memory if self.use_memory else None,
        )

        # Call LLM
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )

        # Parse response using the prediction module
        decision_data = parse_prediction_response(response.choices[0].message.content)

        return PlayerDecision(
            wait_seconds=decision_data["wait_seconds"],
            reasoning=decision_data["reasoning"],
            confidence=decision_data["confidence"]
        )

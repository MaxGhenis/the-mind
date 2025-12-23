"""Reactive LLM player implementation for The Mind game.

This player uses a reactive strategy where the LLM is queried at each timestep
to decide whether to play now, rather than predicting wait time upfront.
"""

import json
import asyncio
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from themind.core.player import Player
from themind.core.card import Card
from themind.core.game_state import GameState, RoundInfo
from themind.prompts import reactive


@dataclass
class ReactiveDecision:
    """Result of a reactive decision process."""

    elapsed_time: float
    reasoning: str
    timesteps_checked: int
    intermediate_decisions: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "elapsed_time": self.elapsed_time,
            "reasoning": self.reasoning,
            "timesteps_checked": self.timesteps_checked,
            "intermediate_decisions": self.intermediate_decisions
        }


class ReactiveLLMPlayer(Player):
    """LLM player using reactive decision-making strategy.

    Instead of predicting wait time, this player simulates time passing
    and asks the LLM at each timestep: "Do you play now?"
    """

    def __init__(
        self,
        name: str,
        model: str,
        client: Any,
        player_id: Optional[str] = None,
        use_memory: bool = False,
        temperature: float = 0.7,
        timestep_interval: float = 0.5,
        max_time: float = 30.0,
    ) -> None:
        """Initialize reactive LLM player.

        Args:
            name: Player name
            model: LLM model identifier
            client: LLM client (expectedparrot wrapper)
            player_id: Optional unique player ID
            use_memory: Whether to use memory from previous rounds
            temperature: LLM temperature parameter
            timestep_interval: Seconds between decision checks (default 0.5)
            max_time: Maximum time to wait before forcing play (default 30.0)
        """
        super().__init__(name, player_id)
        self.model = model
        self.client = client
        self.use_memory = use_memory
        self.temperature = temperature
        self.timestep_interval = timestep_interval
        self.max_time = max_time
        self.memory: List[RoundInfo] = []

    def add_memory(self, round_info: RoundInfo) -> None:
        """Add a round to memory for learning.

        Args:
            round_info: Information about completed round
        """
        if self.use_memory:
            self.memory.append(round_info)
            # Keep only last 10 rounds to avoid context overflow
            if len(self.memory) > 10:
                self.memory = self.memory[-10:]

    async def decide(self, game_state: GameState) -> ReactiveDecision:
        """Decide when to play using reactive timestep queries.

        Args:
            game_state: Current game state

        Returns:
            ReactiveDecision with elapsed time and reasoning

        Raises:
            ValueError: If no cards in hand
        """
        if not self.hand:
            raise ValueError("No cards in hand")

        player_card = self.lowest_card
        current_time = 0.0
        timesteps = 0
        intermediate_decisions = []

        # Simulate time passing and ask at each timestep
        while current_time < self.max_time:
            timesteps += 1

            # Build prompt for this timestep
            prompt = reactive.build_timestep_prompt(
                game_state=game_state,
                player_card=player_card,
                elapsed_seconds=current_time
            )

            # Add memory context if enabled
            if self.use_memory and self.memory:
                memory_context = reactive.get_memory_context(
                    [r.to_dict() for r in self.memory]
                )
                if memory_context:
                    prompt = prompt + "\n" + memory_context

            # Query the LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": reactive.get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            # Parse response
            response_text = response.choices[0].message.content
            try:
                decision_data = reactive.parse_response(response_text)
            except ValueError as e:
                # If parsing fails, wait and try again
                intermediate_decisions.append({
                    "time": current_time,
                    "error": str(e),
                    "raw_response": response_text
                })
                current_time += self.timestep_interval
                continue

            # Record this decision
            intermediate_decisions.append({
                "time": current_time,
                "play": decision_data["play"],
                "reasoning": decision_data["reasoning"]
            })

            # If LLM says to play, return now
            if decision_data["play"]:
                return ReactiveDecision(
                    elapsed_time=current_time,
                    reasoning=decision_data["reasoning"],
                    timesteps_checked=timesteps,
                    intermediate_decisions=intermediate_decisions
                )

            # Otherwise, advance time and check again
            current_time += self.timestep_interval

        # Max time reached, must play now
        return ReactiveDecision(
            elapsed_time=self.max_time,
            reasoning=f"Maximum time ({self.max_time}s) reached, must play now",
            timesteps_checked=timesteps,
            intermediate_decisions=intermediate_decisions
        )

    def get_decision_summary(self, decision: ReactiveDecision) -> str:
        """Get a human-readable summary of a reactive decision.

        Args:
            decision: The reactive decision to summarize

        Returns:
            Formatted string summary
        """
        lines = [
            f"Player {self.name} ({self.model}):",
            f"  Card: {self.lowest_card.value}",
            f"  Decision: Play after {decision.elapsed_time:.1f}s",
            f"  Timesteps checked: {decision.timesteps_checked}",
            f"  Final reasoning: {decision.reasoning}",
        ]

        if decision.timesteps_checked > 1:
            lines.append(f"\n  Decision history:")
            for i, step in enumerate(decision.intermediate_decisions[-5:], 1):
                if "error" in step:
                    lines.append(f"    {step['time']:.1f}s: ERROR - {step['error']}")
                else:
                    action = "PLAY" if step["play"] else "WAIT"
                    lines.append(f"    {step['time']:.1f}s: {action} - {step['reasoning'][:60]}...")

        return "\n".join(lines)

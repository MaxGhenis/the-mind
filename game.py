from typing import List, Dict, Tuple
from openai import OpenAI
import random


class LLMPlayer:
    def __init__(self, name: str, client: OpenAI):
        self.name = name
        self.card: int = None
        self.client = client

    def receive_card(self, card: int):
        self.card = card

    def decide_action(self, game_state: dict) -> Tuple[float, str, str]:
        prompt = self._create_prompt(game_state)

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI playing a simplified version of 'The Mind' card game. Respond with only a number representing seconds to wait.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        decision = response.choices[0].message.content.strip()

        try:
            wait_time = float(decision)
        except ValueError:
            wait_time = random.uniform(
                1, 5
            )  # Default wait time if parsing fails

        return wait_time, prompt, decision

    def _create_prompt(self, game_state: dict) -> str:
        moves_description = "\n".join(
            [
                f"- At {move['time']:.1f} seconds: {move['player']} played {move['card']}"
                for move in game_state["moves"]
            ]
        )
        return f"""
        You are playing a simplified version of 'The Mind' card game. Your goal is to play cards in ascending order without communicating.
        
        Key rules and strategy:
        1. Cards must be played in ascending order.
        2. You should try to play your card after players with lower numbers have played theirs.
        3. You should try to play your card before players with higher numbers play theirs.
        4. Generally, if you have a higher card, you should wait longer before playing.
        5. Use the information about cards already played and time passed to estimate when to play your card.

        Current game state:
        - Your name: {self.name}
        - Your card: {self.card}
        - Time passed in this game: {game_state['time_passed']:.1f} seconds
        - Players left with cards: {game_state['players_with_cards']}
        - Moves made this game:
        {moves_description}

        Based on this information and the game rules, decide how long to wait from this moment before playing your card ({self.card}).
        Respond with only a single number representing the number of seconds to wait (e.g., '3.5').
        """


class TheMindGame:
    def __init__(self, player_names: List[str], client: OpenAI):
        self.players = [LLMPlayer(name, client) for name in player_names]
        self.played_cards: List[Dict] = []
        self.time_passed: float = 0
        self.llm_logs: List[Tuple[str, str, str]] = []
        self.debug_logs: List[str] = []

    def log(self, message: str):
        self.debug_logs.append(message)

    def setup_game(self):
        cards = random.sample(range(1, 101), len(self.players))
        for player, card in zip(self.players, cards):
            player.receive_card(card)
        self.log(
            f"Initial game state: {[(p.name, p.card) for p in self.players]}"
        )

    def play_game(
        self,
    ) -> Tuple[
        Tuple[bool, List[Dict], List[Tuple[str, int]]],
        List[Tuple[str, str, str]],
        List[str],
    ]:
        self.setup_game()
        players_left = sorted(self.players, key=lambda p: p.card)
        self.log(
            f"Players sorted by card value: {[(p.name, p.card) for p in players_left]}"
        )

        while players_left:
            game_state = {
                "time_passed": self.time_passed,
                "players_with_cards": len(players_left),
                "moves": self.played_cards,
            }
            self.log(f"Current game state: {game_state}")

            actions = []
            for player in players_left:
                wait_time, prompt, decision = player.decide_action(game_state)
                actions.append((player, wait_time))
                self.llm_logs.append((player.name, prompt, decision))
                self.log(f"{player.name} decided to wait {wait_time} seconds")

            actions.sort(key=lambda x: x[1])  # Sort by wait time
            self.log(f"Sorted actions: {[(a[0].name, a[1]) for a in actions]}")

            player, wait_time = actions[0]
            self.time_passed += wait_time
            self.log(
                f"Player {player.name} is playing card {player.card} at time {self.time_passed:.1f}"
            )

            # Check if the card being played is the lowest card left
            if player.card != min(p.card for p in players_left):
                unplayed_cards = [
                    (p.name, p.card) for p in players_left if p != player
                ]
                self.log(
                    f"Game over. Card {player.card} played out of order. Unplayed cards: {unplayed_cards}"
                )
                return (
                    (
                        False,
                        self.played_cards
                        + [
                            {
                                "time": self.time_passed,
                                "player": player.name,
                                "card": player.card,
                            }
                        ],
                        unplayed_cards,
                    ),
                    self.llm_logs,
                    self.debug_logs,
                )

            self.played_cards.append(
                {
                    "time": self.time_passed,
                    "player": player.name,
                    "card": player.card,
                }
            )
            players_left.remove(player)

            self.log(
                f"Current game state: Played cards: {self.played_cards}, Players left: {[(p.name, p.card) for p in players_left]}"
            )

            if len(self.played_cards) == len(self.players) - 1:
                self.log(
                    f"Round completed successfully. Last card: {players_left[0].name}: {players_left[0].card}"
                )
                break

        return (
            (
                True,
                self.played_cards,
                (
                    [(players_left[0].name, players_left[0].card)]
                    if players_left
                    else []
                ),
            ),
            self.llm_logs,
            self.debug_logs,
        )

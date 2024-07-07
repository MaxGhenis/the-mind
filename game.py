import random
from typing import List, Dict, Tuple
import openai


class LLMPlayer:
    def __init__(self, name: str):
        self.name = name
        self.card: int = None

    def receive_card(self, card: int):
        self.card = card

    def decide_action(self, game_state: dict) -> float:
        prompt = self._create_prompt(game_state)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI playing a simplified version of 'The Mind' card game. Respond with only a number representing seconds to wait.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        decision = response.choices[0].message["content"].strip()

        try:
            wait_time = float(decision)
        except ValueError:
            wait_time = random.uniform(
                1, 5
            )  # Default wait time if parsing fails

        return wait_time

    def _create_prompt(self, game_state: dict) -> str:
        moves_description = "\n".join(
            [
                f"- At {move['time']:.1f} seconds: {move['player']} played {move['card']}"
                for move in game_state["moves"]
            ]
        )
        return f"""
        You are playing a simplified version of 'The Mind' card game. Your goal is to play cards in ascending order without communicating.
        Current game state:
        - Your name: {self.name}
        - Your card: {self.card}
        - Time passed in this game: {game_state['time_passed']:.1f} seconds
        - Players left with cards: {game_state['players_with_cards']}
        - Moves made this game:
        {moves_description}

        Decide how long to wait from this moment before playing your card ({self.card}).
        Respond with only a single number representing the number of seconds to wait (e.g., '3.5').
        """


class TheMindGame:
    def __init__(self, player_names: List[str]):
        self.players = [LLMPlayer(name) for name in player_names]
        self.played_cards: List[Dict] = []
        self.time_passed: float = 0

    def setup_game(self):
        cards = random.sample(range(1, 101), len(self.players))
        for player, card in zip(self.players, cards):
            player.receive_card(card)

    def play_game(self) -> Tuple[bool, List[Dict], List[Tuple[str, int]]]:
        self.setup_game()
        players_left = self.players.copy()

        while players_left:
            game_state = {
                "time_passed": self.time_passed,
                "players_with_cards": len(players_left),
                "moves": self.played_cards,
            }

            actions = [
                (player, player.decide_action(game_state))
                for player in players_left
            ]
            actions.sort(key=lambda x: x[1])  # Sort by wait time

            player, wait_time = actions[0]
            self.time_passed += wait_time

            if (
                self.played_cards
                and player.card < self.played_cards[-1]["card"]
            ):
                unplayed_cards = [
                    (p.name, p.card) for p in players_left if p != player
                ]
                return (
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
                )

            self.played_cards.append(
                {
                    "time": self.time_passed,
                    "player": player.name,
                    "card": player.card,
                }
            )
            players_left.remove(player)

            if len(self.played_cards) == len(self.players) - 1:
                break

        return True, self.played_cards, []

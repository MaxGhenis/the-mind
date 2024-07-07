import random
from typing import List, Tuple
from player import LLMPlayer
from utils import generate_fun_name


class TheMindGame:
    def __init__(self, num_players: int):
        self.players = self._create_unique_players(num_players)
        self.played_cards: List[int] = []
        self.start_time = 0
        self.llm_logs = []

    def _create_unique_players(self, num_players: int) -> List[LLMPlayer]:
        names = set()
        players = []
        for _ in range(num_players):
            while True:
                name = generate_fun_name()
                if name not in names:
                    names.add(name)
                    players.append(LLMPlayer(name))
                    break
        return players

    def setup_game(self):
        cards = random.sample(range(1, 101), len(self.players))
        self.played_cards = []
        self.start_time = 0

        for player, card in zip(self.players, cards):
            player.receive_card(card)

    def play_game(
        self,
    ) -> Tuple[bool, List[Tuple[float, int, str]], List[Tuple[str, int]]]:
        self.setup_game()
        players_ready = self.players.copy()
        cards_played_this_game = []
        time_passed = 0

        # Get initial decisions from all players
        for player in players_ready:
            game_state = {
                "time_passed": time_passed,
                "players_with_cards": len(players_ready),
                "moves": cards_played_this_game,
            }
            wait_time, prompt, decision = player.decide_action(game_state)
            self.llm_logs.append((player.name, prompt, decision))

        # Sort players by their wait times
        players_ready.sort(key=lambda p: p.wait_time)

        for i, player in enumerate(players_ready):
            time_passed += player.wait_time
            card = player.play_card()
            cards_played_this_game.append((time_passed, card, player.name))

            if self.played_cards and card < max(self.played_cards):
                unplayed_cards = [
                    (p.name, p.card) for p in players_ready[i + 1 :]
                ]
                return False, cards_played_this_game, unplayed_cards

            self.played_cards.append(card)

            if len(self.played_cards) == len(self.players) - 1:
                break

        return True, cards_played_this_game, []

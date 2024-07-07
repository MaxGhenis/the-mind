import random
from typing import List, Tuple
from player import LLMPlayer
from utils import generate_fun_name


class TheMindGame:
    def __init__(self, num_players: int):
        self.players = self._create_unique_players(num_players)
        self.max_level = 12
        self.current_level = 1
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

    def setup_level(self):
        cards = random.sample(range(1, 101), len(self.players))
        self.played_cards = []
        self.start_time = 0

        for player, card in zip(self.players, cards):
            player.receive_card(card)

    def play_round(
        self,
    ) -> Tuple[bool, List[Tuple[float, int, str]], List[Tuple[str, int]]]:
        players_ready = self.players.copy()
        cards_played_this_round = []
        time_passed = 0

        for i, player in enumerate(players_ready):
            game_state = {
                "current_level": self.current_level,
                "time_passed": time_passed,
                "players_with_cards": len(players_ready) - i,
                "moves": cards_played_this_round,
            }
            wait_time, prompt, decision = player.decide_action(game_state)
            self.llm_logs.append((player.name, prompt, decision))

            time_passed += wait_time
            card = player.play_card()
            cards_played_this_round.append((time_passed, card, player.name))

            if self.played_cards and card < max(self.played_cards):
                unplayed_cards = [
                    (p.name, p.card) for p in players_ready[i + 1 :]
                ]
                return False, cards_played_this_round, unplayed_cards

            self.played_cards.append(card)

            if len(self.played_cards) == len(self.players) - 1:
                break

        return True, cards_played_this_round, []

    def play_game(self):
        all_rounds_data = []

        while self.current_level <= self.max_level:
            self.setup_level()
            success, round_data, unplayed_cards = self.play_round()
            all_rounds_data.append(
                (self.current_level, success, round_data, unplayed_cards)
            )

            if success:
                self.current_level += 1
            else:
                break

        return all_rounds_data

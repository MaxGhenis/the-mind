import streamlit as st
import random
import time
from typing import List, Tuple
import openai
import heapq

# Set up your OpenAI API key using Streamlit secrets
openai.api_key = st.secrets["OPENAI_KEY"]


def generate_fun_name():
    adjectives = [
        "Clever",
        "Witty",
        "Brainy",
        "Quirky",
        "Zany",
        "Sassy",
        "Nerdy",
        "Goofy",
        "Peppy",
        "Spunky",
    ]
    nouns = [
        "Bot",
        "AI",
        "Thinker",
        "Whiz",
        "Genius",
        "Mind",
        "Brain",
        "Sage",
        "Guru",
        "Maven",
    ]
    return f"{random.choice(adjectives)} {random.choice(nouns)}"


class LLMPlayer:
    def __init__(self, name: str):
        self.name = name
        self.card: int = None

    def receive_card(self, card: int):
        self.card = card

    def play_card(self) -> int:
        played_card = self.card
        self.card = None
        return played_card

    def decide_action(self, game_state: dict) -> Tuple[float, str]:
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

        # Add a small random factor to the wait time to handle ties
        wait_time += random.uniform(0, 0.1)

        return wait_time, prompt, decision

    def _create_prompt(self, game_state: dict) -> str:
        moves_description = "\n".join(
            [
                f"- At {move[0]:.1f} seconds: {move[2]} played {move[1]}"
                for move in game_state["moves"]
            ]
        )
        return f"""
        You are playing a simplified version of 'The Mind' card game. Your goal is to play cards in ascending order without communicating.
        Current game state:
        - Your name: {self.name}
        - Your card: {self.card}
        - Current level: {game_state['current_level']}
        - Time passed in this level: {game_state['time_passed']:.1f} seconds
        - Players left with cards: {game_state['players_with_cards']}
        - Moves made this level:
        {moves_description}

        Decide how long to wait from this moment before playing your card ({self.card}).
        Respond with only a single number representing the number of seconds to wait (e.g., '3.5').
        """


class TheMindGame:
    def __init__(self, num_players: int):
        self.players = self._create_unique_players(num_players)
        self.max_level = 12
        self.current_level = 1
        self.played_cards: List[int] = []
        self.start_time = time.time()
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
        self.start_time = time.time()

        for player, card in zip(self.players, cards):
            player.receive_card(card)

    def play_round(
        self,
    ) -> Tuple[bool, List[Tuple[float, int, str]], List[Tuple[str, int]]]:
        players_ready = self.players.copy()
        cards_played_this_round = []
        time_passed = 0

        while players_ready:
            action_queue = []
            for player in players_ready:
                game_state = {
                    "current_level": self.current_level,
                    "time_passed": time_passed,
                    "players_with_cards": len(players_ready),
                    "moves": cards_played_this_round,
                }
                wait_time, prompt, decision = player.decide_action(game_state)
                self.llm_logs.append((player.name, prompt, decision))
                heapq.heappush(
                    action_queue,
                    (time_passed + wait_time, player.card, player.name),
                )

            if action_queue:
                play_time, card, player_name = heapq.heappop(action_queue)
                time_passed = play_time
                cards_played_this_round.append(
                    (time_passed, card, player_name)
                )

                if self.played_cards and card < max(self.played_cards):
                    unplayed_cards = [
                        (p.name, p.card)
                        for p in players_ready
                        if p.name != player_name
                    ]
                    return False, cards_played_this_round, unplayed_cards

                self.played_cards.append(card)
                players_ready = [
                    p for p in players_ready if p.name != player_name
                ]

                if len(self.played_cards) == len(self.players):
                    return True, cards_played_this_round, []

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


def display_game(all_rounds_data, llm_logs):
    game_state = st.empty()

    for level, success, round_data, unplayed_cards in all_rounds_data:
        with game_state.container():
            st.subheader(f"Level {level}")

            for wait_time, card, player_name in round_data:
                st.write(
                    f"Second {wait_time:.1f}: {player_name} plays their {card} card"
                )

            if success:
                st.success(f"Level {level} completed successfully!")
            else:
                st.error(f"Game Over at Level {level}")
                if unplayed_cards:
                    st.write("Unplayed cards:")
                    for player_name, card in unplayed_cards:
                        st.write(f"{player_name}: {card}")
                break

    if all(success for _, success, _, _ in all_rounds_data):
        st.success("Congratulations! You've completed all levels!")

    with st.expander("View LLM Logs"):
        for player_name, prompt, decision in llm_logs:
            st.text(f"LLM Call for {player_name}:")
            st.text("Prompt:")
            st.text(prompt)
            st.text("Response:")
            st.text(decision)
            st.text("---")


def main():
    st.title("The Mind Game - LLM Edition")

    num_players = st.sidebar.slider("Number of Players", 2, 5, 3)

    st.sidebar.write(
        "The game has a maximum of 12 levels. In each level, players receive cards equal to the level number."
    )

    if st.sidebar.button("Start New Game"):
        game = TheMindGame(num_players=num_players)
        all_rounds_data = game.play_game()
        display_game(all_rounds_data, game.llm_logs)


if __name__ == "__main__":
    main()

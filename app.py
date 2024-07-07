import streamlit as st
import random
import time
from typing import List, Tuple
import openai
import heapq

# Set up your OpenAI API key using Streamlit secrets
openai.api_key = st.secrets["OPENAI_KEY"]


class LLMPlayer:
    def __init__(self, name: str):
        self.name = name
        self.card: int = None
        self.wait_time: float = 0

    def receive_card(self, card: int):
        self.card = card

    def play_card(self) -> int:
        played_card = self.card
        self.card = None
        return played_card

    def decide_action(self, game_state: dict) -> Tuple[str, float]:
        prompt = self._create_prompt(game_state)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI playing a simplified version of 'The Mind' card game. Decide whether to play your card and how long to wait.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        decision = response.choices[0].message["content"].strip().lower()

        if "play" in decision:
            action = "play"
            wait_time = 0
        else:
            action = "wait"
            try:
                wait_time = float(decision.split()[-1])
            except ValueError:
                wait_time = random.uniform(
                    1, 5
                )  # Default wait time if parsing fails

        return action, wait_time

    def _create_prompt(self, game_state: dict) -> str:
        return f"""
        You are playing a simplified version of 'The Mind' card game. Your goal is to play cards in ascending order without communicating.
        Current game state:
        - Your card: {self.card}
        - Current level: {game_state['current_level']}
        - Cards played this level: {game_state['played_cards']}
        - Time passed in this level: {game_state['time_passed']:.2f} seconds
        - Players left with cards: {game_state['players_with_cards']}

        Decide whether to play your card ({self.card}) now or wait. If you choose to wait, specify how many seconds to wait.
        Respond with either 'Play' or 'Wait X' where X is the number of seconds to wait (e.g., 'Wait 3.5').
        """


class TheMindGame:
    def __init__(self, num_players: int, max_level: int):
        self.players = [LLMPlayer(f"LLM_{i+1}") for i in range(num_players)]
        self.max_level = max_level
        self.current_level = 1
        self.played_cards: List[int] = []
        self.start_time = time.time()

    def setup_level(self):
        cards = random.sample(range(1, 101), len(self.players))
        self.played_cards = []
        self.start_time = time.time()

        for player, card in zip(self.players, cards):
            player.receive_card(card)

    def play_round(self) -> Tuple[bool, List[Tuple[float, int, str]]]:
        players_ready = [p for p in self.players if p.card is not None]
        cards_played_this_round = []
        action_queue = []
        lowest_card = min(p.card for p in players_ready)

        # Get initial decisions from all players
        for player in players_ready:
            game_state = {
                "current_level": self.current_level,
                "played_cards": self.played_cards,
                "time_passed": 0,
                "players_with_cards": len(players_ready),
            }
            action, wait_time = player.decide_action(game_state)
            heapq.heappush(action_queue, (wait_time, player.card, player.name))

        # Process actions in order
        while action_queue:
            wait_time, card, player_name = heapq.heappop(action_queue)

            time_passed = wait_time - (time.time() - self.start_time)
            if time_passed > 0:
                time.sleep(time_passed)

            st.write(
                f"{player_name} attempts to play {card} after {wait_time:.2f} seconds"
            )
            cards_played_this_round.append((wait_time, card, player_name))

            if card != lowest_card:
                st.error(
                    f"Game Over! {player_name} tried to play {card}, but the lowest card was {lowest_card}."
                )
                return False, cards_played_this_round

            self.played_cards.append(card)

            # Update lowest_card for the next iteration
            players_ready = [p for p in players_ready if p.card != card]
            if players_ready:
                lowest_card = min(p.card for p in players_ready)

        return True, cards_played_this_round

    def play_game(self):
        st.write(
            f"Starting a new game with {len(self.players)} players and a maximum of {self.max_level} levels."
        )
        st.write(
            "In each level, players receive cards equal to the level number."
        )

        while self.current_level <= self.max_level:
            st.subheader(f"Level {self.current_level}")
            self.setup_level()

            # Display current hands
            for player in self.players:
                st.text(f"{player.name}'s card: {player.card}")

            success, cards_played = self.play_round()
            st.write("Cards played/attempted this level:")
            for wait_time, card, player_name in cards_played:
                st.write(f"{player_name}: {card} (waited {wait_time:.2f}s)")

            if success:
                st.success(
                    f"Level {self.current_level} completed successfully!"
                )
                self.current_level += 1
            else:
                st.error(f"Game Over at Level {self.current_level}")
                break

            # Add a continue button between levels
            if self.current_level <= self.max_level:
                if st.button(
                    f"Continue to Level {self.current_level}",
                    key=f"continue_{self.current_level}",
                ):
                    st.experimental_rerun()
                else:
                    st.stop()  # Pause the app here until the button is pressed

        if self.current_level > self.max_level:
            st.success("Congratulations! You've completed all levels!")


def main():
    st.title("The Mind Game - LLM Edition")

    num_players = st.sidebar.slider("Number of Players", 2, 5, 3)
    max_level = st.sidebar.slider("Max Level", 1, 12, 8)

    st.sidebar.write(
        "Max Level: The highest level the game can reach. In each level, players receive cards equal to the level number."
    )

    if st.sidebar.button("Start New Game"):
        game = TheMindGame(num_players=num_players, max_level=max_level)
        game.play_game()


if __name__ == "__main__":
    main()

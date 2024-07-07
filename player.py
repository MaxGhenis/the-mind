import random
import openai


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

    def decide_action(self, game_state: dict) -> tuple[float, str]:
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
            self.wait_time = float(decision)
        except ValueError:
            self.wait_time = random.uniform(
                1, 5
            )  # Default wait time if parsing fails

        # Add a small random factor to the wait time to handle ties
        self.wait_time += random.uniform(0, 0.1)

        return self.wait_time, prompt, decision

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
        - Time passed in this game: {game_state['time_passed']:.1f} seconds
        - Players left with cards: {game_state['players_with_cards']}
        - Moves made this game:
        {moves_description}

        Decide how long to wait from this moment before playing your card ({self.card}).
        Respond with only a single number representing the number of seconds to wait (e.g., '3.5').
        """

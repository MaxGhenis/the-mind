import streamlit as st
import openai
from game import TheMindGame
from display import display_game, display_logs
from name_generator import generate_fun_name

# Set up your OpenAI API key using Streamlit secrets
openai.api_key = st.secrets["OPENAI_KEY"]


def main():
    st.title("The Mind Game - LLM Edition")

    num_players = st.sidebar.slider("Number of Players", 2, 5, 3)

    if st.sidebar.button("Start New Game"):
        player_names = [generate_fun_name() for _ in range(num_players)]
        game = TheMindGame(player_names)
        game_result = game.play_game()
        display_game(game_result)
        # Note: LLM logs are not implemented in this version, but could be added later


if __name__ == "__main__":
    main()

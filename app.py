import streamlit as st
import openai
from game import TheMindGame
from display import display_game

# Set up your OpenAI API key using Streamlit secrets
openai.api_key = st.secrets["OPENAI_KEY"]


def main():
    st.title("The Mind Game - LLM Edition")

    num_players = st.sidebar.slider("Number of Players", 2, 5, 3)

    if st.sidebar.button("Start New Game"):
        game = TheMindGame(num_players=num_players)
        game_result = game.play_game()
        display_game(game_result, game.llm_logs)


if __name__ == "__main__":
    main()

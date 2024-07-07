import streamlit as st
import openai
from game import TheMindGame
from name_generator import generate_fun_name

# Set up your OpenAI API key using Streamlit secrets


def display_game(game_result):
    success, moves, unplayed_cards = game_result

    st.subheader("The Mind Game - LLM Edition")

    for move in moves:
        st.write(
            f"{move['time']:.1f}: {move['player']} plays their {move['card']} card"
        )

    if not success:
        st.error("GAME OVER")

    st.write("Cards in play:")
    all_cards = [
        (move["player"], move["card"]) for move in moves
    ] + unplayed_cards
    all_cards.sort(key=lambda x: x[1])  # Sort by card value
    for player_name, card in all_cards:
        st.write(f"{player_name} had a {card}")


def main():
    st.title("The Mind Game - LLM Edition")

    num_players = st.sidebar.slider("Number of Players", 2, 5, 3)

    if st.sidebar.button("Start New Game"):
        player_names = [generate_fun_name() for _ in range(num_players)]
        game = TheMindGame(player_names)
        game_result = game.play_game()
        display_game(game_result)


if __name__ == "__main__":
    main()

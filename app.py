import streamlit as st
from openai import OpenAI
from game import TheMindGame
from name_generator import generate_fun_name

# Set up your OpenAI client using Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def display_game(game_result, llm_logs, debug_logs):
    success, moves, unplayed_cards = game_result

    for move in moves:
        st.write(
            f"{move['time']:.1f}: {move['player']} plays their {move['card']} card"
        )

    if not success:
        st.error("GAME OVER")
        st.write("Final game state:")
        all_cards = [
            (move["player"], move["card"]) for move in moves
        ] + unplayed_cards
        all_cards.sort(key=lambda x: x[1])  # Sort by card value
        for player_name, card in all_cards:
            st.write(f"{player_name} had {card}")
    else:
        st.success("Round Completed Successfully!")
        if unplayed_cards:
            last_player, last_card = unplayed_cards[0]
            st.write(f"{last_player} would have played {last_card} next")

    with st.expander("View LLM Logs"):
        for player_name, prompt, decision in llm_logs:
            st.text(f"LLM Call for {player_name}:")
            st.text("Prompt:")
            st.text(prompt)
            st.text("Response:")
            st.text(decision)
            st.text("---")

    with st.expander("Debug Information"):
        for log in debug_logs:
            st.text(log)


def main():
    st.title("The Mind Game - LLM Edition")

    num_players = st.sidebar.slider("Number of Players", 2, 5, 3)

    if st.sidebar.button("Start New Game"):
        player_names = [generate_fun_name() for _ in range(num_players)]
        game = TheMindGame(player_names, client)
        game_result, llm_logs, debug_logs = game.play_game()
        display_game(game_result, llm_logs, debug_logs)


if __name__ == "__main__":
    main()

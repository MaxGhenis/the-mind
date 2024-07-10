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

    # Add a subtitle describing the game
    st.markdown(
        """
    <p style="font-size: 1.2em; font-style: italic; margin-bottom: 20px;">
    A cooperative card game where players must play cards in ascending order without communicating. 
    Can AI agents learn to play together?
    </p>
    """,
        unsafe_allow_html=True,
    )

    # Create a row of buttons for different player counts
    st.write("Choose the number of AI players:")
    cols = st.columns(5)
    for i, col in enumerate(cols, start=2):
        if col.button(f"{i} Players"):
            player_names = [generate_fun_name() for _ in range(i)]
            game = TheMindGame(player_names, client)
            game_result, llm_logs, debug_logs = game.play_game()
            display_game(game_result, llm_logs, debug_logs)

    # Add some space before the credits
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Credits at the bottom of the main panel
    st.markdown(
        """
    <div style="font-size: 0.8em; border-top: 1px solid #e6e6e6; padding-top: 10px;">
    Created by <a href='mailto:mghenis@gmail.com'>Max Ghenis</a> with 
    <a href='https://streamlit.io'>Streamlit</a>, 
    <a href='https://claude.ai'>Claude</a> 3.5 Sonnet, and the 
    <a href='https://openai.com'>OpenAI</a> GPT-3.5 API
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

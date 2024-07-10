import streamlit as st
import time
from typing import Tuple, List, Dict


def display_game(game_result, llm_logs, debug_logs):
    success, moves, unplayed_cards = game_result

    st.subheader("Game Progress")

    # Create placeholders
    timer_placeholder = st.empty()
    status_placeholder = st.empty()
    moves_placeholder = st.empty()
    cards_placeholder = st.empty()

    # Display game progression
    displayed_moves = []
    cards_in_play = []
    current_time = 0
    update_interval = 0.1  # Update every 0.1 seconds

    for move in moves:
        while current_time < move["time"]:
            # Update timer
            timer_placeholder.markdown(
                f"<h3>Time: {current_time:.1f} seconds</h3>",
                unsafe_allow_html=True,
            )
            status_placeholder.info("Players are thinking...")

            time.sleep(update_interval)
            current_time += update_interval

        # Player makes a move
        timer_placeholder.markdown(
            f"<h3>Time: {move['time']:.1f} seconds</h3>",
            unsafe_allow_html=True,
        )
        status_placeholder.success(f"{move['player']} plays a card!")

        # Add new move
        displayed_moves.append(move)
        cards_in_play.append((move["player"], move["card"]))
        cards_in_play.sort(key=lambda x: x[1])

        # Update moves display
        moves_text = "\n".join(
            [
                f"{m['time']:.1f}: {m['player']} plays their {m['card']} card"
                for m in displayed_moves
            ]
        )
        moves_placeholder.text(moves_text)

        # Update cards in play
        cards_text = "**Cards played:**\n" + "\n".join(
            [f"{player} played {card}" for player, card in cards_in_play]
        )
        cards_placeholder.markdown(cards_text)

        # Pause to emphasize the move
        time.sleep(1)  # Pause for 1 second after each move

    # Final update
    timer_placeholder.markdown(
        f"<h3>Final Time: {moves[-1]['time']:.1f} seconds</h3>",
        unsafe_allow_html=True,
    )

    # Game result
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

    # Display logs in expanders
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


def display_logs(llm_logs):
    with st.expander("View LLM Logs"):
        for player_name, prompt, decision in llm_logs:
            st.text(f"LLM Call for {player_name}:")
            st.text("Prompt:")
            st.text(prompt)
            st.text("Response:")
            st.text(decision)
            st.text("---")


# The main function remains largely the same, but now calls these updated display functions

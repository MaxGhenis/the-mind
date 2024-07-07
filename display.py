import streamlit as st


def display_game(game_result, llm_logs):
    success, round_data, unplayed_cards = game_result

    st.subheader("The Mind Game - LLM Edition")

    if round_data:
        wait_time, card, player_name = round_data[0]
        st.write(f"{wait_time:.1f}: {player_name} plays their {card} card")

    st.error("GAME OVER")

    st.write("Cards in play:")
    all_cards = [(p, c) for _, c, p in round_data] + unplayed_cards
    all_cards.sort(key=lambda x: x[1])  # Sort by card value
    for player_name, card in all_cards:
        st.write(f"{player_name} had a {card}")

    with st.expander("View LLM Logs"):
        for player_name, prompt, decision in llm_logs:
            st.text(f"LLM Call for {player_name}:")
            st.text("Prompt:")
            st.text(prompt)
            st.text("Response:")
            st.text(decision)
            st.text("---")

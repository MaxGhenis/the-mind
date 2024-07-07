import streamlit as st


def display_game(all_rounds_data, llm_logs):
    game_state = st.empty()

    for level, success, round_data, unplayed_cards in all_rounds_data:
        with game_state.container():
            st.subheader(f"Level {level}")

            if round_data:
                wait_time, card, player_name = round_data[0]
                st.write(
                    f"{wait_time:.1f}: {player_name} plays their {card} card"
                )

            if not success:
                st.error("GAME OVER")
                if unplayed_cards:
                    st.write("Unplayed cards:")
                    for player_name, card in unplayed_cards:
                        st.write(f"{player_name} had a {card}")
                break
            else:
                st.success(f"Level {level} completed successfully!")

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

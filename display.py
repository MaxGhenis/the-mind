import streamlit as st


def display_game(game_result: Tuple[bool, List[Dict], List[Tuple[str, int]]]):
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


def display_logs(llm_logs):
    with st.expander("View LLM Logs"):
        for player_name, prompt, decision in llm_logs:
            st.text(f"LLM Call for {player_name}:")
            st.text("Prompt:")
            st.text(prompt)
            st.text("Response:")
            st.text(decision)
            st.text("---")

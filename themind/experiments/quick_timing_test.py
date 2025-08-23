"""Quick test of card-to-time relationship with fewer cards."""

import os
import pandas as pd
import numpy as np
from edsl import Model, QuestionFreeText, Survey
from edsl.agents import Agent, AgentList
import matplotlib.pyplot as plt

os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')

def quick_test():
    """Test a subset of cards to verify monotonic relationship."""
    
    # Test specific cards across the range
    test_cards = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    num_samples = 3
    
    print(f"Testing {len(test_cards)} cards with {num_samples} samples each...")
    
    survey = Survey()
    for card in test_cards:
        q = QuestionFreeText(
            question_name=f"card_{card}",
            question_text=f"""You are playing The Mind card game.
Your card is: {card}
Cards range from 1-100. Lower cards should be played sooner.
Wait approximately {card/100*30:.0f} seconds.
Respond with ONLY a number (0-30):"""
        )
        survey.add_question(q)
    
    model = Model("gemini-2.5-flash-lite", service_name="google", temperature=0.3)
    agents = AgentList([Agent(name=f"s{i}") for i in range(num_samples)])
    
    print("Running survey...")
    results = survey.by(agents).by(model).run()
    
    # Process results
    data = []
    df_results = results.to_pandas()
    
    for idx, row in df_results.iterrows():
        for col in df_results.columns:
            if col.startswith("answer.card_"):
                card = int(col.split("_")[1])
                try:
                    wait_time = float(str(row[col]).strip().split()[0])
                    data.append({
                        'card': card,
                        'wait_time': wait_time,
                        'theoretical': card/100*30
                    })
                except:
                    pass
    
    df = pd.DataFrame(data)
    
    # Analysis
    if len(df) > 0:
        correlation = df['card'].corr(df['wait_time'])
        
        # Group by card and show mean
        summary = df.groupby('card').agg({
            'wait_time': ['mean', 'std', 'count'],
            'theoretical': 'first'
        }).round(1)
        
        print(f"\n📊 Results (Correlation: {correlation:.3f}):")
        print("\nCard | Theory | Actual (mean±std) | n")
        print("-" * 40)
        
        for card in summary.index:
            theory = summary.loc[card, ('theoretical', 'first')]
            mean = summary.loc[card, ('wait_time', 'mean')]
            std = summary.loc[card, ('wait_time', 'std')]
            n = int(summary.loc[card, ('wait_time', 'count')])
            print(f"{card:4d} | {theory:5.1f}s | {mean:5.1f}±{std:3.1f}s | {n}")
        
        # Simple plot
        plt.figure(figsize=(10, 6))
        plt.scatter(df['card'], df['wait_time'], alpha=0.5, label='Actual')
        plt.plot(df['card'], df['theoretical'], 'r-', label='Theoretical')
        
        # Add mean line
        mean_by_card = df.groupby('card')['wait_time'].mean()
        plt.plot(mean_by_card.index, mean_by_card.values, 'b-', alpha=0.7, label='Mean', marker='o')
        
        plt.xlabel('Card Number')
        plt.ylabel('Wait Time (seconds)')
        plt.title(f'Card vs Wait Time (r={correlation:.3f})')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('quick_timing_test.png', dpi=100)
        print(f"\n📊 Plot saved to quick_timing_test.png")

if __name__ == "__main__":
    quick_test()
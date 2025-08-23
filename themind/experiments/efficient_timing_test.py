"""Efficient card timing test using n parameter for multiple completions."""

import os
import openai
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict
import json
import time

# Use OpenAI directly for efficiency with n parameter
openai.api_key = os.environ.get('OPENAI_API_KEY', '')

def test_card_with_n(card: int, n_samples: int = 10, model: str = "gpt-4o-mini") -> List[float]:
    """Test a single card value with n completions in one API call."""
    
    prompt = f"""You are playing The Mind card game.
Your card is: {card}
Cards range from 1-100. Lower cards should be played sooner.
Strategy: Wait approximately {card/3.3:.0f} seconds (0-30 scale).
Respond with ONLY a number (0-30):"""
    
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            n=n_samples,
            temperature=0.7,
            max_tokens=10
        )
        
        wait_times = []
        for choice in response.choices:
            try:
                content = choice.message.content.strip()
                wait_time = float(content.split()[0].replace(',', '.'))
                wait_time = max(0, min(30, wait_time))
                wait_times.append(wait_time)
            except:
                pass
        
        return wait_times
    except Exception as e:
        print(f"Error testing card {card}: {e}")
        return []

def efficient_bulk_test(
    cards: List[int] = None,
    n_samples: int = 10,
    model: str = "gpt-4o-mini"
) -> pd.DataFrame:
    """Test multiple cards efficiently using n parameter."""
    
    if cards is None:
        # Test every 5th card plus boundaries
        cards = list(range(1, 101, 5))
        cards.extend([2, 33, 34, 66, 67, 99, 100])
        cards = sorted(list(set(cards)))
    
    print(f"\n{'='*60}")
    print(f"Efficient Card Timing Test")
    print(f"Model: {model}, n={n_samples} per card")
    print(f"Testing {len(cards)} cards → {len(cards)} API calls only!")
    print(f"{'='*60}\n")
    
    data = []
    start_time = time.time()
    
    for i, card in enumerate(cards):
        print(f"Testing card {card:3d} ({i+1}/{len(cards)})...", end=" ")
        
        wait_times = test_card_with_n(card, n_samples, model)
        
        if wait_times:
            mean_time = np.mean(wait_times)
            std_time = np.std(wait_times)
            print(f"mean={mean_time:.1f}s, std={std_time:.1f}s, n={len(wait_times)}")
            
            for j, wait_time in enumerate(wait_times):
                data.append({
                    'card': card,
                    'wait_time': wait_time,
                    'sample': j,
                    'model': model,
                    'theoretical': card / 100 * 30
                })
        else:
            print("failed")
        
        # Small delay to avoid rate limits
        if i % 10 == 9:
            time.sleep(1)
    
    elapsed = time.time() - start_time
    df = pd.DataFrame(data)
    
    print(f"\n✅ Completed in {elapsed:.1f}s")
    print(f"📊 Collected {len(df)} data points")
    print(f"💰 Cost estimate: {len(cards)} prompts + {len(df)} completions")
    
    return df

def analyze_and_plot(df: pd.DataFrame):
    """Analyze results and create visualization."""
    
    if len(df) == 0:
        print("No data to analyze!")
        return
    
    # Calculate statistics
    stats = df.groupby('card').agg({
        'wait_time': ['mean', 'std', 'min', 'max', 'count'],
        'theoretical': 'first'
    }).round(2)
    
    correlation = df['card'].corr(df['wait_time'])
    
    # Check monotonicity
    means = stats[('wait_time', 'mean')].values
    monotonic = sum(means[i] >= means[i-1] for i in range(1, len(means))) / (len(means) - 1)
    
    print(f"\n📈 Analysis:")
    print(f"  Correlation: {correlation:.3f}")
    print(f"  Monotonicity: {monotonic:.1%}")
    print(f"  Mean absolute error: {(df['wait_time'] - df['theoretical']).abs().mean():.2f}s")
    
    # Create plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Scatter plot
    ax = axes[0]
    ax.scatter(df['card'], df['wait_time'], alpha=0.2, s=10)
    ax.plot(df['card'], df['theoretical'], 'r-', linewidth=2, label='Theoretical', alpha=0.7)
    
    mean_by_card = df.groupby('card')['wait_time'].mean()
    ax.plot(mean_by_card.index, mean_by_card.values, 'b-', linewidth=1, label='Mean', marker='.')
    
    ax.set_xlabel('Card Number')
    ax.set_ylabel('Wait Time (seconds)')
    ax.set_title(f'Card vs Wait Time (r={correlation:.3f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Variance plot
    ax = axes[1]
    std_by_card = df.groupby('card')['wait_time'].std()
    ax.bar(std_by_card.index, std_by_card.values, width=2)
    ax.set_xlabel('Card Number')
    ax.set_ylabel('Standard Deviation (seconds)')
    ax.set_title('Response Consistency')
    ax.grid(True, alpha=0.3)
    
    # Distribution by terciles
    ax = axes[2]
    df['tercile'] = pd.cut(df['card'], bins=[0, 33, 66, 100], labels=['Low (1-33)', 'Mid (34-66)', 'High (67-100)'])
    df.boxplot(column='wait_time', by='tercile', ax=ax)
    ax.set_xlabel('Card Range')
    ax.set_ylabel('Wait Time (seconds)')
    ax.set_title('Distribution by Card Range')
    plt.sca(ax)
    plt.xticks(rotation=0)
    
    plt.suptitle(f'Efficient Testing with n={df.groupby("card")["sample"].nunique()} samples per card', y=1.02)
    plt.tight_layout()
    plt.savefig('efficient_timing_analysis.png', dpi=150)
    print(f"\n📊 Plot saved to efficient_timing_analysis.png")
    
    return stats, correlation

def compare_cost():
    """Compare cost of different approaches."""
    
    cards = 100  # Number of unique cards to test
    samples = 10  # Samples per card
    
    # Rough token estimates
    prompt_tokens = 50  # Per prompt
    completion_tokens = 5  # Per completion
    
    # Prices (GPT-4o-mini)
    prompt_price = 0.15 / 1_000_000  # $0.15 per 1M tokens
    completion_price = 0.60 / 1_000_000  # $0.60 per 1M tokens
    
    # Method 1: Multiple agents (Expected Parrot approach)
    method1_prompts = cards * samples * prompt_tokens
    method1_completions = cards * samples * completion_tokens
    method1_cost = method1_prompts * prompt_price + method1_completions * completion_price
    
    # Method 2: Using n parameter
    method2_prompts = cards * prompt_tokens  # Only send prompt once per card
    method2_completions = cards * samples * completion_tokens  # Still get all completions
    method2_cost = method2_prompts * prompt_price + method2_completions * completion_price
    
    print(f"\n💰 Cost Comparison ({cards} cards, {samples} samples each):")
    print(f"\nMethod 1 (Multiple Agents):")
    print(f"  Prompt tokens: {method1_prompts:,}")
    print(f"  Completion tokens: {method1_completions:,}")
    print(f"  Estimated cost: ${method1_cost:.4f}")
    
    print(f"\nMethod 2 (n parameter):")
    print(f"  Prompt tokens: {method2_prompts:,}")
    print(f"  Completion tokens: {method2_completions:,}")
    print(f"  Estimated cost: ${method2_cost:.4f}")
    
    print(f"\n🎯 Savings: ${method1_cost - method2_cost:.4f} ({(1 - method2_cost/method1_cost)*100:.1f}% cheaper)")

def main():
    """Run efficient timing test."""
    
    # First show cost comparison
    compare_cost()
    
    # Then run actual test
    df = efficient_bulk_test(
        cards=list(range(1, 101, 10)) + [5, 15, 25, 35, 45, 55, 65, 75, 85, 95],  # 20 cards
        n_samples=5,  # 5 samples each
        model="gpt-4o-mini"
    )
    
    if len(df) > 0:
        stats, correlation = analyze_and_plot(df)
        
        # Save results
        df.to_csv('efficient_timing_results.csv', index=False)
        print(f"✅ Results saved to efficient_timing_results.csv")

if __name__ == "__main__":
    main()
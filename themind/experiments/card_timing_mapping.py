"""Systematic experiment to map card numbers to wait times across different models."""

import os
import json
import csv
import numpy as np
from datetime import datetime
from edsl import Model, QuestionFreeText, Survey, Agent
from edsl.agents import AgentList
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import time

os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')

def create_card_timing_survey(num_players: int = 3) -> Survey:
    """Create a survey that asks about wait times for all possible cards."""
    
    survey = Survey()
    
    # Test a range of card values
    card_values = list(range(1, 101, 5))  # Every 5th card for efficiency
    card_values.extend([25, 50, 75])  # Add quartiles
    card_values = sorted(list(set(card_values)))
    
    for card in card_values:
        q = QuestionFreeText(
            question_name=f"card_{card}",
            question_text=f"""You are playing The Mind card game with {num_players} players.
Your card is: {card}
Cards range from 1-100. Lower cards should be played sooner.
Strategy: 1-33 wait 0-10 seconds, 34-66 wait 10-20 seconds, 67-100 wait 20-30 seconds.
Respond with ONLY a number (0-30) representing seconds to wait:"""
        )
        survey.add_question(q)
    
    return survey

def run_timing_experiment(
    model_name: str = "gemini-2.5-flash-lite",
    service_name: str = "google",
    num_players: int = 3,
    num_samples: int = 5  # Run each question multiple times
) -> pd.DataFrame:
    """Run experiment to map card values to wait times."""
    
    print(f"\n{'='*60}")
    print(f"Card-to-Time Mapping Experiment")
    print(f"Model: {model_name}, Players: {num_players}, Samples: {num_samples}")
    print(f"{'='*60}\n")
    
    model = Model(model_name, service_name=service_name)
    survey = create_card_timing_survey(num_players)
    
    # Create multiple agents for multiple samples
    agents = AgentList([
        Agent(name=f"sample_{i}", traits={}) 
        for i in range(num_samples)
    ])
    
    print(f"Running survey with {len(survey.questions)} card values...")
    print(f"This will generate {len(survey.questions) * num_samples} responses total.")
    
    start_time = time.time()
    
    # Run the survey
    results = survey.by(agents).by(model).run()
    
    elapsed = time.time() - start_time
    print(f"\n✅ Completed in {elapsed:.1f} seconds")
    
    # Process results
    data = []
    
    # Convert to DataFrame for easier processing
    df_results = results.to_pandas()
    
    for idx, row in df_results.iterrows():
        sample_num = idx % num_samples
        
        # Find all card columns
        for col in df_results.columns:
            if col.startswith("answer.card_"):
                card_num = int(col.split("card_")[1])
                value = row[col]
                
                try:
                    # Parse the wait time from response
                    wait_time = float(str(value).strip().split()[0].replace(',', '.'))
                    wait_time = max(0, min(30, wait_time))  # Clamp to valid range
                except:
                    wait_time = None
                
                if wait_time is not None:
                    data.append({
                        'card': card_num,
                        'wait_time': wait_time,
                        'sample': sample_num,
                        'model': model_name,
                        'num_players': num_players
                    })
    
    df = pd.DataFrame(data)
    return df

def analyze_results(df: pd.DataFrame) -> Dict:
    """Analyze the relationship between card numbers and wait times."""
    
    # Group by card and calculate statistics
    stats = df.groupby('card')['wait_time'].agg([
        'mean', 'std', 'min', 'max', 'count'
    ]).reset_index()
    
    # Calculate correlation
    correlation = df['card'].corr(df['wait_time'])
    
    # Check monotonicity (how often wait time increases with card number)
    sorted_stats = stats.sort_values('card')
    monotonic_increases = 0
    for i in range(1, len(sorted_stats)):
        if sorted_stats.iloc[i]['mean'] > sorted_stats.iloc[i-1]['mean']:
            monotonic_increases += 1
    monotonicity = monotonic_increases / (len(sorted_stats) - 1) if len(sorted_stats) > 1 else 0
    
    return {
        'correlation': correlation,
        'monotonicity': monotonicity,
        'stats': stats
    }

def plot_results(df: pd.DataFrame, output_file: str = 'card_timing_relationship.png'):
    """Create visualization of card-to-time relationship."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Scatter plot with all samples
    ax1.scatter(df['card'], df['wait_time'], alpha=0.3, s=20)
    
    # Add mean line
    stats = df.groupby('card')['wait_time'].mean().reset_index()
    ax1.plot(stats['card'], stats['wait_time'], 'r-', linewidth=2, label='Mean')
    
    # Add theoretical zones
    ax1.axhspan(0, 10, alpha=0.1, color='green', label='Low cards (0-10s)')
    ax1.axhspan(10, 20, alpha=0.1, color='yellow', label='Mid cards (10-20s)')
    ax1.axhspan(20, 30, alpha=0.1, color='red', label='High cards (20-30s)')
    ax1.axvline(33, color='gray', linestyle='--', alpha=0.5)
    ax1.axvline(66, color='gray', linestyle='--', alpha=0.5)
    
    ax1.set_xlabel('Card Number')
    ax1.set_ylabel('Wait Time (seconds)')
    ax1.set_title('Card Number vs Wait Time - All Samples')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Box plot by card ranges
    df['card_range'] = pd.cut(df['card'], bins=[0, 20, 40, 60, 80, 100], 
                              labels=['1-20', '21-40', '41-60', '61-80', '81-100'])
    df.boxplot(column='wait_time', by='card_range', ax=ax2)
    ax2.set_xlabel('Card Range')
    ax2.set_ylabel('Wait Time (seconds)')
    ax2.set_title('Wait Time Distribution by Card Range')
    plt.suptitle('')  # Remove automatic title
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n📊 Plot saved to {output_file}")
    
    return fig

def save_results(df: pd.DataFrame, analysis: Dict, output_dir: str = 'data/card_timing'):
    """Save experimental results."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save raw data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = f"{output_dir}/card_timing_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    print(f"✅ Raw data saved to {csv_file}")
    
    # Save analysis
    analysis_file = f"{output_dir}/analysis_{timestamp}.json"
    analysis_dict = {
        'correlation': float(analysis['correlation']),
        'monotonicity': float(analysis['monotonicity']),
        'stats': analysis['stats'].to_dict(orient='records')
    }
    with open(analysis_file, 'w') as f:
        json.dump(analysis_dict, f, indent=2)
    print(f"✅ Analysis saved to {analysis_file}")
    
    return csv_file, analysis_file

def main():
    """Run the card timing mapping experiment."""
    
    # Run experiment
    df = run_timing_experiment(
        model_name="gemini-2.5-flash-lite",
        service_name="google",
        num_players=3,
        num_samples=3  # Start with just 3 samples for testing
    )
    
    if len(df) == 0:
        print("❌ No data collected!")
        return
    
    # Analyze results
    analysis = analyze_results(df)
    
    print(f"\n📈 Analysis Results:")
    print(f"  Correlation (card vs time): {analysis['correlation']:.3f}")
    print(f"  Monotonicity: {analysis['monotonicity']:.1%}")
    print(f"\n  Mean wait times by card:")
    
    stats = analysis['stats']
    for _, row in stats.head(10).iterrows():
        print(f"    Card {int(row['card']):3d}: {row['mean']:5.1f}s (σ={row['std']:4.1f}, n={int(row['count'])})")
    
    if len(stats) > 10:
        print(f"    ... ({len(stats) - 10} more cards)")
    
    # Plot results
    plot_results(df)
    
    # Save everything
    save_results(df, analysis)
    
    print("\n✨ Experiment complete!")

if __name__ == "__main__":
    main()
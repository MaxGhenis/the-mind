"""Bulk testing of card-to-time mapping using parallel API calls."""

import os
import json
import asyncio
from datetime import datetime
import pandas as pd
import numpy as np
from edsl import Model, QuestionFreeText, Survey
from edsl.agents import Agent, AgentList
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple

os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')

def create_comprehensive_survey(num_players: int = 3) -> Tuple[Survey, List[int]]:
    """Create survey testing ALL cards from 1-100."""
    
    survey = Survey()
    card_values = list(range(1, 101))  # All cards
    
    for card in card_values:
        q = QuestionFreeText(
            question_name=f"card_{card:03d}",  # Zero-pad for consistent ordering
            question_text=f"""You are playing The Mind card game with {num_players} players.
Your card is: {card}
Cards range from 1-100. Lower cards should be played sooner.
Strategy: Wait {card/100*30:.0f} seconds (proportional to card value).
Respond with ONLY a number (0-30) representing seconds to wait:"""
        )
        survey.add_question(q)
    
    return survey, card_values

def run_bulk_experiment(
    model_name: str = "gemini-2.5-flash-lite",
    service_name: str = "google",
    num_players: int = 3,
    num_samples: int = 10
) -> pd.DataFrame:
    """Run comprehensive card timing experiment."""
    
    print(f"\n{'='*60}")
    print(f"Comprehensive Card-to-Time Mapping")
    print(f"Testing ALL cards 1-100 with {num_samples} samples each")
    print(f"Total API calls: {100 * num_samples}")
    print(f"{'='*60}\n")
    
    model = Model(model_name, service_name=service_name, temperature=0.3)  # Lower temp for consistency
    survey, card_values = create_comprehensive_survey(num_players)
    
    # Create agents for multiple samples
    agents = AgentList([
        Agent(name=f"sample_{i:02d}") 
        for i in range(num_samples)
    ])
    
    print(f"Running survey...")
    import time
    start = time.time()
    
    # Run survey
    results = survey.by(agents).by(model).run()
    
    elapsed = time.time() - start
    print(f"✅ Completed in {elapsed:.1f}s ({elapsed/100:.2f}s per card)")
    
    # Process results
    data = []
    df_results = results.to_pandas()
    
    for idx, row in df_results.iterrows():
        sample_num = idx
        
        for col in df_results.columns:
            if col.startswith("answer.card_"):
                card_num = int(col.split("_")[1])
                value = row[col]
                
                try:
                    wait_time = float(str(value).strip().split()[0].replace(',', '.'))
                    wait_time = max(0, min(30, wait_time))
                    
                    data.append({
                        'card': card_num,
                        'wait_time': wait_time,
                        'sample': sample_num,
                        'model': model_name,
                        'num_players': num_players,
                        'theoretical': card_num / 100 * 30  # What we asked for
                    })
                except Exception as e:
                    print(f"  Warning: Failed to parse card {card_num}: {value}")
    
    df = pd.DataFrame(data)
    print(f"\n📊 Collected {len(df)} data points")
    
    return df

def analyze_comprehensive_results(df: pd.DataFrame) -> Dict:
    """Detailed analysis of card-time relationship."""
    
    # Group statistics
    stats = df.groupby('card').agg({
        'wait_time': ['mean', 'std', 'min', 'max', 'count'],
        'theoretical': 'first'
    }).round(2)
    
    # Flatten column names
    stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
    stats = stats.rename(columns={'theoretical_first': 'theoretical'})
    
    # Calculate error from theoretical
    stats['error'] = stats['wait_time_mean'] - stats['theoretical']
    stats['abs_error'] = stats['error'].abs()
    
    # Overall metrics
    correlation = df['card'].corr(df['wait_time'])
    theoretical_correlation = df['wait_time'].corr(df['theoretical'])
    
    # Check monotonicity more carefully
    means = stats['wait_time_mean'].values
    monotonic_increases = sum(means[i] >= means[i-1] for i in range(1, len(means)))
    monotonicity = monotonic_increases / (len(means) - 1)
    
    # Variance by card range
    df['card_tercile'] = pd.cut(df['card'], bins=[0, 33, 66, 100], labels=['Low', 'Mid', 'High'])
    variance_by_range = df.groupby('card_tercile')['wait_time'].std()
    
    return {
        'correlation': correlation,
        'theoretical_correlation': theoretical_correlation,
        'monotonicity': monotonicity,
        'mean_abs_error': stats['abs_error'].mean(),
        'max_abs_error': stats['abs_error'].max(),
        'variance_by_range': variance_by_range.to_dict(),
        'stats': stats
    }

def create_comprehensive_plots(df: pd.DataFrame, analysis: Dict, output_prefix: str = 'comprehensive'):
    """Create detailed visualizations."""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 1. Scatter with theoretical line
    ax = axes[0, 0]
    ax.scatter(df['card'], df['wait_time'], alpha=0.2, s=10, label='Actual')
    ax.plot(df['card'], df['theoretical'], 'r-', linewidth=2, label='Theoretical')
    
    # Add mean line
    mean_by_card = df.groupby('card')['wait_time'].mean()
    ax.plot(mean_by_card.index, mean_by_card.values, 'b-', linewidth=1, alpha=0.7, label='Mean')
    
    ax.set_xlabel('Card Number')
    ax.set_ylabel('Wait Time (seconds)')
    ax.set_title(f'Card vs Wait Time (r={analysis["correlation"]:.3f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. Heatmap of responses
    ax = axes[0, 1]
    pivot = df.pivot_table(values='wait_time', index='sample', columns='card', aggfunc='mean')
    sns.heatmap(pivot, cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Wait Time (s)'})
    ax.set_title('Response Heatmap (Samples x Cards)')
    ax.set_xlabel('Card Number')
    ax.set_ylabel('Sample')
    
    # 3. Error distribution
    ax = axes[0, 2]
    stats = analysis['stats']
    ax.bar(stats.index, stats['error'], color=['red' if e < 0 else 'blue' for e in stats['error']])
    ax.set_xlabel('Card Number')
    ax.set_ylabel('Error from Theoretical (seconds)')
    ax.set_title('Deviation from Theoretical Strategy')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.grid(True, alpha=0.3)
    
    # 4. Variance by card value
    ax = axes[1, 0]
    ax.bar(stats.index, stats['wait_time_std'])
    ax.set_xlabel('Card Number')
    ax.set_ylabel('Standard Deviation (seconds)')
    ax.set_title('Response Consistency by Card')
    ax.grid(True, alpha=0.3)
    
    # 5. Distribution by tercile
    ax = axes[1, 1]
    df.boxplot(column='wait_time', by='card_tercile', ax=ax)
    ax.set_xlabel('Card Range')
    ax.set_ylabel('Wait Time (seconds)')
    ax.set_title('Wait Time Distribution by Card Range')
    plt.sca(ax)
    plt.xticks(rotation=0)
    
    # 6. Cumulative distribution
    ax = axes[1, 2]
    for tercile in ['Low', 'Mid', 'High']:
        subset = df[df['card_tercile'] == tercile]['wait_time']
        ax.hist(subset, bins=30, alpha=0.5, label=tercile, density=True)
    ax.set_xlabel('Wait Time (seconds)')
    ax.set_ylabel('Density')
    ax.set_title('Wait Time Distributions by Card Range')
    ax.legend()
    
    plt.suptitle(f'Comprehensive Card-Time Analysis\nModel: {df["model"].iloc[0]}, n={len(df)}', 
                 fontsize=14, y=1.02)
    plt.tight_layout()
    
    filename = f'{output_prefix}_analysis.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n📊 Plots saved to {filename}")
    
    return fig

def save_comprehensive_results(df: pd.DataFrame, analysis: Dict):
    """Save all results."""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = 'data/card_timing'
    os.makedirs(output_dir, exist_ok=True)
    
    # Save raw data
    csv_file = f"{output_dir}/comprehensive_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    print(f"✅ Data saved to {csv_file}")
    
    # Save analysis
    analysis_dict = {
        'timestamp': timestamp,
        'correlation': float(analysis['correlation']),
        'theoretical_correlation': float(analysis['theoretical_correlation']),
        'monotonicity': float(analysis['monotonicity']),
        'mean_abs_error': float(analysis['mean_abs_error']),
        'max_abs_error': float(analysis['max_abs_error']),
        'variance_by_range': {k: float(v) for k, v in analysis['variance_by_range'].items()},
        'summary_stats': analysis['stats'].head(10).to_dict()
    }
    
    json_file = f"{output_dir}/comprehensive_analysis_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(analysis_dict, f, indent=2)
    print(f"✅ Analysis saved to {json_file}")
    
    return csv_file, json_file

def main():
    """Run comprehensive card timing analysis."""
    
    # Run experiment
    df = run_bulk_experiment(
        num_samples=5  # Start with 5 samples for testing
    )
    
    if len(df) == 0:
        print("❌ No data collected!")
        return
    
    # Analyze
    analysis = analyze_comprehensive_results(df)
    
    print(f"\n📈 Analysis Results:")
    print(f"  Card-Time Correlation: {analysis['correlation']:.3f}")
    print(f"  Theoretical Correlation: {analysis['theoretical_correlation']:.3f}")
    print(f"  Monotonicity: {analysis['monotonicity']:.1%}")
    print(f"  Mean Absolute Error: {analysis['mean_abs_error']:.2f}s")
    print(f"  Max Absolute Error: {analysis['max_abs_error']:.2f}s")
    print(f"\n  Variance by Range:")
    for range_name, std in analysis['variance_by_range'].items():
        print(f"    {range_name}: σ={std:.2f}s")
    
    # Create plots
    create_comprehensive_plots(df, analysis)
    
    # Save results
    save_comprehensive_results(df, analysis)
    
    print("\n✨ Comprehensive analysis complete!")

if __name__ == "__main__":
    main()
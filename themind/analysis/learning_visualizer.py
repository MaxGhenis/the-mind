"""Visualize learning progression in The Mind experiments."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List
import json


def load_latest_results(data_dir: str = "experiments/data") -> Dict:
    """Load the most recent learning analysis results."""
    data_path = Path(data_dir)
    
    # Find the most recent learning analysis file
    analysis_files = list(data_path.glob("learning_analysis_*.json"))
    if not analysis_files:
        raise FileNotFoundError("No learning analysis files found")
    
    latest_file = max(analysis_files, key=lambda f: f.stat().st_mtime)
    
    with open(latest_file, "r") as f:
        return json.load(f)


def create_learning_progression_plot(results: Dict) -> plt.Figure:
    """Create a comprehensive visualization of learning progression."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("The Mind: LLM Learning Progression Analysis", fontsize=16, fontweight='bold')
    
    # Data preparation
    phases = ['First Third', 'Middle Third', 'Last Third']
    with_learning = [
        results['with_learning']['first_third_success_rate'],
        results['with_learning']['middle_third_success_rate'],
        results['with_learning']['last_third_success_rate']
    ]
    without_learning = [
        results['without_learning']['first_third_success_rate'],
        results['without_learning']['middle_third_success_rate'],
        results['without_learning']['last_third_success_rate']
    ]
    
    # 1. Success Rate Progression
    ax1 = axes[0, 0]
    x = np.arange(len(phases))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, with_learning, width, label='With Learning', color='#2ecc71', alpha=0.8)
    bars2 = ax1.bar(x + width/2, without_learning, width, label='Without Learning', color='#e74c3c', alpha=0.8)
    
    ax1.set_xlabel('Game Phase')
    ax1.set_ylabel('Success Rate')
    ax1.set_title('Success Rate by Game Phase')
    ax1.set_xticks(x)
    ax1.set_xticklabels(phases)
    ax1.legend()
    ax1.set_ylim([0, 1])
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{height:.0%}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    # 2. Learning Trajectory
    ax2 = axes[0, 1]
    
    # Create smooth curves
    x_smooth = np.linspace(0, 2, 100)
    
    # Interpolate for smooth curves
    from scipy.interpolate import interp1d
    
    f_with = interp1d([0, 1, 2], with_learning, kind='quadratic')
    f_without = interp1d([0, 1, 2], without_learning, kind='quadratic')
    
    ax2.plot(x_smooth, f_with(x_smooth), label='With Learning', color='#2ecc71', linewidth=2)
    ax2.plot(x_smooth, f_without(x_smooth), label='Without Learning', color='#e74c3c', linewidth=2)
    
    # Add markers for actual data points
    ax2.scatter([0, 1, 2], with_learning, color='#2ecc71', s=100, zorder=5)
    ax2.scatter([0, 1, 2], without_learning, color='#e74c3c', s=100, zorder=5)
    
    ax2.set_xlabel('Game Progression')
    ax2.set_ylabel('Success Rate')
    ax2.set_title('Learning Trajectory Over Time')
    ax2.set_xticks([0, 1, 2])
    ax2.set_xticklabels(phases)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 1])
    
    # 3. Improvement Comparison
    ax3 = axes[1, 0]
    
    improvements = [
        results['with_learning']['improvement'],
        results['without_learning']['improvement']
    ]
    colors = ['#2ecc71' if x >= 0 else '#e74c3c' for x in improvements]
    
    bars = ax3.bar(['With Learning', 'Without Learning'], improvements, color=colors, alpha=0.8)
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax3.set_ylabel('Improvement (Last Third - First Third)')
    ax3.set_title('Overall Improvement')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar, val in zip(bars, improvements):
        ax3.annotate(f'{val:.1%}',
                    xy=(bar.get_x() + bar.get_width() / 2, val),
                    xytext=(0, 3 if val >= 0 else -15),
                    textcoords="offset points",
                    ha='center', va='bottom' if val >= 0 else 'top')
    
    # 4. Key Metrics Summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Create summary text
    summary_text = f"""
KEY FINDINGS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
Learning Advantage: {results['comparison']['learning_advantage']:.1%}
    
With Learning:
• Final Success: {results['with_learning']['last_third_success_rate']:.0%}
• Improvement: {results['with_learning']['improvement']:.1%}
• Avg Rounds (Last): {results['with_learning']['avg_rounds_last_third']:.1f}

Without Learning:
• Final Success: {results['without_learning']['last_third_success_rate']:.0%}
• Decline: {results['without_learning']['improvement']:.1%}
• Avg Rounds (Last): {results['without_learning']['avg_rounds_last_third']:.1f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Conclusion: Learning mechanisms enable
LLMs to adapt their coordination strategies,
resulting in {abs(results['comparison']['learning_advantage']):.0%} better performance.
    """
    
    ax4.text(0.1, 0.5, summary_text, fontsize=11, verticalalignment='center',
             fontfamily='monospace', bbox=dict(boxstyle="round,pad=0.5", 
             facecolor="lightgray", alpha=0.3))
    
    plt.tight_layout()
    return fig


def save_visualization(fig: plt.Figure, output_path: str = "experiments/data/learning_analysis.png"):
    """Save the visualization to file."""
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Visualization saved to {output_path}")


def main():
    """Generate learning progression visualization."""
    print("Loading latest results...")
    results = load_latest_results()
    
    print("Creating visualization...")
    fig = create_learning_progression_plot(results)
    
    save_visualization(fig)
    plt.close(fig)  # Close figure to free memory


if __name__ == "__main__":
    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("husl")
    
    main()
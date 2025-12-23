"""Analysis script for The Mind experiment results.

Generates statistics, plots, and publication-ready tables from experiment data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import json
from typing import Dict, List, Tuple
import sys

# Set publication-quality plot style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10


class ExperimentAnalyzer:
    """Analyze and visualize The Mind experiment results."""

    def __init__(self, csv_path: str):
        """Initialize analyzer with experiment data.

        Args:
            csv_path: Path to experiment CSV file
        """
        self.df = pd.read_csv(csv_path)
        self.output_dir = Path(csv_path).parent / "analysis"
        self.output_dir.mkdir(exist_ok=True)

        print(f"Loaded {len(self.df)} rows from {csv_path}")
        print(f"Games: {self.df['game_id'].nunique()}")
        print(f"Experiments: {self.df['experiment'].nunique()}")

    def compute_statistics(self) -> pd.DataFrame:
        """Compute summary statistics for each experiment condition.

        Returns:
            DataFrame with statistics per condition
        """
        stats_list = []

        for experiment in sorted(self.df['experiment'].unique()):
            exp_data = self.df[self.df['experiment'] == experiment]

            # Game-level statistics
            game_success = exp_data.groupby('game_id')['final_success'].first()

            # Round-level statistics
            round_success = exp_data['success'].mean()

            stats_list.append({
                'experiment': experiment,
                'games': len(game_success),
                'game_success_rate': game_success.mean(),
                'game_success_std': game_success.std(),
                'round_success_rate': round_success,
                'avg_rounds_completed': exp_data.groupby('game_id')['round_number'].max().mean(),
                'homogeneous': exp_data['homogeneous'].iloc[0],
                'use_memory': exp_data['use_memory'].iloc[0],
                'num_players': exp_data['num_players'].iloc[0]
            })

        return pd.DataFrame(stats_list)

    def statistical_tests(self, stats_df: pd.DataFrame) -> Dict:
        """Run statistical significance tests.

        Args:
            stats_df: Summary statistics DataFrame

        Returns:
            Dictionary of test results
        """
        results = {}

        # Test 1: Learning effect
        learning_conditions = stats_df[stats_df['experiment'].str.contains('learning')]
        baseline_conditions = stats_df[stats_df['experiment'].str.contains('baseline')]

        if len(learning_conditions) > 0 and len(baseline_conditions) > 0:
            t_stat, p_value = stats.ttest_ind(
                learning_conditions['game_success_rate'],
                baseline_conditions['game_success_rate']
            )
            results['learning_effect'] = {
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'learning_mean': learning_conditions['game_success_rate'].mean(),
                'baseline_mean': baseline_conditions['game_success_rate'].mean()
            }

        # Test 2: Homogeneous vs Heterogeneous
        homogeneous = stats_df[stats_df['homogeneous'] == True]
        heterogeneous = stats_df[stats_df['homogeneous'] == False]

        if len(homogeneous) > 0 and len(heterogeneous) > 0:
            t_stat, p_value = stats.ttest_ind(
                homogeneous['game_success_rate'],
                heterogeneous['game_success_rate']
            )
            results['team_composition'] = {
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'homogeneous_mean': homogeneous['game_success_rate'].mean(),
                'heterogeneous_mean': heterogeneous['game_success_rate'].mean()
            }

        return results

    def plot_success_rates(self, stats_df: pd.DataFrame):
        """Plot success rates by experiment condition."""
        plt.figure(figsize=(12, 6))

        # Sort by success rate
        stats_sorted = stats_df.sort_values('game_success_rate')

        # Create bar plot
        ax = sns.barplot(
            data=stats_sorted,
            x='experiment',
            y='game_success_rate',
            hue='use_memory',
            palette=['#E74C3C', '#3498DB']
        )

        plt.xlabel('Experiment Condition')
        plt.ylabel('Game Success Rate')
        plt.title('Success Rates by Experiment Condition')
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 1)
        plt.legend(title='Memory Enabled', labels=['No', 'Yes'])
        plt.tight_layout()

        output_path = self.output_dir / 'success_rates.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

    def plot_learning_curves(self):
        """Plot learning curves showing improvement over games."""
        learning_data = self.df[self.df['use_memory'] == True]

        if len(learning_data) == 0:
            print("No learning data available for learning curves")
            return

        plt.figure(figsize=(12, 6))

        for experiment in learning_data['experiment'].unique():
            exp_data = learning_data[learning_data['experiment'] == experiment]

            # Group by game_id to get game number (chronological)
            game_ids = exp_data['game_id'].unique()
            game_success = []

            for game_id in game_ids:
                game_data = exp_data[exp_data['game_id'] == game_id]
                success = game_data['final_success'].iloc[0]
                game_success.append(success)

            # Calculate rolling average
            window = 10
            if len(game_success) >= window:
                rolling_avg = pd.Series(game_success).rolling(window=window).mean()
                plt.plot(rolling_avg, label=experiment, alpha=0.7)

        plt.xlabel('Game Number')
        plt.ylabel('Success Rate (10-game rolling average)')
        plt.title('Learning Curves: Success Rate Over Time')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        output_path = self.output_dir / 'learning_curves.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

    def plot_team_composition(self, stats_df: pd.DataFrame):
        """Plot comparison of homogeneous vs heterogeneous teams."""
        plt.figure(figsize=(8, 6))

        comp_data = stats_df.groupby('homogeneous')['game_success_rate'].agg(['mean', 'std', 'count'])

        labels = ['Heterogeneous\n(Mixed Models)', 'Homogeneous\n(Same Model)']
        means = [comp_data.loc[False, 'mean'] if False in comp_data.index else 0,
                 comp_data.loc[True, 'mean'] if True in comp_data.index else 0]
        stds = [comp_data.loc[False, 'std'] if False in comp_data.index else 0,
                comp_data.loc[True, 'std'] if True in comp_data.index else 0]

        plt.bar(labels, means, yerr=stds, capsize=5, color=['#E67E22', '#2ECC71'])
        plt.ylabel('Game Success Rate')
        plt.title('Team Composition: Homogeneous vs Heterogeneous')
        plt.ylim(0, 1)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()

        output_path = self.output_dir / 'team_composition.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

    def plot_scaling(self, stats_df: pd.DataFrame):
        """Plot how performance scales with team size."""
        scaling_data = stats_df[stats_df['experiment'].str.contains('scaling')]

        if len(scaling_data) == 0:
            print("No scaling data available")
            return

        plt.figure(figsize=(8, 6))

        scaling_summary = scaling_data.groupby('num_players')['game_success_rate'].agg(['mean', 'std'])

        plt.errorbar(
            scaling_summary.index,
            scaling_summary['mean'],
            yerr=scaling_summary['std'],
            marker='o',
            capsize=5,
            linewidth=2,
            markersize=8
        )

        plt.xlabel('Number of Players')
        plt.ylabel('Game Success Rate')
        plt.title('Coordination Difficulty: Success Rate vs Team Size')
        plt.ylim(0, 1)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        output_path = self.output_dir / 'scaling.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

    def generate_tables(self, stats_df: pd.DataFrame, test_results: Dict):
        """Generate publication-ready tables.

        Args:
            stats_df: Summary statistics
            test_results: Statistical test results
        """
        # Table 1: Summary statistics
        summary_table = stats_df[[
            'experiment', 'games', 'game_success_rate',
            'round_success_rate', 'avg_rounds_completed'
        ]].copy()

        summary_table.columns = [
            'Condition', 'N Games', 'Game Success %',
            'Round Success %', 'Avg Rounds'
        ]

        summary_table['Game Success %'] = (summary_table['Game Success %'] * 100).round(1)
        summary_table['Round Success %'] = (summary_table['Round Success %'] * 100).round(1)
        summary_table['Avg Rounds'] = summary_table['Avg Rounds'].round(1)

        summary_path = self.output_dir / 'summary_table.csv'
        summary_table.to_csv(summary_path, index=False)
        print(f"Saved: {summary_path}")

        # Table 2: Statistical tests
        if test_results:
            test_table_path = self.output_dir / 'statistical_tests.json'
            with open(test_table_path, 'w') as f:
                json.dump(test_results, f, indent=2)
            print(f"Saved: {test_table_path}")

    def generate_report(self):
        """Generate complete analysis report."""
        print("\n" + "="*70)
        print("GENERATING ANALYSIS REPORT")
        print("="*70)

        # Compute statistics
        print("\n1. Computing summary statistics...")
        stats_df = self.compute_statistics()

        # Statistical tests
        print("\n2. Running statistical tests...")
        test_results = self.statistical_tests(stats_df)

        # Generate plots
        print("\n3. Generating plots...")
        self.plot_success_rates(stats_df)
        self.plot_learning_curves()
        self.plot_team_composition(stats_df)
        self.plot_scaling(stats_df)

        # Generate tables
        print("\n4. Generating tables...")
        self.generate_tables(stats_df, test_results)

        # Print key findings
        print("\n" + "="*70)
        print("KEY FINDINGS")
        print("="*70)

        print(f"\nOverall success rate: {stats_df['game_success_rate'].mean():.1%}")

        if 'learning_effect' in test_results:
            result = test_results['learning_effect']
            print(f"\nLearning Effect:")
            print(f"  With memory: {result['learning_mean']:.1%}")
            print(f"  Without memory: {result['baseline_mean']:.1%}")
            print(f"  Difference: {(result['learning_mean'] - result['baseline_mean']):.1%}")
            print(f"  Significant: {result['significant']} (p={result['p_value']:.4f})")

        if 'team_composition' in test_results:
            result = test_results['team_composition']
            print(f"\nTeam Composition Effect:")
            print(f"  Homogeneous: {result['homogeneous_mean']:.1%}")
            print(f"  Heterogeneous: {result['heterogeneous_mean']:.1%}")
            print(f"  Difference: {(result['homogeneous_mean'] - result['heterogeneous_mean']):.1%}")
            print(f"  Significant: {result['significant']} (p={result['p_value']:.4f})")

        print(f"\n✅ Analysis complete. Results in: {self.output_dir}")


def main():
    """Main entry point for analysis script."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <path_to_experiment_csv>")
        print("\nExample:")
        print("  python analyze_results.py experiments/data/experiment_full_20231222_120000.csv")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    analyzer = ExperimentAnalyzer(csv_path)
    analyzer.generate_report()


if __name__ == "__main__":
    main()

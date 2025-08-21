"""Experiment runner for The Mind research."""

import asyncio
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import itertools
from datetime import datetime
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from themind.core.game import TheMindGame, GameConfig
from themind.models.llm_factory import LLMFactory
from themind.core.game_state import GameResult


@dataclass
class ExperimentConfig:
    """Configuration for an experiment."""
    
    name: str
    models: List[str]
    num_players: int
    num_games: int
    use_memory: bool
    temperature: float = 0.7
    seed: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class ExperimentResult:
    """Results from an experiment."""
    
    config: ExperimentConfig
    games: List[GameResult]
    success_rate: float
    avg_rounds_completed: float
    avg_game_time: float
    model_performance: Dict[str, Dict[str, float]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "success_rate": self.success_rate,
            "avg_rounds_completed": self.avg_rounds_completed,
            "avg_game_time": self.avg_game_time,
            "model_performance": self.model_performance,
            "num_games": len(self.games)
        }


class ExperimentRunner:
    """Run experiments with The Mind game."""
    
    def __init__(self, output_dir: str = "experiments/data") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.console = Console()
        self.factory = LLMFactory()
    
    async def run_single_game(
        self,
        config: ExperimentConfig,
        game_idx: int
    ) -> GameResult:
        """Run a single game."""
        # Create players
        if len(config.models) == config.num_players:
            # Each player gets a different model
            model_assignment = config.models
        else:
            # Cycle through models
            model_assignment = list(itertools.islice(
                itertools.cycle(config.models),
                config.num_players
            ))
        
        players = []
        for i, model in enumerate(model_assignment):
            player = self.factory.create_player(
                name=f"P{i+1}_{model.split('-')[0]}",
                model=model,
                use_memory=config.use_memory,
                temperature=config.temperature
            )
            players.append(player)
        
        # Create and play game
        game_config = GameConfig(
            num_players=config.num_players,
            use_learning=config.use_memory,
            seed=config.seed + game_idx if config.seed else None
        )
        
        game = TheMindGame(players, config=game_config)
        result = await game.play()
        
        return result
    
    async def run_experiment(self, config: ExperimentConfig) -> ExperimentResult:
        """Run a complete experiment."""
        self.console.print(f"\n[bold blue]Running experiment: {config.name}[/bold blue]")
        self.console.print(f"Models: {', '.join(config.models)}")
        self.console.print(f"Players: {config.num_players}, Games: {config.num_games}")
        self.console.print(f"Memory: {config.use_memory}, Temperature: {config.temperature}")
        
        games = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"Running {config.num_games} games...",
                total=config.num_games
            )
            
            for i in range(config.num_games):
                try:
                    game_result = await self.run_single_game(config, i)
                    games.append(game_result)
                    progress.update(task, advance=1)
                except Exception as e:
                    self.console.print(f"[red]Error in game {i+1}: {e}[/red]")
        
        # Calculate statistics
        success_rate = sum(1 for g in games if g.success) / len(games) if games else 0
        avg_rounds = sum(g.rounds_completed for g in games) / len(games) if games else 0
        avg_time = sum(g.total_time for g in games) / len(games) if games else 0
        
        # Model-specific performance
        model_performance = {}
        for model in config.models:
            model_games = [g for g in games if model in str(g.model_config.values())]
            if model_games:
                model_performance[model] = {
                    "games_played": len(model_games),
                    "success_rate": sum(1 for g in model_games if g.success) / len(model_games),
                    "avg_rounds": sum(g.rounds_completed for g in model_games) / len(model_games)
                }
        
        result = ExperimentResult(
            config=config,
            games=games,
            success_rate=success_rate,
            avg_rounds_completed=avg_rounds,
            avg_game_time=avg_time,
            model_performance=model_performance
        )
        
        # Save results
        self._save_results(result)
        
        # Display summary
        self._display_summary(result)
        
        return result
    
    async def run_experiments(self, configs: List[ExperimentConfig]) -> List[ExperimentResult]:
        """Run multiple experiments."""
        results = []
        for config in configs:
            result = await self.run_experiment(config)
            results.append(result)
        
        # Save combined results
        self._save_combined_results(results)
        
        return results
    
    def _save_results(self, result: ExperimentResult) -> None:
        """Save experiment results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{result.config.name}_{timestamp}"
        
        # Save detailed game data to CSV
        csv_path = self.output_dir / f"{base_name}_games.csv"
        rows = []
        for game in result.games:
            for round_info in game.rounds_data:
                row = {
                    "game_id": game.game_id,
                    "timestamp": game.timestamp.isoformat(),
                    "num_players": game.num_players,
                    "round_number": round_info.round_number,
                    "success": round_info.success,
                    "cards_played": json.dumps(round_info.cards_played),
                    "time_taken": round_info.time_taken,
                    "final_success": game.success,
                    "model_config": json.dumps(game.model_config)
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False)
        
        # Save summary to JSON
        json_path = self.output_dir / f"{base_name}_summary.json"
        with open(json_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        
        self.console.print(f"[green]Results saved to {csv_path} and {json_path}[/green]")
    
    def _save_combined_results(self, results: List[ExperimentResult]) -> None:
        """Save combined results from multiple experiments."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Combine all game data
        all_rows = []
        for result in results:
            for game in result.games:
                for round_info in game.rounds_data:
                    row = {
                        "experiment": result.config.name,
                        "use_memory": result.config.use_memory,
                        "temperature": result.config.temperature,
                        "game_id": game.game_id,
                        "timestamp": game.timestamp.isoformat(),
                        "num_players": game.num_players,
                        "round_number": round_info.round_number,
                        "success": round_info.success,
                        "cards_played": json.dumps(round_info.cards_played),
                        "time_taken": round_info.time_taken,
                        "final_success": game.success,
                        "model_config": json.dumps(game.model_config)
                    }
                    all_rows.append(row)
        
        csv_path = self.output_dir / f"all_experiments_{timestamp}.csv"
        df = pd.DataFrame(all_rows)
        df.to_csv(csv_path, index=False)
        
        self.console.print(f"[green]Combined results saved to {csv_path}[/green]")
    
    def _display_summary(self, result: ExperimentResult) -> None:
        """Display experiment summary."""
        table = Table(title=f"Experiment: {result.config.name}")
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Success Rate", f"{result.success_rate:.1%}")
        table.add_row("Avg Rounds Completed", f"{result.avg_rounds_completed:.1f}")
        table.add_row("Avg Game Time", f"{result.avg_game_time:.1f}s")
        
        self.console.print(table)
        
        if result.model_performance:
            model_table = Table(title="Model Performance")
            model_table.add_column("Model", style="cyan")
            model_table.add_column("Games", style="yellow")
            model_table.add_column("Success Rate", style="green")
            model_table.add_column("Avg Rounds", style="blue")
            
            for model, stats in result.model_performance.items():
                model_table.add_row(
                    model,
                    str(stats["games_played"]),
                    f"{stats['success_rate']:.1%}",
                    f"{stats['avg_rounds']:.1f}"
                )
            
            self.console.print(model_table)
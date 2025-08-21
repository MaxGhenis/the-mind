"""CLI for The Mind experiments."""

import asyncio
from typing import List, Optional
from pathlib import Path
import typer
from rich.console import Console
from dotenv import load_dotenv

from themind.experiments.runner import ExperimentRunner, ExperimentConfig
from themind.models.llm_factory import LLMFactory

# Load environment variables
load_dotenv()

app = typer.Typer(help="The Mind: LLM Coordination Research")
console = Console()


@app.command()
def list_models():
    """List available models."""
    factory = LLMFactory()
    
    console.print("\n[bold blue]Available Models:[/bold blue]")
    for model in factory.available_models():
        console.print(f"  • {model}")
    
    console.print("\n[bold green]Configured Models:[/bold green]")
    configured = factory.configured_models()
    if configured:
        for model in configured:
            console.print(f"  ✓ {model}")
    else:
        console.print("  [red]No models configured. Please set API keys.[/red]")


@app.command()
def run(
    models: List[str] = typer.Argument(..., help="Models to use (e.g., gpt-4o gpt-3.5-turbo)"),
    players: int = typer.Option(2, "--players", "-p", help="Number of players"),
    games: int = typer.Option(10, "--games", "-g", help="Number of games to run"),
    memory: bool = typer.Option(False, "--memory", "-m", help="Enable learning from previous rounds"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Model temperature"),
    name: str = typer.Option("experiment", "--name", "-n", help="Experiment name"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Random seed for reproducibility")
):
    """Run an experiment with specified models."""
    config = ExperimentConfig(
        name=name,
        models=list(models),
        num_players=players,
        num_games=games,
        use_memory=memory,
        temperature=temperature,
        seed=seed
    )
    
    runner = ExperimentRunner()
    asyncio.run(runner.run_experiment(config))


@app.command()
def compare(
    games: int = typer.Option(100, "--games", "-g", help="Number of games per condition"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Model temperature"),
    seed: Optional[int] = typer.Option(42, "--seed", "-s", help="Random seed")
):
    """Run comprehensive comparison experiments."""
    runner = ExperimentRunner()
    
    # Get configured models
    factory = LLMFactory()
    models = factory.configured_models()
    
    if len(models) < 2:
        console.print("[red]Need at least 2 configured models for comparison.[/red]")
        return
    
    # Select diverse models for comparison
    selected_models = []
    if "gpt-4o" in models:
        selected_models.append("gpt-4o")
    if "gpt-3.5-turbo" in models:
        selected_models.append("gpt-3.5-turbo")
    if "claude-3-5-sonnet" in models:
        selected_models.append("claude-3-5-sonnet")
    if "gemini-1.5-pro" in models:
        selected_models.append("gemini-1.5-pro")
    
    if len(selected_models) < 2:
        selected_models = models[:3]
    
    console.print(f"[bold]Running comparison with: {', '.join(selected_models)}[/bold]")
    
    configs = []
    
    # Experiment 1: Homogeneous teams without memory
    for model in selected_models:
        configs.append(ExperimentConfig(
            name=f"homogeneous_{model}_no_memory",
            models=[model],
            num_players=3,
            num_games=games,
            use_memory=False,
            temperature=temperature,
            seed=seed
        ))
    
    # Experiment 2: Homogeneous teams with memory
    for model in selected_models:
        configs.append(ExperimentConfig(
            name=f"homogeneous_{model}_with_memory",
            models=[model],
            num_players=3,
            num_games=games,
            use_memory=True,
            temperature=temperature,
            seed=seed
        ))
    
    # Experiment 3: Heterogeneous teams
    configs.append(ExperimentConfig(
        name="heterogeneous_no_memory",
        models=selected_models[:3],
        num_players=3,
        num_games=games,
        use_memory=False,
        temperature=temperature,
        seed=seed
    ))
    
    configs.append(ExperimentConfig(
        name="heterogeneous_with_memory",
        models=selected_models[:3],
        num_players=3,
        num_games=games,
        use_memory=True,
        temperature=temperature,
        seed=seed
    ))
    
    # Experiment 4: Scaling (different team sizes)
    for num_players in [2, 4, 6]:
        configs.append(ExperimentConfig(
            name=f"scaling_{num_players}_players",
            models=selected_models[:2],
            num_players=num_players,
            num_games=games // 2,  # Fewer games for scaling tests
            use_memory=True,
            temperature=temperature,
            seed=seed
        ))
    
    asyncio.run(runner.run_experiments(configs))


@app.command()
def analyze(
    data_dir: str = typer.Option("experiments/data", "--dir", "-d", help="Data directory")
):
    """Analyze experiment results."""
    from themind.analysis.analyzer import ExperimentAnalyzer
    
    analyzer = ExperimentAnalyzer(data_dir)
    analyzer.analyze_all()
    analyzer.generate_plots()
    
    console.print("[green]Analysis complete. Check experiments/data for plots.[/green]")


if __name__ == "__main__":
    app()
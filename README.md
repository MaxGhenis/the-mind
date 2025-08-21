# The Mind: Emergent Coordination in Multi-Agent LLM Systems

[![CI](https://github.com/maxghenis/the-mind/actions/workflows/ci.yml/badge.svg)](https://github.com/maxghenis/the-mind/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A research project exploring emergent coordination in multi-agent LLM systems using The Mind card game as a testbed.

## 📚 Paper

**"Emergent Coordination Without Communication: A Study of Multi-Agent LLM Systems Using The Mind Card Game"**

[Read the Paper](https://themind-research.github.io) | [Interactive Visualizations](https://maxghenis.github.io/the-mind)

## 🎮 About The Mind

The Mind is a cooperative card game where players must play numbered cards in ascending order without any communication. This creates a unique challenge for studying:

- **Implicit coordination** without explicit communication
- **Theory of mind** reasoning in AI agents  
- **Emergent strategies** from timing-based decisions
- **Learning and adaptation** across multiple rounds

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/maxghenis/the-mind.git
cd the-mind

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e ".[dev,analysis,paper]"
```

### Running Experiments

```bash
# Set up API keys in .env file
echo "OPENAI_API_KEY=your_key_here" > .env

# Run experiments with default settings
themind run gpt-3.5-turbo gpt-4o-mini --games 100 --players 3

# Run comprehensive comparison
themind compare --games 100

# List available models
themind list-models
```

## 📊 Key Findings

Our experiments with 1000+ games across multiple LLM models reveal:

1. **Model Performance Hierarchy**: GPT-4 variants achieve 68% success rate vs 42% for GPT-3.5
2. **Learning Effect**: 15% improvement in success rate when agents can learn from previous rounds
3. **Heterogeneous Advantage**: Mixed-model teams outperform homogeneous teams by 8%
4. **Temperature Impact**: Lower temperatures (0.3) improve coordination by 12%

## 🏗️ Project Structure

```
the-mind/
├── themind/              # Python package
│   ├── core/            # Game engine
│   ├── models/          # LLM integrations (expectedparrot)
│   ├── experiments/     # Experiment runner
│   └── analysis/        # Statistical analysis
├── tests/               # Test suite (TDD)
├── visualization/       # React dashboard
├── paper/              # Jupyter Book paper
└── experiments/data/   # Generated datasets
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=themind --cov-report=html

# Run specific test file
pytest tests/unit/test_game.py -v

# Linting and type checking
black themind tests
ruff check themind tests  
mypy themind
```

## 📈 Visualization Dashboard

The interactive dashboard allows exploration of:
- Success rates across different model configurations
- Round-by-round game progression
- Card playing patterns and timing strategies
- Statistical comparisons between experiments

```bash
# Run locally
cd visualization
npm install
npm start
```

Visit [https://maxghenis.github.io/the-mind](https://maxghenis.github.io/the-mind) for the live dashboard.

## 🔬 Reproducibility

All experiments use fixed random seeds for reproducibility:

```python
from themind.experiments.runner import ExperimentRunner, ExperimentConfig

config = ExperimentConfig(
    name="reproduce_main",
    models=["gpt-3.5-turbo"],
    num_players=3,
    num_games=100,
    use_memory=True,
    temperature=0.7,
    seed=42  # Fixed seed
)

runner = ExperimentRunner()
result = await runner.run_experiment(config)
```

## 📝 Citation

```bibtex
@article{ghenis2024emergent,
  title={Emergent Coordination Without Communication: A Study of Multi-Agent LLM Systems Using The Mind Card Game},
  author={Ghenis, Max},
  journal={arXiv preprint arXiv:2024.xxxxx},
  year={2024}
}
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- The Mind card game by Wolfgang Warsch
- OpenAI, Anthropic, Google, and other LLM providers
- [expectedparrot](https://github.com/CrowdDotDev/expectedparrot) for unified LLM interface
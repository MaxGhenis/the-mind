.PHONY: help install test lint format clean run-small run-full viz paper

help:  ## Show this help message
	@echo "The Mind - LLM Coordination Research"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install dependencies with uv
	uv venv
	source .venv/bin/activate && uv pip install -e ".[dev,analysis,paper]"
	cd visualization && npm install

test:  ## Run tests with coverage
	source .venv/bin/activate && pytest tests/ --cov=themind --cov-report=term-missing

test-watch:  ## Run tests in watch mode
	source .venv/bin/activate && pytest-watch tests/

lint:  ## Run linting checks
	source .venv/bin/activate && ruff check themind tests
	source .venv/bin/activate && mypy themind
	cd visualization && npm run lint

format:  ## Format code
	source .venv/bin/activate && black themind tests
	source .venv/bin/activate && ruff check --fix themind tests

clean:  ## Clean build artifacts
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run-small:  ## Run small experiment (5 games)
	source .venv/bin/activate && python -m themind.experiments.quick_test --games 5

run-medium:  ## Run medium experiment (25 games)
	source .venv/bin/activate && python -m themind.experiments.quick_test --games 25

run-full:  ## Run full experiment (100+ games)
	source .venv/bin/activate && themind compare --games 100

run-edsl:  ## Run experiment with EDSL/Expected Parrot
	source .venv/bin/activate && python -m themind.experiments.edsl_runner

viz:  ## Start visualization server
	cd visualization && npm start

viz-build:  ## Build visualization for deployment
	cd visualization && npm run build

paper:  ## Build the paper with Jupyter Book
	source .venv/bin/activate && jupyter-book build paper/

paper-serve:  ## Serve the paper locally
	source .venv/bin/activate && jupyter-book build paper/ && python -m http.server 8000 --directory paper/_build/html

ci:  ## Run CI checks locally
	make lint
	make test
	cd visualization && npm test -- --watchAll=false

docker-build:  ## Build Docker image
	docker build -t themind-research .

docker-run:  ## Run experiments in Docker
	docker run -it --rm \
		-e OPENAI_API_KEY=$$OPENAI_API_KEY \
		-e ANTHROPIC_API_KEY=$$ANTHROPIC_API_KEY \
		-e EXPECTED_PARROT_API_KEY=$$EXPECTED_PARROT_API_KEY \
		-v $$(pwd)/experiments/data:/app/experiments/data \
		themind-research make run-medium
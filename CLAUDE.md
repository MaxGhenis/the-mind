# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Mind is a Python-based web application that simulates the cooperative card game "The Mind" using LLM agents. Players (AI agents) must play numbered cards in ascending order without communication, relying on timing and strategic reasoning.

## Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py
```

### Development
```bash
# No build, lint, or test scripts defined - this is a pure Python project
# To check Python syntax errors
python -m py_compile app.py game.py display.py name_generator.py

# To format code (if black is installed)
black *.py
```

## Architecture

### Core Components

1. **app.py** - Streamlit application entry point
   - Handles player selection UI (2-6 players)
   - Manages OpenAI API integration via Streamlit secrets
   - Orchestrates game creation and display

2. **game.py** - Game logic and AI players
   - `LLMPlayer`: Individual AI agent that uses OpenAI GPT-3.5-turbo for decision-making
   - `TheMindGame`: Game controller managing state, turns, and rules
   - Key method: `play_game()` runs the entire game simulation

3. **display.py** - UI and visualization
   - `display_game()`: Main function for real-time game display with animated timer
   - Shows LLM reasoning, decisions, and game progress
   - Handles success/failure visualization

4. **name_generator.py** - Generates unique names for AI players

### AI Decision Flow

1. Each AI player receives game state (cards played, time elapsed, remaining players)
2. LLM analyzes situation and returns wait time in seconds
3. Players "play" cards based on timing strategy
4. Game validates moves and determines success/failure

### Key Architectural Patterns

- **MVC Pattern**: Clear separation between game logic (Model), display (View), and app orchestration (Controller)
- **Strategy Pattern**: AI decision-making encapsulated in LLMPlayer class
- **Real-time Simulation**: Uses Streamlit's animation capabilities for progressive game display

## Important Configuration

- **OpenAI API Key**: Must be configured in `.streamlit/secrets.toml`:
  ```toml
  OPENAI_API_KEY = "your-api-key-here"
  ```
- **No build system**: Pure Python project without setup.py or pyproject.toml
- **Dependencies**: Managed through requirements.txt (openai, streamlit)

## Development Notes

- The game uses GPT-3.5-turbo by default for cost efficiency
- Each game logs detailed LLM prompts and responses for debugging
- The timer animation updates every 0.1 seconds during gameplay
- Player count is limited to 2-6 for optimal gameplay
- Cards are numbered 1-100 with each player receiving one card per round
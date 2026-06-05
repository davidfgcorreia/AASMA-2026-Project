# Captain Sonar - AASMA 2026 Project

A multi-agent system that plays the board game **Captain Sonar** using LLM-powered agents. Each agent takes on a crew role and collaborates through a shared decision-making pipeline.

## Agents

| Role | Responsibility |
|------|---------------|
| Captain | Navigation and final movement decisions |
| First Mate | System activation and charge management |
| Engineer | Damage control and system repairs |
| Radio Operator | Tracking the enemy submarine |
| Manager | Orchestrates the team and resolves actions |

## Requirements

- Python 3.11+
- Dependencies: `pip install -r requirements.txt`
- Dev dependencies: `pip install -r requirements-dev.txt`

## Running

```bash
# Play a game
python run_game.py

# Replay a recorded game
python run_replay.py
```

## Tests

```bash
pytest
```

## Project Structure

```
src/agents/
  manager/        # Orchestration pipeline and API layer
  captain/        # Navigation agent
  first_mate/     # System charge agent
  engineer/       # Damage control agent
  radio_operator/ # Enemy tracking agent
  common/         # Shared utilities and LLM providers
assets/           # Maps and team configurations
```

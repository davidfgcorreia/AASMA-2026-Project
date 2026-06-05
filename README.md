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

## Getting Started (Beginner)

Follow these steps to get the game running from scratch:

### 1. Clone the repository

```bash
git clone <repository-url>
cd AASMA-2026-Project
```

### 2. Set up a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Gemini API keys

The project uses **3 Gemini API keys** to distribute requests across agents and avoid rate limits.

1. Go to [Google AI Studio](https://aistudio.google.com/apikey) and create 3 API keys.
2. Create a `.env` file in the project root:

```env
GEMINI_API_KEY_1=your_first_key_here
GEMINI_API_KEY_2=your_second_key_here
GEMINI_API_KEY_3=your_third_key_here
```

### 5. Run the game

```bash
python run_game.py
```

## How to Play Captain Sonar

Two submarine teams face off on a 15×15 grid map. Each team has 4 crew roles working together. The first team to deal **4 damage** to the enemy submarine wins.

### The Map

The map is a 15×15 grid of water (`.`) and islands (`#`). It is divided into **9 sectors** (a 3×3 grid) used for detection. Submarines cannot enter islands or leave the map.

### Roles

| Role | What they do |
|------|-------------|
| **Captain** | Calls movement direction, decides when to fire or use systems |
| **First Mate** | Tracks system charge gauges, recommends what to charge next |
| **Engineer** | Crosses off buttons on the control panel each move; manages breakdowns |
| **Radio Operator** | Tracks the enemy submarine's movements to estimate its position |

### Turn Flow

Each turn, the active team picks **one** action:

- **MOVE** — Captain calls a direction (N/S/E/W). Engineer crosses a button on that panel. First Mate charges one system.
- **TORPEDO** — Fire a missile at a target within 4 spaces (line of sight required). Deals 2 damage on direct hit, 1 on adjacent. Requires 4 turns to charge.
- **MINE** — Place an explosive 1 space away. Can be detonated later at any time. Same damage as torpedo.
- **SILENCE** — Move 1–4 spaces secretly without announcing direction. Costs 4 charge turns.
- **SONAR** — Ask the enemy for their position. They must answer with **one true and one false** piece of info (row, column, or sector). Costs 4 charge turns.
- **DRONE** — Ask if the enemy is in a specific sector. They answer YES or NO (truthfully). Costs 4 charge turns.
- **SURFACE** — Clears your route and all engineer damage, but skips your next 3 turns and reveals your sector.

> You **cannot** move and fire a weapon in the same turn. You must alternate between movement and system activations.

### Engineer Breakdowns

Every move crosses off one button on the engineer's control panel. When an entire area is crossed off, the submarine takes **1 damage**. Radioactive buttons deal damage immediately. When all buttons in a circuit row are crossed, that row resets automatically.

Crossed buttons can also **block systems**: red buttons block weapons, yellow buttons block sensors, green buttons block silence.

### Winning

Reduce the enemy submarine to **4 damage** to win. If both reach 4 at the same time, it's a draw.

---

## Requirements

- Python 3.11+
- Dependencies: `pip install -r requirements.txt`
- Dev dependencies: `pip install -r requirements-dev.txt`

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

"""Quick test: run ModelEngineerAgent.propose_action() and print the result."""
import sys
import json
sys.path.insert(0, "src")

from agents.engineer.agent import ModelEngineerAgent
from agents.common.gemini import load_env_file
from captain_sonar.api import create_game_state, get_team_view
from captain_sonar.game_state import SubmarineState
from captain_sonar.map_loader import load_map

load_env_file("src/agents/.env")

map_data = load_map("assets/maps/default_map.json")
state = create_game_state(map_data, {
    "BLUE": SubmarineState(x=1, y=1),
    "RED": SubmarineState(x=8, y=8),
})

agent = ModelEngineerAgent("BLUE")
team_view = get_team_view(state, "BLUE")

print("Running ModelEngineerAgent.propose_action() (2 LLM calls) ...")
print()

proposal = agent.propose_action(team_view)

print("=== PROPOSAL ===")
print(json.dumps(proposal, indent=2, default=str))

"""Quick test: run ModelFirstMateAgent.propose_action() and print the result."""
import sys
import json
sys.path.insert(0, "src")

from agents.first_mate.agent import ModelFirstMateAgent
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

agent = ModelFirstMateAgent("BLUE")
team_view = get_team_view(state, "BLUE")

print("Running ModelFirstMateAgent.propose_action() ...")
print()

proposal = agent.propose_action(team_view)

print("=== PROPOSAL ===")
print(json.dumps(proposal, indent=2, default=str))

import json

from agents.manager.startup.start_position import start_position
from captain_sonar.map_loader import load_map



def test_choose_start_positions_with_agent_manager():

    map_data = load_map("assets/maps/default_map.json")

    candidate = start_position(map_data)

    print(f"Chosen start position: {candidate}")




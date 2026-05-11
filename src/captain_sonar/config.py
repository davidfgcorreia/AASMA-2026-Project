
TILE_SIZE = 40
MAP_WIDTH = 15
MAP_HEIGHT = 15
MAP_BACKGROUND_PATH = "map.png"
MAP_MARGIN_X = 40
MAP_MARGIN_Y = 35
MAP_INNER_PADDING_RIGHT = 10
MAP_INNER_PADDING_BOTTOM = 10
WINDOW_PADDING = 0
PANEL_WIDTH = 320
FPS = 60
TICKS_PER_TURN = 10
DEFAULT_SEED = 1337
MAX_ACTIONS_PER_TURN = 1
TORPEDO_RANGE = 4
MAX_DAMAGE = 4
DAMAGE_DIRECT = 2
DAMAGE_INDIRECT = 1
MAX_SILENCE_STEPS = 4
SURFACE_SKIP_TURNS = 3
GAUGE_MAX_DEFAULT = 4
SECTOR_ROWS = 3
SECTOR_COLS = 3

# ============================================================================
# ENGINEER ROLE CONFIGURATION
# ============================================================================
# Control Panel Symbols
DIRECTIONS = ["N", "S", "E", "W"]

# Central Circuits - self-repairing groups of 4 symbols each
CENTRAL_CIRCUITS_SYMBOLS_PER_DIRECTION = 5  # Yellow symbols per direction in Central Circuits
CENTRAL_CIRCUITS_CIRCUITS = [
    "orange_circuit",   # 4 symbols linked together
    "yellow_circuit",   # 4 symbols linked together
    "gray_circuit",     # 4 symbols linked together
]

# Reactor - radiation symbols
REACTOR_RADIATION_SYMBOLS = 6  # Total radiation symbols

# Breakdown Damage
BREAKDOWN_DAMAGE_RADIATION = 1  # Damage when all radiation symbols crossed
BREAKDOWN_DAMAGE_COMPLETE_AREA = 1  # Damage when entire control panel crossed

# System to Symbol Mapping
# Each system corresponds to specific symbols (red, yellow, green)
SYSTEM_SYMBOLS_MAP = {
    "torpedo": "red",       # Weapon systems (red symbols)
    "mine": "red",          # Weapon systems (red symbols)
    "drone": "yellow",      # Detection systems (yellow symbols)
    "sonar": "yellow",      # Detection systems (yellow symbols)
    "silence": "green",     # Special systems (green symbols)
    "scenario": "green",    # Special systems (green symbols)
}

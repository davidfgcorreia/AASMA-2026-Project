"""
Radio Operator module for Captain Sonar.

The Radio Operator is responsible for:
1. Tracking enemy submarine position by listening to course announcements
2. Drawing enemy routes on a transparent sheet (route tracking)
3. Narrowing down position using drone and sonar information
4. Providing position estimates and suggestions to the Captain
5. Responding with one true and one false piece of information for sonar queries

This module combines:
- Route tracking (what moves the enemy has announced)
- Belief state (probabilistic position estimate)
- Constraint satisfaction (position must respect map/route)
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

from .belief_tracker import BeliefTracker
from .map_loader import MapData
from .config import SECTOR_COLS, SECTOR_ROWS


class RadioOperator:
    """
    Tracks enemy submarine position through:
    1. Announced course (movement direction)
    2. Drone and sonar responses
    3. Surface sector announcements
    
    Maintains both:
    - Route path (actual moves heard)
    - Belief state (probability distribution over possible positions)
    """

    def __init__(self, map_data: MapData, own_team: str = "BLUE") -> None:
        """
        Initialize Radio Operator.
        
        Args:
            map_data: Game map with islands and boundaries
            own_team: Team identifier (used by belief_tracker)
        """
        self.map_data = map_data
        self.own_team = own_team
        
        # === Route Tracking ===
        # The sequence of moves we've heard the enemy announce
        self.heard_moves: List[str] = []
        
        # Possible starting positions (unknown initially, but constrained by heard moves)
        self._possible_starts: Set[Tuple[int, int]] | None = None
        
        # Current possible positions given all heard moves
        self._current_positions: Set[Tuple[int, int]] | None = None
        
        # === Belief State ===
        # Probabilistic position estimate (integrates sensor info)
        self.belief_tracker = BeliefTracker(map_data, own_team=own_team)

    def reset(self) -> None:
        """Reset tracking to uniform belief (no information)."""
        self.heard_moves.clear()
        self._possible_starts = None
        self._current_positions = None
        self.belief_tracker.reset_uniform()

    def update_from_events(self, events: List[dict]) -> None:
        """
        Update Radio Operator state from game events.
        
        Processes:
        - Enemy moves (updates route tracking)
        - Silence actions (ambiguous movement)
        - Surface announcements (known sector)
        - Drone/sonar/explosion responses (sensor info)
        
        Args:
            events: List of event dictionaries from game loop
        """
        if not events:
            return
        
        # Extract enemy team (first non-own actor in events)
        enemy = None
        for event in events:
            actor = event.get("actor")
            if isinstance(actor, str) and actor != self.own_team:
                enemy = actor
                break
        
        if not enemy:
            return
        
        # Update route tracking and belief state
        for event in events:
            actor = event.get("actor")
            if actor != enemy:
                continue
            
            etype = event.get("type")
            
            if etype == "move":
                direction = event.get("direction")
                if isinstance(direction, str):
                    self.heard_moves.append(direction)
                    self._current_positions = None  # Invalidate cache
            
            elif etype == "silence":
                direction = event.get("direction")
                steps = event.get("steps", 1)
                if isinstance(direction, str):
                    for _ in range(steps):
                        self.heard_moves.append(f"SILENCE_{direction}")
                    self._current_positions = None
            
            elif etype == "surface":
                sector = event.get("sector")
                if isinstance(sector, int):
                    self.belief_tracker._apply_surface_sector(sector)
        
        # Update belief tracker with all events
        self.belief_tracker.update(events)

    def heard_move_sequence(self) -> List[str]:
        """
        Get the sequence of moves we've heard the enemy announce.
        
        Returns:
            List of direction strings (N, S, E, W, or SILENCE_*)
        """
        return self.heard_moves.copy()

    def heard_move_count(self) -> int:
        """Total number of moves heard (sum of single moves + silence steps)."""
        return len(self.heard_moves)

    def add_heard_move(self, direction: str) -> None:
        """
        Manually add a heard move (for testing or alternative inputs).
        
        Args:
            direction: Direction string (N, S, E, W, or SILENCE_*)
        """
        if isinstance(direction, str):
            self.heard_moves.append(direction)
            self._current_positions = None

    # =========================================================================
    # ROUTE TRACKING - Determine possible positions from heard moves
    # =========================================================================

    def possible_current_positions(self) -> Set[Tuple[int, int]]:
        """
        Calculate all possible current positions of enemy submarine.
        
        This uses the ROUTE TRACKING approach:
        1. Start with all valid map positions
        2. For each heard move, advance position and check constraints
        3. Return set of valid end positions
        
        Constraints:
        - Can't move off map
        - Can't move into islands
        - Can't cross own path (if known)
        
        Returns:
            Set of (x, y) positions where enemy could currently be
        """
        if self._current_positions is not None:
            return self._current_positions.copy()
        
        # Start: any valid position on map
        candidates: Set[Tuple[int, int]] = set()
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                if not self.map_data.is_blocked(x, y):
                    candidates.add((x, y))
        
        # Apply each heard move to filter/advance positions
        if not self.heard_moves:
            # No moves heard yet: could be anywhere
            self._current_positions = candidates
            return candidates.copy()
        
        # For each starting position, try to apply all heard moves
        valid_endings: Set[Tuple[int, int]] = set()
        
        for start_x, start_y in candidates:
            # Trace path from this starting position
            path = {(start_x, start_y)}
            x, y = start_x, start_y
            valid = True
            
            for move in self.heard_moves:
                dx, dy = 0, 0
                
                if move == "N":
                    dy = -1
                elif move == "S":
                    dy = 1
                elif move == "E":
                    dx = 1
                elif move == "W":
                    dx = -1
                elif move.startswith("SILENCE_"):
                    # Parse SILENCE_X as single step in direction X
                    dir_char = move.split("_")[1][0] if len(move.split("_")) > 1 else ""
                    if dir_char == "N":
                        dy = -1
                    elif dir_char == "S":
                        dy = 1
                    elif dir_char == "E":
                        dx = 1
                    elif dir_char == "W":
                        dx = -1
                    else:
                        valid = False
                        break
                else:
                    valid = False
                    break
                
                # Attempt move
                nx, ny = x + dx, y + dy
                
                # Check bounds
                if not self.map_data.in_bounds(nx, ny):
                    valid = False
                    break
                
                # Check island
                if self.map_data.is_blocked(nx, ny):
                    valid = False
                    break
                
                # Check crossing own path (conservative: assume no self-crossing)
                if (nx, ny) in path:
                    valid = False
                    break
                
                path.add((nx, ny))
                x, y = nx, ny
            
            if valid:
                valid_endings.add((x, y))
        
        self._current_positions = valid_endings if valid_endings else candidates
        return self._current_positions.copy()

    def possible_starting_positions(self) -> Set[Tuple[int, int]]:
        """
        Calculate all possible starting positions that lead to heard moves.
        
        Returns:
            Set of valid start positions before any heard moves
        """
        if self._possible_starts is not None:
            return self._possible_starts.copy()
        
        if not self.heard_moves:
            # No moves heard: could start anywhere
            self._possible_starts = {
                (x, y)
                for y in range(self.map_data.height)
                for x in range(self.map_data.width)
                if not self.map_data.is_blocked(x, y)
            }
            return self._possible_starts.copy()
        
        # Try each position as start, see if moves are valid
        valid_starts: Set[Tuple[int, int]] = set()
        
        for start_x in range(self.map_data.width):
            for start_y in range(self.map_data.height):
                if self.map_data.is_blocked(start_x, start_y):
                    continue
                
                # Trace from this start
                x, y = start_x, start_y
                path = {(x, y)}
                valid = True
                
                for move in self.heard_moves:
                    dx, dy = 0, 0
                    
                    if move == "N":
                        dy = -1
                    elif move == "S":
                        dy = 1
                    elif move == "E":
                        dx = 1
                    elif move == "W":
                        dx = -1
                    elif move.startswith("SILENCE_"):
                        dir_char = move.split("_")[1][0] if len(move.split("_")) > 1 else ""
                        if dir_char == "N":
                            dy = -1
                        elif dir_char == "S":
                            dy = 1
                        elif dir_char == "E":
                            dx = 1
                        elif dir_char == "W":
                            dx = -1
                        else:
                            valid = False
                            break
                    else:
                        valid = False
                        break
                    
                    nx, ny = x + dx, y + dy
                    
                    if not self.map_data.in_bounds(nx, ny):
                        valid = False
                        break
                    
                    if self.map_data.is_blocked(nx, ny):
                        valid = False
                        break
                    
                    if (nx, ny) in path:
                        valid = False
                        break
                    
                    path.add((nx, ny))
                    x, y = nx, ny
                
                if valid:
                    valid_starts.add((start_x, start_y))
        
        self._possible_starts = valid_starts if valid_starts else {
            (x, y)
            for y in range(self.map_data.height)
            for x in range(self.map_data.width)
            if not self.map_data.is_blocked(x, y)
        }
        return self._possible_starts.copy()

    def most_likely_position(self) -> Tuple[int, int] | None:
        """
        Get single best guess for enemy position.
        
        Combines:
        1. Route tracking (possible positions from heard moves)
        2. Belief state (sensor information)
        
        Returns:
            (x, y) of most likely position, or None
        """
        # Get position with highest probability from belief
        best_pos = self.belief_tracker.most_likely_cell()
        return best_pos

    def most_likely_sector(self) -> int | None:
        """
        Get single best guess for enemy sector.
        
        Returns:
            Sector number (1-indexed), or None
        """
        return self.belief_tracker.most_likely_sector()

    def position_probability_at(self, x: int, y: int) -> float:
        """
        Get probability of enemy at specific position.
        
        Args:
            x, y: Map coordinates
        
        Returns:
            Probability in range [0.0, 1.0]
        """
        return self.belief_tracker.probability_at(x, y)

    # =========================================================================
    # SECTOR INFORMATION
    # =========================================================================

    def sector_probability_masses(self) -> Dict[int, float]:
        """
        Get probability mass for each sector.
        
        Returns:
            Dict mapping sector number to total probability
        """
        return self.belief_tracker.sector_masses()

    def get_sector_for_position(self, x: int, y: int) -> int:
        """
        Get sector number for a map position.
        
        Args:
            x, y: Map coordinates
        
        Returns:
            Sector number (1-indexed)
        """
        row = min(SECTOR_ROWS - 1, (y * SECTOR_ROWS) // self.map_data.height)
        col = min(SECTOR_COLS - 1, (x * SECTOR_COLS) // self.map_data.width)
        return row * SECTOR_COLS + col + 1

    # =========================================================================
    # SENSOR INFORMATION INTEGRATION
    # =========================================================================

    def apply_drone_response(self, sector: int, response: bool) -> None:
        """
        Update belief based on drone query response.
        
        Args:
            sector: Queried sector (1-indexed)
            response: True if enemy in sector, False otherwise
        """
        self.belief_tracker._apply_drone(sector, response)

    def apply_sonar_response(self, true_info: dict, false_info: dict) -> None:
        """
        Update belief based on sonar response.
        
        Args:
            true_info: One piece of true information
            false_info: One piece of false information
        """
        self.belief_tracker._apply_sonar(true_info, false_info)

    def apply_surface_announcement(self, sector: int) -> None:
        """
        Update belief when enemy surfaces in a sector.
        
        Args:
            sector: Sector of surface announcement (1-indexed)
        """
        self.belief_tracker._apply_surface_sector(sector)

    def apply_torpedo_miss(self, x: int, y: int) -> None:
        """
        Update belief when a torpedo/mine explodes without hitting enemy.
        
        Args:
            x, y: Impact coordinates
        """
        self.belief_tracker._apply_torpedo_miss(x, y)

    # =========================================================================
    # DECISION SUPPORT
    # =========================================================================

    def suggest_drone_sector(self) -> int | None:
        """
        Suggest which sector to query with drone for best info gain.
        
        Returns:
            Sector number with highest probability mass
        """
        masses = self.belief_tracker.sector_masses()
        if not masses:
            return 1
        return max(masses, key=masses.get)

    def suggest_torpedo_targets(self, max_count: int = 5) -> List[Tuple[int, int]]:
        """
        Suggest best torpedo target positions (high enemy probability).
        
        Args:
            max_count: Maximum number of suggestions
        
        Returns:
            List of (x, y) positions sorted by probability (highest first)
        """
        candidates: List[Tuple[float, int, int]] = []
        
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                if self.map_data.is_blocked(x, y):
                    continue
                prob = self.belief_tracker.probability_at(x, y)
                if prob > 0.0:
                    candidates.append((prob, x, y))
        
        # Sort by probability descending
        candidates.sort(reverse=True)
        
        return [(x, y) for _, x, y in candidates[:max_count]]

    def has_position_fix(self) -> bool:
        """
        Check if we have high-confidence position fix.
        
        A fix is when possible positions from route tracking
        are significantly constrained.
        
        Returns:
            True if likely position narrowed down
        """
        possible = self.possible_current_positions()
        return len(possible) <= 4

    def get_confidence_estimate(self) -> float:
        """
        Estimate confidence in position knowledge (0.0 to 1.0).
        
        Based on:
        - How constrained possible positions are
        - How concentrated belief distribution is
        
        Returns:
            Confidence estimate
        """
        possible = self.possible_current_positions()
        if not possible:
            return 0.0
        
        # If very few positions possible, high confidence
        num_possible = len(possible)
        total_cells = sum(
            1 for y in range(self.map_data.height)
            for x in range(self.map_data.width)
            if not self.map_data.is_blocked(x, y)
        )
        
        if total_cells == 0:
            return 0.0
        
        route_constraint = 1.0 - (num_possible / total_cells)
        
        # Check belief distribution concentration (entropy-like)
        masses = self.belief_tracker.sector_masses()
        if masses:
            max_mass = max(masses.values())
            belief_concentration = max_mass / sum(masses.values()) if sum(masses.values()) > 0 else 0.0
        else:
            belief_concentration = 0.0
        
        # Average the two factors
        confidence = (route_constraint + belief_concentration) / 2.0
        return min(1.0, max(0.0, confidence))

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .actions import Action, ActionType, validate_action
from .config import (
    BREAKDOWN_DAMAGE_COMPLETE_AREA,
    BREAKDOWN_DAMAGE_RADIATION,
    DAMAGE_DIRECT,
    DAMAGE_INDIRECT,
    DIRECTIONS,
    GAUGE_MAX_DEFAULT,
    MAX_DAMAGE,
    MAX_SILENCE_STEPS,
    SECTOR_COLS,
    SECTOR_ROWS,
    SURFACE_SKIP_TURNS,
    SYSTEM_SYMBOLS_MAP,
    TORPEDO_RANGE,
)
from .engineer_layout import ENGINEER_BUTTON_SPECS, engineer_button_spec_by_id
from .map_loader import MapData
from .radio_operator import RadioOperator

# =============================================================================
# MODULE CONSTANTS
# =============================================================================

SYSTEMS = ("torpedo", "mine", "drone", "sonar", "silence", "scenario")

CIRCUIT_PARTS = ("top", "central", "down")
TOTAL_RADIOACTIVE_BUTTONS = sum(
    1
    for specs in ENGINEER_BUTTON_SPECS.values()
    for spec in specs
    if spec.function_type == "radioactive"
)

SYSTEM_ACTION = {
    ActionType.TORPEDO: "torpedo",
    ActionType.MINE: "mine",
    ActionType.DRONE: "drone",
    ActionType.SONAR: "sonar",
    ActionType.SILENCE: "silence",
    # TRIGGER_MINE is intentionally excluded: it bypasses gauge/breakdown/
    # last_action_system restrictions and may be used "at any time" per the rules.
}


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class SubmarineState:
    """Tracks position and health of a submarine."""
    x: int
    y: int
    damage: int = 0


@dataclass(frozen=True)
class MineState:
    """Immutable state of a deployed mine."""
    x: int
    y: int
    owner: str


@dataclass
class BreakdownState:
    """
    Tracks crossed engineer buttons by direction.

    Each crossed symbol is represented by its button_id and looked up via
    engineer_button_spec_by_id for function_type/circuit_part behavior.
    """
    crossed_by_direction: Dict[str, set[str]] = field(default_factory=lambda: {d: set() for d in DIRECTIONS})


# =============================================================================
# GAME STATE CLASS
# =============================================================================


@dataclass
class GameState:
    """
    Manages the complete state of a Captain Sonar game.
    
    Core responsibilities:
    - Track submarine positions and damage
    - Manage routes (no crossing own path)
    - Track deployed mines
    - Manage system gauges (4 spaces each)
    - Coordinate action resolution
    - Track breakdowns (Engineer role)
    - Manage game flow (turns, surfacing, game over)
    - Maintain Radio Operator tracking of enemy position
    """
    map_data: MapData
    subs: Dict[str, SubmarineState]
    
    # === Game State ===
    turn: int = 0
    game_over: bool = False
    winner: str | None = None
    
    # === Events ===
    events: List[dict] = field(default_factory=list)
    
    # === Map and Navigation ===
    routes: Dict[str, set[Tuple[int, int]]] = field(default_factory=dict)
    trajectory: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)
    mines: List[MineState] = field(default_factory=list)
    
    # === Systems (First Mate) ===
    gauges: Dict[str, Dict[str, int]] = field(default_factory=dict)
    last_action_system: Dict[str, bool] = field(default_factory=dict)
    
    # === Breakdowns (Engineer) ===
    breakdowns: Dict[str, BreakdownState] = field(default_factory=dict)
    
    # === Surface State ===
    skip_turns: Dict[str, int] = field(default_factory=dict)
    
    # === Radio Operator (Enemy Tracking) ===
    radio_operators: Dict[str, RadioOperator] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize game state to valid defaults."""
        self._init_routes()
        self._init_trajectory()
        self._init_gauges()
        self._init_radio_operators()
        self._init_system_flags()
        self._init_surface_state()
        self._init_breakdowns()

    # =========================================================================
    # PUBLIC API - MAIN GAME FLOW
    # =========================================================================

    def apply_actions(self, ordered_actions: List[Action]) -> None:
        """
        Process a batch of actions from all players.
        
        Flow:
        1. Validate action syntax and game state
        2. Resolve valid actions
        3. Update game state (damage, gauges, etc.)
        4. Update Radio Operators with new events
        5. Check for game over
        6. Increment turn
        """
        if self.game_over:
            return
        
        self.events.clear()

        # Process each action
        for action in ordered_actions:
            if self.skip_turns.get(action.actor, 0) > 0:
                self.events.append({
                    "type": "action_skipped",
                    "actor": action.actor,
                    "reason": "surfaced"
                })
                continue

            # Validate action
            errors = validate_action(action)
            errors.extend(self._validate_state(action))
            if errors:
                self.events.append({
                    "type": "action_rejected",
                    "action": action,
                    "errors": errors
                })
                continue

            # Resolve valid action
            self._resolve_action(action)

        self._check_game_over()
        self.turn += 1

    def system_ready(self, team: str, system: str) -> bool:
        """Check if a system's gauge is fully charged (ready to activate)."""
        return self.gauges.get(team, {}).get(system, 0) >= GAUGE_MAX_DEFAULT

    def get_radio_operator(self, team: str) -> RadioOperator | None:
        """
        Get the Radio Operator for a team (tracks enemy position).
        
        Args:
            team: Team identifier
        
        Returns:
            RadioOperator instance or None
        """
        return self.radio_operators.get(team)

    def snapshot(self, turn_id: int | None = None) -> dict[str, Any]:
        """
        Return a JSON-friendly snapshot of the full game state.

        The snapshot is intended for logging, replay, and agent consumption.
        """
        from .api import snapshot_game_state

        return snapshot_game_state(self, turn_id=turn_id)

    # =========================================================================
    # PRIVATE: INITIALIZATION
    # =========================================================================

    def _init_routes(self) -> None:
        """Initialize routes: each submarine starts at its position."""
        if not self.routes:
            self.routes = {
                team: {(sub.x, sub.y)}
                for team, sub in self.subs.items()
            }

    def _init_trajectory(self) -> None:
        """Initialize ordered trajectory lists from starting positions."""
        if not self.trajectory:
            self.trajectory = {
                team: [(sub.x, sub.y)]
                for team, sub in self.subs.items()
            }

    def _init_gauges(self) -> None:
        """Initialize all system gauges to 0 (uncharged)."""
        if not self.gauges:
            self.gauges = {
                team: {system: 0 for system in SYSTEMS}
                for team in self.subs.keys()
            }

    def _init_system_flags(self) -> None:
        """Initialize last_action_system tracking (prevents two systems in a row)."""
        if not self.last_action_system:
            self.last_action_system = {team: False for team in self.subs.keys()}

    def _init_radio_operators(self) -> None:
        """Initialize Radio Operator for each team (tracks enemy position)."""
        if not self.radio_operators:
            self.radio_operators = {
                team: RadioOperator(self.map_data, own_team=team)
                for team in self.subs.keys()
            }

    def _init_surface_state(self) -> None:
        """Initialize surface skip turns (0 = not surfaced)."""
        if not self.skip_turns:
            self.skip_turns = {team: 0 for team in self.subs.keys()}

    def _init_breakdowns(self) -> None:
        """Initialize engineer's breakdown tracking."""
        if not self.breakdowns:
            self.breakdowns = {
                team: BreakdownState()
                for team in self.subs.keys()
            }

    # =========================================================================
    # PRIVATE: GAUGE MANAGEMENT (First Mate Systems)
    # =========================================================================

    def _consume_gauge(self, team: str, system: str) -> None:
        """Reset gauge to 0 after system is activated."""
        if team in self.gauges and system in self.gauges[team]:
            self.gauges[team][system] = 0

    def _charge_gauge(self, team: str, system: str) -> None:
        """Increment gauge by 1 (up to max of GAUGE_MAX_DEFAULT)."""
        if team not in self.gauges or system not in self.gauges[team]:
            return
        self.gauges[team][system] = min(
            GAUGE_MAX_DEFAULT,
            self.gauges[team][system] + 1
        )

    # =========================================================================
    # PRIVATE: VALIDATION
    # =========================================================================

    def _validate_state(self, action: Action) -> List[str]:
        """
        Validate action against current game state.
        
        Checks:
        - Actor exists
        - System is ready (gauge charged)
        - Can't activate two systems in a row
        - Targets are in bounds
        - Special constraints per action type
        """
        errors: List[str] = []
        sub = self.subs.get(action.actor)
        
        if not sub:
            errors.append("unknown actor")
            return errors
        
        # === System Activation Rules ===
        if action.type in SYSTEM_ACTION:
            system = SYSTEM_ACTION[action.type]

            # Must be ready (except triggering mines, which don't need gauge)
            if action.type != ActionType.TRIGGER_MINE:
                if not self.system_ready(action.actor, system):
                    errors.append(f"{system} system not ready")

            # Must not be broken by engineer breakdowns.
            # Triggering a mine is allowed even if the mine system is broken.
            if action.type != ActionType.TRIGGER_MINE:
                if self._system_has_breakdown(action.actor, system):
                    errors.append(f"{system} system has breakdown")

            # Can't activate two systems in a row
            if self.last_action_system.get(action.actor, False):
                errors.append("cannot activate two systems in a row")
        
        # === Target Bounds Checking ===
        if action.type in (ActionType.TORPEDO, ActionType.MINE, ActionType.TRIGGER_MINE, ActionType.SONAR):
            target = action.payload.get("target")
            if isinstance(target, dict):
                tx, ty = target.get("x"), target.get("y")
                if isinstance(tx, int) and isinstance(ty, int):
                    if not self.map_data.in_bounds(tx, ty):
                        errors.append("target out of bounds")
        
        # === Drone Sector Validation ===
        if action.type == ActionType.DRONE:
            sector = action.payload.get("sector")
            if isinstance(sector, int):
                max_sector = SECTOR_ROWS * SECTOR_COLS
                if sector < 1 or sector > max_sector:
                    errors.append("sector out of bounds")
        
        # === Silence Steps Validation ===
        if action.type == ActionType.SILENCE:
            steps = action.payload.get("steps")
            if not isinstance(steps, int):
                errors.append("SILENCE steps must be integer")
            elif steps < 1 or steps > MAX_SILENCE_STEPS:
                errors.append(f"SILENCE steps must be 1-{MAX_SILENCE_STEPS}")
        
        return errors

    # =========================================================================
    # PRIVATE: ACTION RESOLUTION
    # =========================================================================

    def _resolve_action(self, action: Action) -> None:
        """Dispatch action to appropriate resolver method."""
        if action.type == ActionType.MOVE:
            self._resolve_move(action)
        elif action.type == ActionType.SILENCE:
            self._resolve_silence(action)
        elif action.type == ActionType.TORPEDO:
            self._resolve_torpedo(action)
        elif action.type == ActionType.MINE:
            self._resolve_mine(action)
        elif action.type == ActionType.TRIGGER_MINE:
            self._resolve_trigger_mine(action)
        elif action.type == ActionType.DRONE:
            self._resolve_drone(action)
        elif action.type == ActionType.SONAR:
            self._resolve_sonar(action)
        elif action.type == ActionType.REPAIR:
            self._resolve_repair(action)
        elif action.type == ActionType.SURFACE:
            self._resolve_surface(action.actor, forced=False)
        else:
            self.events.append({"type": "action_noop", "action": action})

    # === MOVEMENT ===

    def _resolve_move(self, action: Action) -> None:
        """
        Captain announces course (N/S/E/W).
        1. Move submarine one space
        2. Add position to route
        3. Apply engineer breakdown (random symbol in direction)
        4. Charge gauge (player chooses which)
        5. Set last_action_system to False (can activate system next)
        """
        sub = self.subs.get(action.actor)
        if not sub:
            return
        
        direction = action.payload.get("direction")
        if not isinstance(direction, str):
            direction = None
        dx, dy = 0, 0
        
        if direction == "N":
            dy = -1
        elif direction == "S":
            dy = 1
        elif direction == "E":
            dx = 1
        elif direction == "W":
            dx = -1
        
        nx, ny = sub.x + dx, sub.y + dy
        
        # Blocked move: only surface if it is a true blackout (no valid direction
        # remains); otherwise reject so the player can pick another direction.
        if self._route_blocked(action.actor, nx, ny):
            if self._is_blackout(action.actor):
                self._resolve_surface(action.actor, forced=True)
            else:
                self.events.append({
                    "type": "action_rejected",
                    "action": action,
                    "errors": ["move blocked"],
                })
            return
        
        # Move submarine
        sub.x, sub.y = nx, ny
        self.routes[action.actor].add((nx, ny))
        self.trajectory[action.actor].append((nx, ny))
        
        # Engineer crosses out a breakdown symbol for the announced direction.
        breakdown_choice = action.payload.get("breakdown_choice")
        if direction is not None:
            self._apply_breakdown(action.actor, direction, breakdown_choice)
        
        # Charge gauge (player selects which system)
        charge = action.payload.get("charge", "torpedo")
        self._charge_gauge(action.actor, charge)
        
        # Can activate system next (not system last turn)
        self.last_action_system[action.actor] = False
        
        self.events.append({
            "type": "move",
            "actor": action.actor,
            "direction": direction,
            "to": (nx, ny),
            "charge": charge
        })

    # === SILENCE (Stealth Movement) ===

    def _resolve_silence(self, action: Action) -> None:
        """
        Captain uses silence system: move 1-4 spaces without announcing.
        1. Move submarine multiple spaces in one direction
        2. Add each position to route
        3. Apply engineer breakdown for direction
        4. Consume gauge
        5. Set last_action_system to True (system action)
        """
        sub = self.subs.get(action.actor)
        if not sub:
            return
        
        direction = action.payload.get("direction")
        if not isinstance(direction, str):
            direction = None
        steps = action.payload.get("steps", 1)
        dx, dy = 0, 0
        
        if direction == "N":
            dy = -1
        elif direction == "S":
            dy = 1
        elif direction == "E":
            dx = 1
        elif direction == "W":
            dx = -1
        
        moved = 0
        for _ in range(int(steps)):
            nx, ny = sub.x + dx, sub.y + dy
            if self._route_blocked(action.actor, nx, ny):
                break
            sub.x, sub.y = nx, ny
            self.routes[action.actor].add((nx, ny))
            self.trajectory[action.actor].append((nx, ny))
            moved += 1

        if moved == 0:
            self.events.append({
                "type": "action_failed",
                "reason": "silence path fully blocked",
                "action": action,
            })
            return

        # Silence also creates a breakdown tied to the announced direction.
        breakdown_choice = action.payload.get("breakdown_choice")
        if direction is not None:
            self._apply_breakdown(action.actor, direction, breakdown_choice)
        
        # Consume silence gauge
        self._consume_gauge(action.actor, "silence")
        
        # Charge another gauge
        charge = action.payload.get("charge", "torpedo")
        self._charge_gauge(action.actor, charge)
        
        # System was activated
        self.last_action_system[action.actor] = True
        
        self.events.append({
            "type": "silence",
            "actor": action.actor,
            "direction": direction,
            "steps": moved,
            "to": (sub.x, sub.y),
            "charge": charge,
        })

    # === WEAPONS ===

    def _resolve_torpedo(self, action: Action) -> None:
        """
        Captain launches torpedo.
        1. Check target is 1-4 spaces away (orthogonal)
        2. Apply explosion at target
        3. Consume gauge
        4. Set last_action_system to True
        """
        sub = self.subs.get(action.actor)
        if not sub:
            return
        
        target = action.payload.get("target", {})
        tx, ty = target.get("x"), target.get("y")
        
        if not isinstance(tx, int) or not isinstance(ty, int):
            return
        
        # Must be orthogonal (same row or column)
        if not (sub.x == tx or sub.y == ty):
            self.events.append({
                "type": "action_failed",
                "reason": "torpedo not orthogonal",
                "action": action
            })
            return
        
        distance = abs(sub.x - tx) + abs(sub.y - ty)
        
        # Must be 1-4 spaces away
        if distance < 1 or distance > TORPEDO_RANGE:
            self.events.append({
                "type": "action_failed",
                "reason": "torpedo out of range",
                "action": action
            })
            return
        
        self._consume_gauge(action.actor, "torpedo")
        self.last_action_system[action.actor] = True
        self._apply_explosion((tx, ty), source="torpedo", owner=action.actor)

    def _resolve_mine(self, action: Action) -> None:
        """
        Captain drops a mine adjacent to submarine.
        1. Check target is adjacent (1 space away)
        2. Check not blocked or occupied
        3. Add mine to list
        4. Consume gauge
        5. Set last_action_system to True
        """
        sub = self.subs.get(action.actor)
        if not sub:
            return
        
        target = action.payload.get("target")
        if not isinstance(target, dict):
            return
        
        tx, ty = target.get("x"), target.get("y")
        if not isinstance(tx, int) or not isinstance(ty, int):
            return
        
        # Must be adjacent (distance = 1)
        if abs(sub.x - tx) + abs(sub.y - ty) != 1:
            self.events.append({
                "type": "action_failed",
                "reason": "mine must be adjacent",
                "action": action
            })
            return
        
        # Space must be in bounds and not an island
        if not self.map_data.in_bounds(tx, ty) or self.map_data.is_blocked(tx, ty):
            self.events.append({
                "type": "action_failed",
                "reason": "mine blocked",
                "action": action
            })
            return

        # Cannot drop a mine on own route
        if (tx, ty) in self.routes.get(action.actor, set()):
            self.events.append({
                "type": "action_failed",
                "reason": "mine cannot be placed on own route",
                "action": action,
            })
            return

        # No mine already there
        if any(mine.x == tx and mine.y == ty for mine in self.mines):
            self.events.append({
                "type": "action_failed",
                "reason": "mine exists",
                "action": action
            })
            return
        
        # Deploy mine
        self.mines.append(MineState(x=tx, y=ty, owner=action.actor))
        self._consume_gauge(action.actor, "mine")
        self.last_action_system[action.actor] = True
        
        self.events.append({
            "type": "mine_dropped",
            "actor": action.actor,
            "target": (tx, ty)
        })

    def _resolve_trigger_mine(self, action: Action) -> None:
        """
        Captain triggers a previously deployed mine.
        1. Find mine at target location
        2. Remove mine from list
        3. Apply explosion
        4. Set last_action_system to True
        
        Note: Mine gauge doesn't need to be charged to trigger
        """
        target = action.payload.get("target")
        if not isinstance(target, dict):
            return
        
        tx, ty = target.get("x"), target.get("y")
        if not isinstance(tx, int) or not isinstance(ty, int):
            return
        
        # Find owned mine at this location
        mine_index = next(
            (idx for idx, mine in enumerate(self.mines)
             if mine.x == tx and mine.y == ty and mine.owner == action.actor),
            None,
        )
        
        if mine_index is None:
            self.events.append({
                "type": "action_failed",
                "reason": "no owned mine",
                "action": action
            })
            return
        
        # Detonate mine. Triggering does not count as a "system" activation —
        # it can happen at any time and does not block a subsequent system use.
        self.mines.pop(mine_index)
        self.last_action_system[action.actor] = False
        self._apply_explosion((tx, ty), source="mine", owner=action.actor)

    # === DETECTION ===

    def _resolve_drone(self, action: Action) -> None:
        """
        First Mate or Captain activates drone.
        1. Get enemy submarine's sector
        2. Compare with queried sector
        3. Return YES/NO
        4. Consume gauge
        5. Set last_action_system to True
        
        Map divided into sectors (2x2 in turn-by-turn mode)
        """
        enemy = self._enemy_of(action.actor)
        if not enemy:
            return
        
        enemy_sub = self.subs.get(enemy)
        if not enemy_sub:
            return
        
        sector_val = action.payload.get("sector")
        if not isinstance(sector_val, int):
            return
        
        enemy_sector = self._sector_for(enemy_sub.x, enemy_sub.y)
        response = sector_val == enemy_sector
        
        self._consume_gauge(action.actor, "drone")
        self.last_action_system[action.actor] = True
        
        self.events.append({
            "type": "drone",
            "actor": action.actor,
            "sector": sector_val,
            "response": response,
            "enemy_sector": enemy_sector
        })

    def _resolve_sonar(self, action: Action) -> None:
        """
        First Mate or Captain activates sonar.
        1. Get enemy submarine's actual position (row, col, sector)
        2. Generate one true piece of info
        3. Generate one false piece of different type
        4. Return both (mixed)
        5. Consume gauge
        6. Set last_action_system to True
        
        Sonar reveals one true + one false piece of different type info.
        """
        enemy = self._enemy_of(action.actor)
        if not enemy:
            return
        
        enemy_sub = self.subs.get(enemy)
        if not enemy_sub:
            return
        
        # True information
        true_row = self._row_label(enemy_sub.y)
        true_col = enemy_sub.x + 1
        true_sector = self._sector_for(enemy_sub.x, enemy_sub.y)
        
        # False information (rotated)
        false_row = self._row_label((enemy_sub.y + 1) % self.map_data.height)
        false_col = ((enemy_sub.x + 1) % self.map_data.width) + 1
        false_sector = (true_sector % (SECTOR_ROWS * SECTOR_COLS)) + 1
        
        pieces = [
            ("row", true_row, False),
            ("col", true_col, False),
            ("sector", true_sector, False),
        ]
        
        false_pieces = [
            ("row", false_row, True),
            ("col", false_col, True),
            ("sector", false_sector, True),
        ]
        
        # Alternate which true piece is revealed
        index = self.turn % 3
        true_piece = pieces[index]
        false_piece = next(
            item for item in false_pieces
            if item[0] != true_piece[0]
        )
        
        self._consume_gauge(action.actor, "sonar")
        self.last_action_system[action.actor] = True
        
        self.events.append({
            "type": "sonar",
            "actor": action.actor,
            "true_info": {
                "type": true_piece[0],
                "value": true_piece[1]
            },
            "false_info": {
                "type": false_piece[0],
                "value": false_piece[1]
            },
        })

    # === REPAIR (ENGINEER) ===

    def _resolve_repair(self, action: Action) -> None:
        """
        Engineer repairs submarine damage.
        1. Reduce damage by 1
        2. Set last_action_system to False (repair is not a system)
        
        Note: Full breakdown repair is only via surfacing (Phase 2)
        """
        sub = self.subs.get(action.actor)
        if not sub:
            return
        
        sub.damage = max(0, sub.damage - 1)
        self.last_action_system[action.actor] = False
        
        self.events.append({
            "type": "repair",
            "actor": action.actor,
            "damage": sub.damage
        })

    # === SURFACE ===

    def _resolve_surface(self, actor: str, forced: bool) -> None:
        """
        Submarine surfaces to repair.
        1. Set skip_turns = 3 (enemy gets 3 free turns)
        2. Clear route (reset to current position)
        3. Clear all breakdowns (TODO: Phase 2)
        4. Set last_action_system to False
        5. Log sector announcement
        
        Forced surface: blocked by route/island/mine
        Voluntary surface: captain chooses to surface
        """
        sub = self.subs.get(actor)
        if not sub:
            return
        
        self.skip_turns[actor] = SURFACE_SKIP_TURNS
        self.routes[actor] = {(sub.x, sub.y)}
        self.trajectory[actor] = [(sub.x, sub.y)]
        self.last_action_system[actor] = False
        
        self._clear_all_breakdowns(actor)
        
        sector = self._sector_for(sub.x, sub.y)
        self.events.append({
            "type": "surface",
            "actor": actor,
            "sector": sector,
            "forced": forced
        })

    # =========================================================================
    # PRIVATE: BREAKDOWN MANAGEMENT (ENGINEER ROLE - Phase 2)
    # =========================================================================

    def _apply_breakdown(self, team: str, direction: str, choice: dict | None = None) -> None:
        """
        Engineer crosses out a symbol for the announced direction.

        Priority:
        1. If engineer selected a button, use that exact button_id
        2. If no explicit choice was provided, auto-select the next available symbol
        """
        breakdown = self.breakdowns.get(team)
        if not breakdown:
            return

        if direction not in breakdown.crossed_by_direction:
            return

        crossed = breakdown.crossed_by_direction[direction]
        selected_spec = None
        explicit_choice_used = False

        # 1) Engineer explicit choice by button_id, but only if it belongs to the announced direction.
        if isinstance(choice, dict):
            choice_button_id = choice.get("button_id")
            choice_spec = engineer_button_spec_by_id(choice_button_id) if isinstance(choice_button_id, str) else None
            if choice_spec is not None and choice_spec.direction == direction:
                explicit_choice_used = True
                if choice_spec.button_id in crossed:
                    return
                selected_spec = choice_spec

        # 2) Fallback only when no explicit choice was provided.
        if selected_spec is None and not explicit_choice_used:
            for spec in ENGINEER_BUTTON_SPECS.get(direction, []):
                if spec.button_id not in crossed:
                    selected_spec = spec
                    break

        if selected_spec is None:
            return

        crossed.add(selected_spec.button_id)

        self.events.append({
            "type": "breakdown",
            "actor": team,
            "direction": direction,
            "button_id": selected_spec.button_id,
            "circuit_part": selected_spec.circuit_part,
            "function_type": selected_spec.function_type,
        })
        self._check_breakdown_effects(team)

    def _check_breakdown_effects(self, team: str) -> None:
        """
        Check effects after breakdown is applied:
        1. Complete area breakdown? -> damage + clear all
        2. Radiation damage? -> damage + clear all
        3. Circuit self-repair? -> clear circuit
        """
        breakdown = self.breakdowns.get(team)
        sub = self.subs.get(team)
        if not breakdown or not sub:
            return

        if self._is_complete_area_breakdown(team):
            sub.damage = min(MAX_DAMAGE, sub.damage + BREAKDOWN_DAMAGE_COMPLETE_AREA)
            self.events.append({
                "type": "complete_area_breakdown",
                "actor": team,
                "damage": BREAKDOWN_DAMAGE_COMPLETE_AREA,
            })
            self._clear_all_breakdowns(team)
            return

        if self._count_radioactive_breakdowns(team) >= TOTAL_RADIOACTIVE_BUTTONS:
            sub.damage = min(MAX_DAMAGE, sub.damage + BREAKDOWN_DAMAGE_RADIATION)
            self.events.append({
                "type": "radiation_damage",
                "actor": team,
                "damage": BREAKDOWN_DAMAGE_RADIATION,
            })
            self._clear_all_breakdowns(team)
            return

        repaired = self._repair_circuits(team)
        if repaired:
            self.events.append({
                "type": "circuit_self_repair",
                "actor": team,
                "circuits": repaired,
            })

    def _clear_all_breakdowns(self, team: str) -> None:
        """Clear all breakdown symbols (via complete area or surfacing)."""
        if team in self.breakdowns:
            self.breakdowns[team] = BreakdownState()

    def _system_has_breakdown(self, team: str, system: str) -> bool:
        """Check if any symbol of a system is crossed out."""
        breakdown = self.breakdowns.get(team)
        if not breakdown:
            return False

        color = SYSTEM_SYMBOLS_MAP.get(system)
        if color is None:
            return False

        for crossed in breakdown.crossed_by_direction.values():
            for button_id in crossed:
                spec = engineer_button_spec_by_id(button_id)
                if spec and spec.function_type == color:
                    return True
        return False

    def _is_complete_area_breakdown(self, team: str) -> bool:
        breakdown = self.breakdowns.get(team)
        if not breakdown:
            return False
        for direction, specs in ENGINEER_BUTTON_SPECS.items():
            if len(breakdown.crossed_by_direction.get(direction, set())) >= len(specs):
                return True
        return False

    def _count_radioactive_breakdowns(self, team: str) -> int:
        breakdown = self.breakdowns.get(team)
        if not breakdown:
            return 0

        count = 0
        for crossed in breakdown.crossed_by_direction.values():
            for button_id in crossed:
                spec = engineer_button_spec_by_id(button_id)
                if spec and spec.function_type == "radioactive":
                    count += 1
        return count

    def _repair_circuits(self, team: str) -> List[str]:
        breakdown = self.breakdowns.get(team)
        if not breakdown:
            return []

        repaired: List[str] = []
        for circuit_part in CIRCUIT_PARTS:
            circuit_name = f"{circuit_part}_circuit"

            part_button_ids = {
                spec.button_id
                for specs in ENGINEER_BUTTON_SPECS.values()
                for spec in specs
                if spec.circuit_part == circuit_part
            }
            if not part_button_ids:
                continue

            crossed_ids = set().union(*breakdown.crossed_by_direction.values())
            if part_button_ids.issubset(crossed_ids):
                for crossed in breakdown.crossed_by_direction.values():
                    crossed.difference_update(part_button_ids)
                repaired.append(circuit_name)

        return repaired

    # =========================================================================
    # PRIVATE: HELPER METHODS
    # =========================================================================

    def _route_blocked(self, actor: str, x: int, y: int) -> bool:
        """
        Check if a position is blocked (can't move there).
        
        Blocked if:
        - Out of bounds
        - Island
        - Own route already passes through
        - Own mine at location
        """
        if not self.map_data.in_bounds(x, y):
            return True
        if self.map_data.is_blocked(x, y):
            return True
        if (x, y) in self.routes.get(actor, set()):
            return True
        if any(mine.owner == actor and mine.x == x and mine.y == y
               for mine in self.mines):
            return True
        return False

    def _is_blackout(self, actor: str) -> bool:
        """True only when every orthogonal neighbour is blocked (true blackout)."""
        sub = self.subs.get(actor)
        if not sub:
            return False
        for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
            if not self._route_blocked(actor, sub.x + dx, sub.y + dy):
                return False
        return True

    def _apply_explosion(self, impact: Tuple[int, int], source: str, owner: str) -> None:
        """
        Apply explosion at impact location.
        1. Remove any mines at location
        2. Calculate damage to all submarines based on distance
        3. Direct hit (0 distance) = 2 damage
        4. Indirect hit (1 distance) = 1 damage
        5. Log all hits
        
        Special: Torpedo can damage the sub that fired it!
        """
        ix, iy = impact
        
        # Remove mines at impact location
        removed = [
            mine for mine in self.mines
            if mine.x == ix and mine.y == iy
        ]
        if removed:
            self.mines = [
                mine for mine in self.mines
                if not (mine.x == ix and mine.y == iy)
            ]
        
        # Calculate damage to all submarines
        hits = []
        for team, sub in self.subs.items():
            distance = abs(sub.x - ix) + abs(sub.y - iy)
            damage = 0
            
            if distance == 0:
                damage = DAMAGE_DIRECT
            elif distance == 1:
                damage = DAMAGE_INDIRECT
            
            if damage > 0:
                sub.damage = min(MAX_DAMAGE, sub.damage + damage)
                hits.append({"team": team, "damage": damage})
        
        self.events.append({
            "type": "explosion",
            "source": source,
            "owner": owner,
            "impact": impact,
            "hits": hits,
            "mine_removed": bool(removed),
        })

    def _enemy_of(self, team: str) -> str | None:
        """Get the enemy team (the other submarine)."""
        return next(
            (name for name in self.subs.keys() if name != team),
            None
        )

    def _sector_for(self, x: int, y: int) -> int:
        """Calculate which sector a position is in (1-4 for 2x2 grid)."""
        row = min(
            SECTOR_ROWS - 1,
            (y * SECTOR_ROWS) // self.map_data.height
        )
        col = min(
            SECTOR_COLS - 1,
            (x * SECTOR_COLS) // self.map_data.width
        )
        return row * SECTOR_COLS + col + 1

    def _row_label(self, y: int) -> str:
        """Convert y coordinate to row letter (A, B, C, ...)."""
        return chr(ord("A") + y)

    def _update_radio_operators(self) -> None:
        """
        Update each team's Radio Operator with events.
        
        This allows the Radio Operator to track:
        - Enemy moves and position updates
        - Sensor information (drone, sonar, surface announcements)
        - Constraint satisfaction (route tracking)
        """
        for team, radio_op in self.radio_operators.items():
            if radio_op is not None:
                radio_op.update_from_events(self.events)

    def _check_game_over(self) -> None:
        """Check if any submarine is destroyed (4 damage)."""
        destroyed = [
            team for team, sub in self.subs.items()
            if sub.damage >= MAX_DAMAGE
        ]
        
        if not destroyed:
            return
        
        alive = [
            team for team, sub in self.subs.items()
            if sub.damage < MAX_DAMAGE
        ]
        
        self.game_over = True
        self.winner = alive[0] if len(alive) == 1 else None
        
        self.events.append({
            "type": "game_over",
            "winner": self.winner,
            "destroyed": destroyed
        })


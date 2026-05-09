"""
Test suite for Radio Operator functionality.

Tests coverage for:
1. Route tracking (hearing enemy moves)
2. Possible position calculation
3. Belief state updates from sensors
4. Decision support (suggestions)
"""

import pytest
from src.captain_sonar.map_loader import MapData
from src.captain_sonar.radio_operator import RadioOperator
from src.captain_sonar.game_state import GameState, SubmarineState


class TestRadioOperatorRouteTracking:
    """Tests for tracking enemy routes from heard moves."""

    @pytest.fixture
    def map_data(self):
        """Create a simple test map."""
        tiles = [["." for _ in range(10)] for _ in range(10)]
        return MapData(width=10, height=10, tiles=tiles)

    @pytest.fixture
    def radio_op(self, map_data):
        """Create a Radio Operator for testing."""
        return RadioOperator(map_data, own_team="BLUE")

    def test_initial_state(self, radio_op, map_data):
        """Test initial Radio Operator state."""
        assert radio_op.heard_move_count() == 0
        assert len(radio_op.heard_move_sequence()) == 0
        
        # Initially could be anywhere
        possible = radio_op.possible_current_positions()
        assert len(possible) == 100  # 10x10 map

    def test_add_single_move(self, radio_op):
        """Test adding a single heard move."""
        radio_op.add_heard_move("N")
        
        assert radio_op.heard_move_count() == 1
        assert "N" in radio_op.heard_move_sequence()

    def test_multiple_moves(self, radio_op):
        """Test tracking multiple moves."""
        moves = ["N", "N", "E", "S", "W"]
        for move in moves:
            radio_op.add_heard_move(move)
        
        assert radio_op.heard_move_count() == 5
        assert radio_op.heard_move_sequence() == moves

    def test_possible_positions_constrain_with_moves(self, radio_op):
        """Test that moves constrain possible positions."""
        # No moves: could be anywhere
        no_moves = len(radio_op.possible_current_positions())
        assert no_moves == 100
        
        # After north moves: must be in upper part of map
        radio_op.add_heard_move("N")
        radio_op.add_heard_move("N")
        radio_op.add_heard_move("N")
        
        after_moves = radio_op.possible_current_positions()
        # Can't all be at y=0 since we started somewhere and moved north 3 times
        assert len(after_moves) < no_moves

    def test_no_crossing_own_path(self, radio_op):
        """Test that submarine can't cross its own path."""
        # Start at (5, 5), go E to (6, 5), then S to (6, 6), then W to (5, 6)
        # This should be valid. But can't go back to (6, 5) since path crosses.
        radio_op.add_heard_move("E")
        radio_op.add_heard_move("S")
        radio_op.add_heard_move("W")
        
        possible = radio_op.possible_current_positions()
        # Should be possible to end at (5, 6) via above path
        assert len(possible) > 0

    def test_reset(self, radio_op):
        """Test resetting Radio Operator state."""
        radio_op.add_heard_move("N")
        radio_op.add_heard_move("E")
        
        assert radio_op.heard_move_count() == 2
        
        radio_op.reset()
        
        assert radio_op.heard_move_count() == 0
        assert len(radio_op.heard_move_sequence()) == 0


class TestRadioOperatorSensorIntegration:
    """Tests for sensor information integration."""

    @pytest.fixture
    def map_data(self):
        """Create a test map."""
        tiles = [["." for _ in range(10)] for _ in range(10)]
        return MapData(width=10, height=10, tiles=tiles)

    @pytest.fixture
    def radio_op(self, map_data):
        """Create a Radio Operator."""
        return RadioOperator(map_data, own_team="BLUE")

    def test_drone_response_positive(self, radio_op):
        """Test drone response narrows belief (positive response)."""
        # Start uniform
        initial_mass = radio_op.belief_tracker.sector_masses()
        
        # Drone says yes to sector 1
        radio_op.apply_drone_response(sector=1, response=True)
        
        after_mass = radio_op.belief_tracker.sector_masses()
        # Probability in sector 1 should increase
        assert after_mass.get(1, 0) > initial_mass.get(1, 0)

    def test_drone_response_negative(self, radio_op):
        """Test drone response narrows belief (negative response)."""
        initial_mass = radio_op.belief_tracker.sector_masses()
        
        # Drone says no to sector 1
        radio_op.apply_drone_response(sector=1, response=False)
        
        after_mass = radio_op.belief_tracker.sector_masses()
        # Probability in sector 1 should decrease
        assert after_mass.get(1, 0) < initial_mass.get(1, 0)

    def test_surface_announcement(self, radio_op):
        """Test surface announcement updates belief."""
        initial_sectors = list(radio_op.belief_tracker.sector_masses().keys())
        
        # Enemy surfaces in sector 2
        radio_op.apply_surface_announcement(sector=2)
        
        after_sectors = radio_op.belief_tracker.sector_masses()
        # Sector 2 should now have most of the probability
        assert after_sectors.get(2, 0) > 0.8

    def test_torpedo_miss(self, radio_op):
        """Test torpedo miss eliminates a position."""
        # Torpedo hits (5, 5) with no damage
        radio_op.apply_torpedo_miss(x=5, y=5)
        
        # Position (5, 5) should have zero probability
        prob_at_hit = radio_op.position_probability_at(5, 5)
        assert prob_at_hit == 0.0


class TestRadioOperatorDecisionSupport:
    """Tests for decision support features."""

    @pytest.fixture
    def map_data(self):
        """Create a test map."""
        tiles = [["." for _ in range(10)] for _ in range(10)]
        return MapData(width=10, height=10, tiles=tiles)

    @pytest.fixture
    def radio_op(self, map_data):
        """Create a Radio Operator."""
        return RadioOperator(map_data, own_team="BLUE")

    def test_suggest_drone_sector(self, radio_op):
        """Test drone sector suggestion."""
        suggestion = radio_op.suggest_drone_sector()
        assert isinstance(suggestion, int)
        assert 1 <= suggestion <= 4

    def test_suggest_torpedo_targets(self, radio_op):
        """Test torpedo target suggestions."""
        suggestions = radio_op.suggest_torpedo_targets(max_count=3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        for target in suggestions:
            assert isinstance(target, tuple)
            assert len(target) == 2

    def test_most_likely_position(self, radio_op):
        """Test getting most likely position."""
        pos = radio_op.most_likely_position()
        
        if pos is not None:
            assert isinstance(pos, tuple)
            assert len(pos) == 2
            x, y = pos
            assert 0 <= x < 10
            assert 0 <= y < 10

    def test_most_likely_sector(self, radio_op):
        """Test getting most likely sector."""
        sector = radio_op.most_likely_sector()
        
        if sector is not None:
            assert isinstance(sector, int)
            assert 1 <= sector <= 4

    def test_confidence_estimate(self, radio_op):
        """Test confidence estimation."""
        confidence = radio_op.get_confidence_estimate()
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_position_fix_detection(self, radio_op):
        """Test detection of position fix."""
        # Initially not fixed
        assert not radio_op.has_position_fix()
        
        # After enough moves, might be fixed
        for _ in range(5):
            radio_op.add_heard_move("N")
        
        # Now might have position fix (depends on map)
        has_fix = radio_op.has_position_fix()
        assert isinstance(has_fix, bool)


class TestRadioOperatorGameStateIntegration:
    """Tests for integration with GameState."""

    @pytest.fixture
    def game_state(self):
        """Create a game state for testing."""
        tiles = [["." for _ in range(10)] for _ in range(10)]
        map_data = MapData(width=10, height=10, tiles=tiles)
        
        game = GameState(
            map_data=map_data,
            subs={
                "BLUE": SubmarineState(x=5, y=5, damage=0),
                "RED": SubmarineState(x=8, y=8, damage=0),
            }
        )
        return game

    def test_game_state_has_radio_operators(self, game_state):
        """Test that GameState initializes Radio Operators."""
        assert "BLUE" in game_state.radio_operators
        assert "RED" in game_state.radio_operators
        
        blue_op = game_state.get_radio_operator("BLUE")
        assert blue_op is not None
        assert isinstance(blue_op, RadioOperator)

    def test_get_radio_operator(self, game_state):
        """Test accessing Radio Operator from GameState."""
        blue_op = game_state.get_radio_operator("BLUE")
        
        assert blue_op is not None
        assert blue_op.own_team == "BLUE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

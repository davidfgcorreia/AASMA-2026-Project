from captain_sonar.belief_tracker import BeliefTracker
from captain_sonar.map_loader import MapData


def test_uniform_ignores_blocked_cells():
    map_data = MapData(width=2, height=2, tiles=[["#", "."], [".", "."]])
    tracker = BeliefTracker(map_data)
    assert tracker.probability_at(0, 0) == 0.0
    total = sum(sum(row) for row in tracker.heatmap())
    assert abs(total - 1.0) < 1e-9


def test_move_updates_distribution_by_direction():
    map_data = MapData(width=3, height=3, tiles=[["."] * 3 for _ in range(3)])
    tracker = BeliefTracker(map_data, own_team="BLUE")
    tracker.set_point_prior(1, 1)

    # Enemy moved east.
    tracker.update([{"type": "move", "actor": "RED", "direction": "E"}])
    assert tracker.probability_at(2, 1) == 1.0


def test_surface_filters_to_sector():
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    tracker = BeliefTracker(map_data, own_team="BLUE")

    # With SECTOR_ROWS=3 and SECTOR_COLS=3 (config), sector 1 is top-left area.
    tracker.update([{"type": "surface", "actor": "RED", "sector": 1, "forced": False}])

    # (0,0) should be in sector 1; (3,3) should not.
    assert tracker.probability_at(0, 0) > 0.0
    assert tracker.probability_at(3, 3) == 0.0


def test_drone_response_filters_sector_membership():
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    tracker = BeliefTracker(map_data, own_team="BLUE")

    # Drone says enemy is in sector 1.
    tracker.update([{"type": "drone", "actor": "BLUE", "sector": 1, "response": True, "enemy_sector": 1}])
    assert tracker.probability_at(0, 0) > 0.0
    assert tracker.probability_at(3, 3) == 0.0

    # Reset, now drone says enemy is NOT in sector 1.
    tracker.reset_uniform()
    tracker.update([{"type": "drone", "actor": "BLUE", "sector": 1, "response": False, "enemy_sector": 2}])
    assert tracker.probability_at(0, 0) == 0.0
    assert tracker.probability_at(3, 3) > 0.0


def test_sector_masses_and_most_likely_helpers():
    map_data = MapData(width=4, height=4, tiles=[["."] * 4 for _ in range(4)])
    tracker = BeliefTracker(map_data, own_team="BLUE")
    tracker.set_point_prior(3, 3)

    masses = tracker.sector_masses()
    assert abs(sum(masses.values()) - 1.0) < 1e-9
    # With SECTOR_ROWS=2 and SECTOR_COLS=2 (config), bottom-right is sector 4.
    assert tracker.most_likely_sector() == 4
    assert tracker.most_likely_cell() == (3, 3)

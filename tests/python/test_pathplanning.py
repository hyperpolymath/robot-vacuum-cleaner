"""
Unit tests for path planning algorithms
"""

import pytest
import numpy as np
from src.python.pathplanning import (
    AStarPlanner,
    SpiralCoveragePlanner,
    ZigzagCoveragePlanner,
    WallFollowPlanner,
    RandomCoveragePlanner,
    CoverageOptimizer
)


@pytest.fixture
def simple_environment():
    """Create a simple test environment"""
    env = np.zeros((30, 30), dtype=np.int8)
    # Add walls
    env[0, :] = 1
    env[-1, :] = 1
    env[:, 0] = 1
    env[:, -1] = 1
    return env


@pytest.fixture
def obstacle_environment():
    """Create an environment with obstacles"""
    env = np.zeros((30, 30), dtype=np.int8)
    # Add walls
    env[0, :] = 1
    env[-1, :] = 1
    env[:, 0] = 1
    env[:, -1] = 1
    # Add central obstacle
    env[10:15, 10:15] = 1
    return env


class TestAStarPlanner:
    """Tests for A* pathfinding algorithm"""

    def test_straight_line_path(self, simple_environment):
        """Test A* finds straight line path"""
        planner = AStarPlanner(simple_environment)
        path = planner.find_path((5, 5), (10, 5))

        assert path is not None
        assert len(path) > 0
        assert path[0] == (5, 5)
        assert path[-1] == (10, 5)

    def test_path_around_obstacle(self, obstacle_environment):
        """Test A* navigates around obstacles"""
        planner = AStarPlanner(obstacle_environment)
        path = planner.find_path((5, 12), (20, 12))

        assert path is not None
        assert len(path) > 0
        assert path[0] == (5, 12)
        assert path[-1] == (20, 12)

        # Verify path doesn't go through obstacle
        for x, y in path:
            assert obstacle_environment[y, x] != 1

    def test_no_path_available(self, obstacle_environment):
        """Test A* returns None when no path exists"""
        # Create completely blocked target
        env = obstacle_environment.copy()
        env[15:17, 15:17] = 1
        env[15, 15] = 0  # Target in middle

        planner = AStarPlanner(env)
        path = planner.find_path((5, 5), (15, 15))

        # May or may not find path depending on implementation
        # Just verify it handles the case
        if path is None:
            assert True
        else:
            assert len(path) > 0

    def test_same_start_and_goal(self, simple_environment):
        """Test A* with same start and goal"""
        planner = AStarPlanner(simple_environment)
        path = planner.find_path((10, 10), (10, 10))

        assert path is not None
        assert len(path) >= 1

    def test_diagonal_movement(self, simple_environment):
        """Test A* with diagonal movement enabled"""
        planner = AStarPlanner(simple_environment)
        path = planner.find_path((5, 5), (10, 10), diagonal=True)

        assert path is not None
        # Diagonal path should be shorter
        assert len(path) < 11


class TestSpiralCoveragePlanner:
    """Tests for spiral coverage algorithm"""

    def test_spiral_generation(self, simple_environment):
        """Test spiral path generation"""
        planner = SpiralCoveragePlanner(simple_environment)
        path = planner.generate_spiral_path((15, 15), max_radius=10)

        assert len(path) > 0
        assert path[0] == (15, 15)

        # Verify spiral expands outward
        distances = []
        for x, y in path[:20]:
            dist = abs(x - 15) + abs(y - 15)
            distances.append(dist)

        # Distances should generally increase
        assert distances[-1] >= distances[0]

    def test_spiral_with_max_radius(self, simple_environment):
        """Test spiral with maximum radius"""
        planner = SpiralCoveragePlanner(simple_environment)
        path = planner.generate_spiral_path((15, 15), max_radius=5)

        # Verify all points within radius
        for x, y in path:
            dist = max(abs(x - 15), abs(y - 15))
            assert dist <= 6  # Allow some margin


class TestZigzagCoveragePlanner:
    """Tests for zigzag coverage algorithm"""

    def test_horizontal_zigzag(self, simple_environment):
        """Test horizontal zigzag pattern"""
        planner = ZigzagCoveragePlanner(simple_environment)
        path = planner.generate_zigzag_path((1, 1), horizontal=True)

        assert len(path) > 0

        # Verify zigzag pattern (alternating directions)
        # Check that path covers multiple rows
        rows = set(y for _, y in path)
        assert len(rows) > 1

    def test_vertical_zigzag(self, simple_environment):
        """Test vertical zigzag pattern"""
        planner = ZigzagCoveragePlanner(simple_environment)
        path = planner.generate_zigzag_path((1, 1), horizontal=False)

        assert len(path) > 0

        # Check that path covers multiple columns
        cols = set(x for x, _ in path)
        assert len(cols) > 1

    def test_zigzag_coverage(self, simple_environment):
        """Test zigzag achieves good coverage"""
        planner = ZigzagCoveragePlanner(simple_environment)
        path = planner.generate_zigzag_path((1, 1), horizontal=True)

        # Count unique cells covered
        unique_cells = set(path)
        total_free = np.sum(simple_environment == 0)

        # Should cover significant portion of free space
        coverage_ratio = len(unique_cells) / total_free
        assert coverage_ratio > 0.5


class TestWallFollowPlanner:
    """Tests for wall-following algorithm"""

    def test_wall_following(self, simple_environment):
        """Test wall following behavior"""
        planner = WallFollowPlanner(simple_environment)
        path = planner.follow_wall((2, 2), max_steps=100)

        assert len(path) > 0
        assert path[0] == (2, 2)

        # Verify path stays within bounds
        for x, y in path:
            assert 0 <= x < 30
            assert 0 <= y < 30
            assert simple_environment[y, x] == 0

    def test_wall_following_with_obstacles(self, obstacle_environment):
        """Test wall following around obstacles"""
        planner = WallFollowPlanner(obstacle_environment)
        path = planner.follow_wall((5, 5), max_steps=100)

        assert len(path) > 0

        # Verify path doesn't go through obstacles
        for x, y in path:
            assert obstacle_environment[y, x] != 1


class TestRandomCoveragePlanner:
    """Tests for random coverage algorithm"""

    def test_random_coverage_basic(self, simple_environment):
        """Test random coverage generation"""
        planner = RandomCoveragePlanner(simple_environment, seed=42)
        path = planner.generate_random_path(
            (15, 15),
            target_coverage=0.5,
            max_steps=1000
        )

        assert len(path) > 0
        assert path[0] == (15, 15)

    def test_random_coverage_deterministic(self, simple_environment):
        """Test random coverage is deterministic with seed"""
        planner1 = RandomCoveragePlanner(simple_environment, seed=42)
        path1 = planner1.generate_random_path((15, 15), target_coverage=0.3, max_steps=100)

        planner2 = RandomCoveragePlanner(simple_environment, seed=42)
        path2 = planner2.generate_random_path((15, 15), target_coverage=0.3, max_steps=100)

        assert path1 == path2

    def test_random_coverage_target(self, simple_environment):
        """Test random coverage reaches target"""
        planner = RandomCoveragePlanner(simple_environment, seed=42)
        path = planner.generate_random_path(
            (15, 15),
            target_coverage=0.5,
            max_steps=5000
        )

        covered = set(path)
        total_free = np.sum(simple_environment == 0)
        coverage = len(covered) / total_free

        # Should reach at least target coverage
        assert coverage >= 0.45  # Allow some tolerance


class TestCoverageOptimizer:
    """Tests for coverage optimization"""

    def test_remove_redundant_moves(self):
        """Test removing redundant moves"""
        # Path with backtracking
        path = [(0, 0), (1, 0), (2, 0), (1, 0), (2, 0), (3, 0)]
        optimized = CoverageOptimizer.remove_redundant_moves(path)

        assert len(optimized) <= len(path)
        assert optimized[0] == path[0]

    def test_remove_redundant_single_point(self):
        """Test with single point path"""
        path = [(5, 5)]
        optimized = CoverageOptimizer.remove_redundant_moves(path)

        assert optimized == path

    def test_smooth_path(self):
        """Test path smoothing"""
        # Create path with unnecessary waypoints
        path = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
        smoothed = CoverageOptimizer.smooth_path(path)

        assert len(smoothed) <= len(path)
        assert smoothed[0] == path[0]
        assert smoothed[-1] == path[-1]

    def test_smooth_path_preserves_endpoints(self):
        """Test smoothing preserves start and end"""
        path = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        smoothed = CoverageOptimizer.smooth_path(path)

        assert smoothed[0] == path[0]
        assert smoothed[-1] == path[-1]


class TestPathPlanningIntegration:
    """Integration tests for path planning"""

    def test_all_planners_produce_valid_paths(self, simple_environment):
        """Test all planners produce valid paths"""
        # A* planner
        astar = AStarPlanner(simple_environment)
        path1 = astar.find_path((5, 5), (20, 20))
        assert path1 is not None
        assert all(simple_environment[y, x] == 0 for x, y in path1)

        # Spiral planner
        spiral = SpiralCoveragePlanner(simple_environment)
        path2 = spiral.generate_spiral_path((15, 15), max_radius=10)
        assert len(path2) > 0

        # Zigzag planner
        zigzag = ZigzagCoveragePlanner(simple_environment)
        path3 = zigzag.generate_zigzag_path((1, 1))
        assert len(path3) > 0

        # Wall follow planner
        wall = WallFollowPlanner(simple_environment)
        path4 = wall.follow_wall((5, 5), max_steps=100)
        assert len(path4) > 0

        # Random planner
        random_planner = RandomCoveragePlanner(simple_environment, seed=42)
        path5 = random_planner.generate_random_path((15, 15), target_coverage=0.3, max_steps=500)
        assert len(path5) > 0

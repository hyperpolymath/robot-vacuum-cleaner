"""
Unit tests for environment simulation
"""

import pytest
import numpy as np
from src.python.environment import (
    Environment,
    EnvironmentGenerator,
    CellType,
    create_environment,
    PREDEFINED_ROOMS
)


class TestEnvironmentGenerator:
    """Tests for environment generation"""

    def test_create_empty_room(self):
        """Test empty room generation"""
        env = EnvironmentGenerator.create_empty_room(30, 40)

        assert env.shape == (40, 30)  # height, width
        assert env[0, 15] == CellType.OBSTACLE.value  # Top wall
        assert env[-1, 15] == CellType.OBSTACLE.value  # Bottom wall
        assert env[15, 0] == CellType.OBSTACLE.value  # Left wall
        assert env[15, -1] == CellType.OBSTACLE.value  # Right wall
        assert env[15, 15] == CellType.FREE.value  # Center is free

    def test_create_room_with_furniture(self):
        """Test room with furniture generation"""
        env = EnvironmentGenerator.create_room_with_furniture(50, 50, num_obstacles=3)

        assert env.shape == (50, 50)
        # Count obstacles (excluding walls)
        obstacles = np.sum(env[1:-1, 1:-1] == CellType.OBSTACLE.value)
        assert obstacles > 0  # Should have some furniture

    def test_create_multi_room(self):
        """Test multi-room generation"""
        env = EnvironmentGenerator.create_multi_room(80, 60)

        assert env.shape == (60, 80)
        # Should have dividing walls
        mid_x = 80 // 2
        mid_y = 60 // 2
        # Check that there are dividers
        assert np.any(env[mid_y, :] == CellType.OBSTACLE.value)
        assert np.any(env[:, mid_x] == CellType.OBSTACLE.value)

    def test_create_narrow_corridor(self):
        """Test narrow corridor generation"""
        env = EnvironmentGenerator.create_narrow_corridor(length=60, width=5)

        assert env.shape == (5, 60)
        # Should have corridor in the middle
        assert env[2, 30] == CellType.FREE.value

    def test_create_obstacle_course(self):
        """Test obstacle course generation"""
        env = EnvironmentGenerator.create_obstacle_course(60, 60)

        assert env.shape == (60, 60)
        # Should have various obstacles
        obstacles = np.sum(env == CellType.OBSTACLE.value)
        free_space = np.sum(env == CellType.FREE.value)
        assert obstacles > 0
        assert free_space > 0

    def test_create_stairs_test(self):
        """Test stairs/cliff environment"""
        env = EnvironmentGenerator.create_stairs_test(50, 50)

        assert env.shape == (50, 50)
        # Should have cliff cells
        assert np.any(env == CellType.CLIFF.value)

    def test_add_dock_default_position(self):
        """Test adding dock with default position"""
        env = EnvironmentGenerator.create_empty_room(30, 30)
        env_with_dock = EnvironmentGenerator.add_dock(env)

        # Should have exactly one dock
        assert np.sum(env_with_dock == CellType.DOCK.value) >= 1

    def test_add_dock_specific_position(self):
        """Test adding dock at specific position"""
        env = EnvironmentGenerator.create_empty_room(30, 30)
        dock_pos = (10, 10)
        env_with_dock = EnvironmentGenerator.add_dock(env, position=dock_pos)

        assert env_with_dock[dock_pos[1], dock_pos[0]] == CellType.DOCK.value


class TestEnvironment:
    """Tests for Environment class"""

    @pytest.fixture
    def simple_env(self):
        """Create a simple test environment"""
        env_array = EnvironmentGenerator.create_empty_room(30, 30)
        env_array = EnvironmentGenerator.add_dock(env_array, position=(15, 15))
        return Environment(env_array)

    def test_environment_initialization(self, simple_env):
        """Test environment initialization"""
        assert simple_env.width == 30
        assert simple_env.height == 30
        assert simple_env.sim_time == 0.0
        assert simple_env.dock_position is not None

    def test_environment_dirt_initialization(self, simple_env):
        """Test dirt map initialization"""
        # All free cells should start dirty
        free_cells = np.sum(simple_env.original_env == CellType.FREE.value)
        dirty_cells = np.sum(simple_env.dirt_map)
        assert dirty_cells == free_cells

    def test_clean_cell(self, simple_env):
        """Test cleaning a cell"""
        initial_dirty = np.sum(simple_env.dirt_map)
        simple_env.clean_cell(10, 10)
        final_dirty = np.sum(simple_env.dirt_map)

        assert final_dirty < initial_dirty

    def test_is_dirty(self, simple_env):
        """Test checking if cell is dirty"""
        assert simple_env.is_dirty(10, 10) is True
        simple_env.clean_cell(10, 10)
        assert simple_env.is_dirty(10, 10) is False

    def test_cleaning_percentage(self, simple_env):
        """Test cleaning percentage calculation"""
        initial_pct = simple_env.get_cleaning_percentage()
        assert initial_pct == pytest.approx(0.0, abs=0.1)

        # Clean some cells
        for x in range(5, 15):
            for y in range(5, 15):
                if simple_env.is_valid_position(x, y):
                    simple_env.clean_cell(x, y)

        final_pct = simple_env.get_cleaning_percentage()
        assert final_pct > initial_pct

    def test_reset(self, simple_env):
        """Test environment reset"""
        # Clean some cells
        simple_env.clean_cell(10, 10)
        simple_env.clean_cell(11, 11)
        simple_env.sim_time = 100.0

        simple_env.reset()

        assert simple_env.sim_time == 0.0
        assert simple_env.is_dirty(10, 10) is True
        assert simple_env.is_dirty(11, 11) is True

    def test_step(self, simple_env):
        """Test simulation step"""
        initial_time = simple_env.sim_time
        simple_env.step()
        assert simple_env.sim_time > initial_time

    def test_get_cell_type(self, simple_env):
        """Test getting cell type"""
        # Check obstacle (wall)
        assert simple_env.get_cell_type(0, 0) == CellType.OBSTACLE

        # Check free space
        assert simple_env.get_cell_type(10, 10) == CellType.FREE

        # Check dock
        assert simple_env.get_cell_type(15, 15) == CellType.DOCK

    def test_is_valid_position(self, simple_env):
        """Test position validation"""
        # Valid position
        assert simple_env.is_valid_position(10, 10) is True

        # Invalid - obstacle
        assert simple_env.is_valid_position(0, 0) is False

        # Invalid - out of bounds
        assert simple_env.is_valid_position(-1, 10) is False
        assert simple_env.is_valid_position(10, 100) is False

    def test_get_statistics(self, simple_env):
        """Test getting environment statistics"""
        stats = simple_env.get_statistics()

        assert 'width' in stats
        assert 'height' in stats
        assert 'total_area' in stats
        assert 'free_cells' in stats
        assert 'obstacles' in stats
        assert 'cleaning_percentage' in stats
        assert 'sim_time' in stats
        assert 'dock_position' in stats

    def test_dock_position_tuple(self, simple_env):
        """Test dock position is stored as tuple"""
        assert isinstance(simple_env.dock_position, tuple)
        assert len(simple_env.dock_position) == 2

    def test_environment_immutability_after_reset(self, simple_env):
        """Test original environment unchanged after reset"""
        original_copy = simple_env.original_env.copy()
        simple_env.reset()
        assert np.array_equal(simple_env.original_env, original_copy)


class TestPredefinedRooms:
    """Tests for predefined room configurations"""

    def test_predefined_rooms_exist(self):
        """Test predefined rooms are available"""
        assert 'empty' in PREDEFINED_ROOMS
        assert 'furnished' in PREDEFINED_ROOMS
        assert 'multi_room' in PREDEFINED_ROOMS
        assert 'corridor' in PREDEFINED_ROOMS
        assert 'obstacle_course' in PREDEFINED_ROOMS
        assert 'stairs_test' in PREDEFINED_ROOMS

    def test_create_environment_empty(self):
        """Test creating empty room environment"""
        env = create_environment('empty')
        assert isinstance(env, Environment)
        assert env.dock_position is not None

    def test_create_environment_furnished(self):
        """Test creating furnished room environment"""
        env = create_environment('furnished')
        assert isinstance(env, Environment)
        # Should have some obstacles
        obstacles = np.sum(env.env == CellType.OBSTACLE.value)
        assert obstacles > 100  # Walls plus furniture

    def test_create_environment_multi_room(self):
        """Test creating multi-room environment"""
        env = create_environment('multi_room')
        assert isinstance(env, Environment)
        assert env.width >= 80
        assert env.height >= 60

    def test_create_environment_corridor(self):
        """Test creating corridor environment"""
        env = create_environment('corridor')
        assert isinstance(env, Environment)
        # Corridor should be narrow
        assert min(env.width, env.height) < 10

    def test_create_environment_obstacle_course(self):
        """Test creating obstacle course environment"""
        env = create_environment('obstacle_course')
        assert isinstance(env, Environment)

    def test_create_environment_stairs_test(self):
        """Test creating stairs test environment"""
        env = create_environment('stairs_test')
        assert isinstance(env, Environment)
        # Should have cliffs
        assert np.any(env.env == CellType.CLIFF.value)

    def test_create_environment_invalid_type(self):
        """Test creating environment with invalid type"""
        with pytest.raises(ValueError):
            create_environment('nonexistent_room_type')


class TestEnvironmentIntegration:
    """Integration tests for environment"""

    def test_full_cleaning_simulation(self):
        """Test complete cleaning simulation"""
        env = create_environment('empty')

        # Clean all free cells
        for y in range(env.height):
            for x in range(env.width):
                if env.is_valid_position(x, y):
                    env.clean_cell(x, y)

        # Should be 100% clean
        assert env.get_cleaning_percentage() == pytest.approx(100.0, abs=0.1)

    def test_partial_cleaning(self):
        """Test partial cleaning"""
        env = create_environment('furnished')

        total_free = np.sum(env.original_env == CellType.FREE.value)
        cells_to_clean = total_free // 2

        # Clean half the cells
        cleaned = 0
        for y in range(env.height):
            for x in range(env.width):
                if cleaned >= cells_to_clean:
                    break
                if env.is_valid_position(x, y) and env.is_dirty(x, y):
                    env.clean_cell(x, y)
                    cleaned += 1
            if cleaned >= cells_to_clean:
                break

        # Should be approximately 50% clean
        pct = env.get_cleaning_percentage()
        assert 40 < pct < 60

    def test_environment_step_timing(self):
        """Test environment step timing"""
        env = create_environment('empty')

        for _ in range(10):
            env.step(delta_time=1.0)

        assert env.sim_time == pytest.approx(10.0)

    def test_environment_with_custom_tick_rate(self):
        """Test environment with custom tick rate"""
        env_array = EnvironmentGenerator.create_empty_room(20, 20)
        env = Environment(env_array, tick_rate=0.5)

        assert env.tick_rate == 0.5

        env.step()  # Should advance by 0.5
        assert env.sim_time == pytest.approx(0.5)

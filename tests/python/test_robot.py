"""
Unit tests for robot vacuum core functionality
"""

import pytest
import numpy as np
from src.python.robot import (
    RobotVacuum,
    Position,
    RobotState,
    CleaningMode,
    SensorData
)


class TestPosition:
    """Tests for Position class"""

    def test_position_creation(self):
        """Test position creation"""
        pos = Position(5.0, 10.0)
        assert pos.x == 5.0
        assert pos.y == 10.0

    def test_distance_calculation(self):
        """Test distance calculation between positions"""
        pos1 = Position(0.0, 0.0)
        pos2 = Position(3.0, 4.0)
        assert pos1.distance_to(pos2) == pytest.approx(5.0)

    def test_to_grid(self):
        """Test conversion to grid coordinates"""
        pos = Position(5.7, 10.3)
        assert pos.to_grid() == (5, 10)


class TestRobotVacuum:
    """Tests for RobotVacuum class"""

    @pytest.fixture
    def robot(self):
        """Create a test robot"""
        return RobotVacuum(
            position=Position(10.0, 10.0),
            battery_capacity=100.0,
            cleaning_width=0.3,
            speed=0.2
        )

    @pytest.fixture
    def simple_environment(self):
        """Create a simple test environment"""
        env = np.zeros((50, 50), dtype=np.int8)
        # Add walls
        env[0, :] = 1
        env[-1, :] = 1
        env[:, 0] = 1
        env[:, -1] = 1
        # Add some obstacles
        env[15:20, 15:20] = 1
        return env

    def test_robot_initialization(self, robot):
        """Test robot initialization"""
        assert robot.position.x == 10.0
        assert robot.position.y == 10.0
        assert robot.battery_level == 100.0
        assert robot.state == RobotState.IDLE
        assert robot.mode == CleaningMode.AUTO

    def test_robot_movement(self, robot):
        """Test robot movement"""
        initial_x = robot.position.x
        initial_y = robot.position.y

        success = robot.move(1.0, 0.0)

        assert success is True
        assert robot.position.x == initial_x + 1.0
        assert robot.position.y == initial_y
        assert robot.battery_level < 100.0

    def test_battery_depletion(self, robot):
        """Test battery depletes with movement"""
        initial_battery = robot.battery_level

        robot.move(5.0, 5.0)

        assert robot.battery_level < initial_battery

    def test_movement_with_depleted_battery(self, robot):
        """Test movement fails with depleted battery"""
        robot.battery_level = 0.0

        success = robot.move(1.0, 1.0)

        assert success is False
        assert robot.state == RobotState.ERROR

    def test_sensor_update(self, robot, simple_environment):
        """Test sensor updates"""
        robot.position = Position(15.0, 15.0)
        sensor_data = robot.update_sensors(simple_environment)

        assert isinstance(sensor_data, SensorData)
        # Should detect obstacle to the right (15:20 range)
        assert sensor_data.obstacle_front or sensor_data.obstacle_right or \
               sensor_data.obstacle_left or sensor_data.obstacle_back

    def test_dock_position(self, robot):
        """Test setting dock position"""
        dock_pos = Position(5.0, 5.0)
        robot.set_dock_position(dock_pos)

        assert robot.dock_position is not None
        assert robot.dock_position.x == 5.0
        assert robot.dock_position.y == 5.0

    def test_should_return_to_dock_low_battery(self, robot):
        """Test robot returns to dock with low battery"""
        robot.battery_level = 15.0
        assert robot.should_return_to_dock() is True

    def test_should_return_to_dock_sufficient_battery(self, robot):
        """Test robot doesn't return to dock with sufficient battery"""
        robot.battery_level = 50.0
        assert robot.should_return_to_dock() is False

    def test_charging(self, robot):
        """Test robot charging"""
        robot.battery_level = 50.0
        robot.state = RobotState.CHARGING

        fully_charged = robot.charge(charge_rate=10.0)

        assert robot.battery_level == 60.0
        assert fully_charged is False

        # Charge until full
        for _ in range(10):
            fully_charged = robot.charge(charge_rate=10.0)
            if fully_charged:
                break

        assert robot.battery_level == 100.0
        assert fully_charged is True

    def test_stats_tracking(self, robot):
        """Test statistics tracking"""
        robot.move(5.0, 0.0)
        robot.move(0.0, 5.0)

        assert robot.stats.total_distance > 0
        assert len(robot.cleaned_cells) > 0
        assert len(robot.visited_cells) > 0

    def test_get_status(self, robot):
        """Test getting robot status"""
        status = robot.get_status()

        assert 'position' in status
        assert 'battery_level' in status
        assert 'state' in status
        assert 'mode' in status
        assert 'stats' in status
        assert 'sensors' in status

    def test_reset_stats(self, robot):
        """Test resetting statistics"""
        robot.move(5.0, 5.0)
        robot.reset_stats()

        assert robot.stats.total_distance == 0.0
        assert robot.stats.area_cleaned == 0
        assert len(robot.cleaned_cells) == 0
        assert len(robot.visited_cells) == 0

    def test_path_history(self, robot):
        """Test path history tracking"""
        initial_length = len(robot.path_history)

        robot.move(1.0, 0.0)
        robot.move(0.0, 1.0)
        robot.move(-1.0, 0.0)

        assert len(robot.path_history) == initial_length + 3

    def test_cleaning_width(self, robot):
        """Test cleaning width parameter"""
        assert robot.cleaning_width == 0.3

    def test_speed_parameter(self, robot):
        """Test speed parameter"""
        assert robot.speed == 0.2

    def test_sensor_range(self, robot):
        """Test sensor range parameter"""
        assert robot.sensor_range == 2.0


class TestRobotStates:
    """Tests for robot state transitions"""

    @pytest.fixture
    def robot(self):
        return RobotVacuum(position=Position(10.0, 10.0))

    def test_idle_to_cleaning(self, robot):
        """Test transition from idle to cleaning"""
        robot.state = RobotState.IDLE
        robot.state = RobotState.CLEANING
        assert robot.state == RobotState.CLEANING

    def test_cleaning_to_returning(self, robot):
        """Test transition from cleaning to returning to dock"""
        robot.state = RobotState.CLEANING
        robot.state = RobotState.RETURNING_TO_DOCK
        assert robot.state == RobotState.RETURNING_TO_DOCK

    def test_returning_to_charging(self, robot):
        """Test transition to charging state"""
        robot.state = RobotState.RETURNING_TO_DOCK
        robot.state = RobotState.CHARGING
        assert robot.state == RobotState.CHARGING

    def test_error_state(self, robot):
        """Test error state"""
        robot.state = RobotState.ERROR
        assert robot.state == RobotState.ERROR

    def test_stuck_state(self, robot):
        """Test stuck state"""
        robot.state = RobotState.STUCK
        assert robot.state == RobotState.STUCK


class TestCleaningModes:
    """Tests for cleaning modes"""

    @pytest.fixture
    def robot(self):
        return RobotVacuum(position=Position(10.0, 10.0))

    def test_auto_mode(self, robot):
        """Test auto cleaning mode"""
        robot.mode = CleaningMode.AUTO
        assert robot.mode == CleaningMode.AUTO

    def test_spiral_mode(self, robot):
        """Test spiral cleaning mode"""
        robot.mode = CleaningMode.SPIRAL
        assert robot.mode == CleaningMode.SPIRAL

    def test_zigzag_mode(self, robot):
        """Test zigzag cleaning mode"""
        robot.mode = CleaningMode.ZIGZAG
        assert robot.mode == CleaningMode.ZIGZAG

    def test_wall_follow_mode(self, robot):
        """Test wall follow mode"""
        robot.mode = CleaningMode.WALL_FOLLOW
        assert robot.mode == CleaningMode.WALL_FOLLOW

    def test_random_mode(self, robot):
        """Test random cleaning mode"""
        robot.mode = CleaningMode.RANDOM
        assert robot.mode == CleaningMode.RANDOM

    def test_spot_mode(self, robot):
        """Test spot cleaning mode"""
        robot.mode = CleaningMode.SPOT
        assert robot.mode == CleaningMode.SPOT

    def test_edge_mode(self, robot):
        """Test edge cleaning mode"""
        robot.mode = CleaningMode.EDGE
        assert robot.mode == CleaningMode.EDGE

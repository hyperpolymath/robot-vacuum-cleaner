"""
Robot Vacuum Cleaner Core Implementation

This module provides the core robot vacuum cleaner class with navigation,
sensor integration, and cleaning algorithms.
"""

import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RobotState(Enum):
    """Robot operational states"""
    IDLE = "idle"
    CLEANING = "cleaning"
    RETURNING_TO_DOCK = "returning_to_dock"
    CHARGING = "charging"
    ERROR = "error"
    STUCK = "stuck"


class CleaningMode(Enum):
    """Available cleaning modes"""
    AUTO = "auto"
    SPOT = "spot"
    EDGE = "edge"
    SPIRAL = "spiral"
    ZIGZAG = "zigzag"
    WALL_FOLLOW = "wall_follow"
    RANDOM = "random"


class Direction(Enum):
    """Movement directions"""
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)
    NORTHEAST = (1, -1)
    NORTHWEST = (-1, -1)
    SOUTHEAST = (1, 1)
    SOUTHWEST = (-1, 1)


@dataclass
class Position:
    """2D position representation"""
    x: float
    y: float

    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position"""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def to_grid(self) -> Tuple[int, int]:
        """Convert to grid coordinates"""
        return (int(self.x), int(self.y))


@dataclass
class SensorData:
    """Sensor readings"""
    obstacle_front: bool = False
    obstacle_left: bool = False
    obstacle_right: bool = False
    obstacle_back: bool = False
    cliff_detected: bool = False
    bumper_triggered: bool = False
    distance_front: float = float('inf')
    distance_left: float = float('inf')
    distance_right: float = float('inf')
    distance_back: float = float('inf')


@dataclass
class RobotStats:
    """Robot operational statistics"""
    total_distance: float = 0.0
    area_cleaned: int = 0
    cleaning_time: float = 0.0
    battery_cycles: int = 0
    errors_encountered: int = 0
    stuck_count: int = 0


class RobotVacuum:
    """
    Main robot vacuum cleaner class

    Handles navigation, cleaning, sensor processing, and state management.
    """

    def __init__(
        self,
        position: Position,
        battery_capacity: float = 100.0,
        cleaning_width: float = 0.3,
        speed: float = 0.2,
        sensor_range: float = 2.0
    ):
        self.position = position
        self.battery_capacity = battery_capacity
        self.battery_level = battery_capacity
        self.cleaning_width = cleaning_width
        self.speed = speed
        self.sensor_range = sensor_range

        self.state = RobotState.IDLE
        self.mode = CleaningMode.AUTO
        self.heading = 0.0  # degrees

        self.dock_position: Optional[Position] = None
        self.sensor_data = SensorData()
        self.stats = RobotStats()

        self.cleaned_cells: Set[Tuple[int, int]] = set()
        self.visited_cells: Set[Tuple[int, int]] = set()
        self.path_history: List[Position] = [position]

        self.environment_map: Optional[np.ndarray] = None
        self.obstacle_map: Optional[np.ndarray] = None

        logger.info(f"Robot initialized at position ({position.x}, {position.y})")

    def update_sensors(self, environment: np.ndarray) -> SensorData:
        """
        Update sensor readings based on environment

        Args:
            environment: 2D numpy array representing the environment
                        (0=free, 1=obstacle, 2=cliff, 3=dock)

        Returns:
            Updated sensor data
        """
        x, y = self.position.to_grid()
        height, width = environment.shape

        # Reset sensor data
        self.sensor_data = SensorData()

        # Check obstacles in cardinal directions
        directions = {
            'front': (0, -1),
            'back': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }

        for direction, (dx, dy) in directions.items():
            check_x, check_y = x + dx, y + dy

            if 0 <= check_x < width and 0 <= check_y < height:
                cell_value = environment[check_y, check_x]

                if cell_value == 1:  # Obstacle
                    setattr(self.sensor_data, f'obstacle_{direction}', True)
                    setattr(self.sensor_data, f'distance_{direction}', 1.0)
                elif cell_value == 2:  # Cliff
                    self.sensor_data.cliff_detected = True
                else:
                    # Calculate distance to nearest obstacle in this direction
                    distance = self._calculate_distance_to_obstacle(
                        environment, x, y, dx, dy
                    )
                    setattr(self.sensor_data, f'distance_{direction}', distance)
            else:
                # Edge of map
                setattr(self.sensor_data, f'obstacle_{direction}', True)
                setattr(self.sensor_data, f'distance_{direction}', 0.0)

        return self.sensor_data

    def _calculate_distance_to_obstacle(
        self,
        environment: np.ndarray,
        x: int,
        y: int,
        dx: int,
        dy: int
    ) -> float:
        """Calculate distance to nearest obstacle in given direction"""
        height, width = environment.shape
        distance = 0.0

        while distance < self.sensor_range:
            x += dx
            y += dy
            distance += 1.0

            if not (0 <= x < width and 0 <= y < height):
                return distance

            if environment[y, x] in [1, 2]:  # Obstacle or cliff
                return distance

        return self.sensor_range

    def move(self, dx: float, dy: float) -> bool:
        """
        Move robot by given delta

        Args:
            dx: Change in x coordinate
            dy: Change in y coordinate

        Returns:
            True if move was successful, False otherwise
        """
        if self.battery_level <= 0:
            self.state = RobotState.ERROR
            logger.warning("Cannot move: battery depleted")
            return False

        new_position = Position(
            self.position.x + dx,
            self.position.y + dy
        )

        # Update position
        self.position = new_position
        self.path_history.append(new_position)

        # Update stats
        distance = np.sqrt(dx**2 + dy**2)
        self.stats.total_distance += distance

        # Consume battery (proportional to distance)
        battery_consumption = distance * 0.1
        self.battery_level = max(0, self.battery_level - battery_consumption)

        # Mark cell as visited and cleaned
        grid_pos = self.position.to_grid()
        self.visited_cells.add(grid_pos)
        self.cleaned_cells.add(grid_pos)
        self.stats.area_cleaned = len(self.cleaned_cells)

        return True

    def should_return_to_dock(self) -> bool:
        """Determine if robot should return to charging dock"""
        if self.battery_level < 20.0:
            return True

        if self.dock_position:
            distance_to_dock = self.position.distance_to(self.dock_position)
            # Estimate battery needed to return
            estimated_battery_needed = distance_to_dock * 0.1 * 1.5  # 50% safety margin
            if self.battery_level < estimated_battery_needed + 10:
                return True

        return False

    def charge(self, charge_rate: float = 10.0) -> bool:
        """
        Charge the robot battery

        Args:
            charge_rate: Amount to charge per tick

        Returns:
            True if fully charged, False otherwise
        """
        if self.state != RobotState.CHARGING:
            self.state = RobotState.CHARGING

        self.battery_level = min(
            self.battery_capacity,
            self.battery_level + charge_rate
        )

        if self.battery_level >= self.battery_capacity:
            self.stats.battery_cycles += 1
            logger.info("Battery fully charged")
            return True

        return False

    def set_dock_position(self, position: Position):
        """Set the charging dock position"""
        self.dock_position = position
        logger.info(f"Dock position set to ({position.x}, {position.y})")

    def get_status(self) -> dict:
        """Get current robot status as dictionary"""
        return {
            'position': {'x': self.position.x, 'y': self.position.y},
            'battery_level': self.battery_level,
            'state': self.state.value,
            'mode': self.mode.value,
            'heading': self.heading,
            'stats': {
                'total_distance': self.stats.total_distance,
                'area_cleaned': self.stats.area_cleaned,
                'cleaning_time': self.stats.cleaning_time,
                'battery_cycles': self.stats.battery_cycles,
                'errors': self.stats.errors_encountered,
                'stuck_count': self.stats.stuck_count
            },
            'sensors': {
                'obstacle_front': self.sensor_data.obstacle_front,
                'obstacle_left': self.sensor_data.obstacle_left,
                'obstacle_right': self.sensor_data.obstacle_right,
                'obstacle_back': self.sensor_data.obstacle_back,
                'cliff_detected': self.sensor_data.cliff_detected,
                'bumper_triggered': self.sensor_data.bumper_triggered
            }
        }

    def reset_stats(self):
        """Reset operational statistics"""
        self.stats = RobotStats()
        self.cleaned_cells.clear()
        self.visited_cells.clear()
        self.path_history = [self.position]
        logger.info("Statistics reset")

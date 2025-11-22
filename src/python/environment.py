"""
Environment simulation for robot vacuum cleaner testing

Provides various room layouts, obstacle configurations, and testing scenarios.
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class CellType(Enum):
    """Environment cell types"""
    FREE = 0
    OBSTACLE = 1
    CLIFF = 2
    DOCK = 3
    DIRTY = 4


@dataclass
class Room:
    """Room configuration"""
    width: int
    height: int
    obstacles: List[Tuple[int, int]]
    dock_position: Tuple[int, int]
    name: str = "Generic Room"


class EnvironmentGenerator:
    """Generate various test environments"""

    @staticmethod
    def create_empty_room(width: int = 50, height: int = 50) -> np.ndarray:
        """Create empty rectangular room"""
        env = np.zeros((height, width), dtype=np.int8)

        # Add walls
        env[0, :] = CellType.OBSTACLE.value  # Top wall
        env[-1, :] = CellType.OBSTACLE.value  # Bottom wall
        env[:, 0] = CellType.OBSTACLE.value  # Left wall
        env[:, -1] = CellType.OBSTACLE.value  # Right wall

        return env

    @staticmethod
    def create_room_with_furniture(
        width: int = 50,
        height: int = 50,
        num_obstacles: int = 5
    ) -> np.ndarray:
        """Create room with random furniture obstacles"""
        env = EnvironmentGenerator.create_empty_room(width, height)

        # Add random furniture
        for _ in range(num_obstacles):
            # Random size furniture (2x2 to 5x5)
            furn_width = np.random.randint(2, 6)
            furn_height = np.random.randint(2, 6)

            # Random position (not too close to edges)
            x = np.random.randint(5, width - furn_width - 5)
            y = np.random.randint(5, height - furn_height - 5)

            # Place furniture
            env[y:y+furn_height, x:x+furn_width] = CellType.OBSTACLE.value

        return env

    @staticmethod
    def create_multi_room(width: int = 80, height: int = 60) -> np.ndarray:
        """Create multi-room environment with corridors"""
        env = EnvironmentGenerator.create_empty_room(width, height)

        # Divide into 4 rooms with corridors
        mid_x = width // 2
        mid_y = height // 2

        # Horizontal divider with doorway
        env[mid_y, 5:-5] = CellType.OBSTACLE.value
        doorway_x = mid_x + np.random.randint(-5, 6)
        env[mid_y, doorway_x-2:doorway_x+2] = CellType.FREE.value

        # Vertical divider with doorway
        env[5:-5, mid_x] = CellType.OBSTACLE.value
        doorway_y = mid_y + np.random.randint(-5, 6)
        env[doorway_y-2:doorway_y+2, mid_x] = CellType.FREE.value

        # Add some furniture in each room
        for room_x, room_y in [(mid_x//2, mid_y//2), (mid_x + mid_x//2, mid_y//2),
                                (mid_x//2, mid_y + mid_y//2), (mid_x + mid_x//2, mid_y + mid_y//2)]:
            furn_size = 3
            env[room_y-1:room_y+2, room_x-1:room_x+2] = CellType.OBSTACLE.value

        return env

    @staticmethod
    def create_narrow_corridor(length: int = 60, width: int = 5) -> np.ndarray:
        """Create narrow corridor for testing tight spaces"""
        env = np.ones((width, length), dtype=np.int8) * CellType.OBSTACLE.value

        # Create corridor in the middle
        corridor_start = 1
        corridor_end = width - 1
        env[corridor_start:corridor_end, 1:-1] = CellType.FREE.value

        # Add some obstacles in corridor
        for _ in range(5):
            x = np.random.randint(5, length - 5)
            y = corridor_start + np.random.randint(0, corridor_end - corridor_start)
            env[y, x] = CellType.OBSTACLE.value

        return env

    @staticmethod
    def create_obstacle_course(width: int = 60, height: int = 60) -> np.ndarray:
        """Create challenging obstacle course"""
        env = EnvironmentGenerator.create_empty_room(width, height)

        # Add various obstacle shapes

        # L-shaped obstacle
        env[10:20, 10:15] = CellType.OBSTACLE.value
        env[15:20, 10:20] = CellType.OBSTACLE.value

        # U-shaped obstacle
        env[25:35, 25:28] = CellType.OBSTACLE.value
        env[25:35, 35:38] = CellType.OBSTACLE.value
        env[32:35, 25:38] = CellType.OBSTACLE.value

        # Scattered obstacles
        for x, y in [(15, 30), (30, 15), (40, 40), (20, 45), (45, 20)]:
            env[y-2:y+2, x-2:x+2] = CellType.OBSTACLE.value

        # Narrow passage
        env[height//2-1:height//2+2, 5:width-10] = CellType.OBSTACLE.value
        env[height//2, width//2-2:width//2+2] = CellType.FREE.value

        return env

    @staticmethod
    def create_stairs_test(width: int = 50, height: int = 50) -> np.ndarray:
        """Create environment with cliffs (stairs) for safety testing"""
        env = EnvironmentGenerator.create_empty_room(width, height)

        # Add cliff areas
        env[height//3:height//3+5, 10:width-10] = CellType.CLIFF.value
        env[2*height//3:2*height//3+5, 10:width-10] = CellType.CLIFF.value

        return env

    @staticmethod
    def add_dock(env: np.ndarray, position: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """
        Add charging dock to environment

        Args:
            env: Environment array
            position: Dock position, or None for random placement

        Returns:
            Environment with dock added
        """
        height, width = env.shape

        if position is None:
            # Find valid position (free cell near wall)
            valid_positions = []

            for y in range(2, height - 2):
                for x in range(2, width - 2):
                    if env[y, x] == CellType.FREE.value:
                        # Check if near wall
                        if (env[y-1, x] == CellType.OBSTACLE.value or
                            env[y+1, x] == CellType.OBSTACLE.value or
                            env[y, x-1] == CellType.OBSTACLE.value or
                            env[y, x+1] == CellType.OBSTACLE.value):
                            valid_positions.append((x, y))

            if valid_positions:
                x, y = valid_positions[np.random.randint(len(valid_positions))]
            else:
                # Fallback to any free position
                free_cells = np.argwhere(env == CellType.FREE.value)
                if len(free_cells) > 0:
                    y, x = free_cells[np.random.randint(len(free_cells))]
                else:
                    x, y = width // 2, height // 2
        else:
            x, y = position

        env[y, x] = CellType.DOCK.value
        return env


class Environment:
    """
    Simulation environment for robot vacuum

    Manages the physical environment, tracks state, and provides visualization.
    """

    def __init__(self, env_array: np.ndarray, tick_rate: float = 0.1):
        """
        Initialize environment

        Args:
            env_array: 2D array representing the environment
            tick_rate: Simulation time step in seconds
        """
        self.env = env_array.copy()
        self.original_env = env_array.copy()
        self.height, self.width = env_array.shape
        self.tick_rate = tick_rate

        # Find dock position
        dock_positions = np.argwhere(self.env == CellType.DOCK.value)
        if len(dock_positions) > 0:
            self.dock_position = tuple(dock_positions[0][::-1])  # (x, y)
        else:
            self.dock_position = None

        # Track dirt/cleaned areas
        self.dirt_map = np.zeros_like(self.env, dtype=bool)
        self._initialize_dirt()

        self.sim_time = 0.0

    def _initialize_dirt(self):
        """Initialize dirty areas (all free cells start dirty)"""
        self.dirt_map = (self.env == CellType.FREE.value)

    def clean_cell(self, x: int, y: int):
        """Mark cell as cleaned"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.dirt_map[y, x] = False

    def is_dirty(self, x: int, y: int) -> bool:
        """Check if cell is dirty"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.dirt_map[y, x]
        return False

    def get_cleaning_percentage(self) -> float:
        """Get percentage of area cleaned"""
        total_cleanable = np.sum(self.original_env == CellType.FREE.value)
        if total_cleanable == 0:
            return 100.0

        cleaned = total_cleanable - np.sum(self.dirt_map)
        return (cleaned / total_cleanable) * 100.0

    def reset(self):
        """Reset environment to initial state"""
        self.env = self.original_env.copy()
        self._initialize_dirt()
        self.sim_time = 0.0

    def step(self, delta_time: Optional[float] = None):
        """
        Advance simulation by one time step

        Args:
            delta_time: Time step (uses tick_rate if None)
        """
        if delta_time is None:
            delta_time = self.tick_rate

        self.sim_time += delta_time

    def get_cell_type(self, x: int, y: int) -> CellType:
        """Get cell type at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return CellType(self.env[y, x])
        return CellType.OBSTACLE  # Out of bounds treated as obstacle

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is valid (not obstacle or cliff)"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        cell_type = CellType(self.env[y, x])
        return cell_type in [CellType.FREE, CellType.DOCK, CellType.DIRTY]

    def get_statistics(self) -> dict:
        """Get environment statistics"""
        return {
            'width': self.width,
            'height': self.height,
            'total_area': self.width * self.height,
            'free_cells': int(np.sum(self.env == CellType.FREE.value)),
            'obstacles': int(np.sum(self.env == CellType.OBSTACLE.value)),
            'cleaning_percentage': self.get_cleaning_percentage(),
            'sim_time': self.sim_time,
            'dock_position': self.dock_position
        }


# Predefined room configurations
PREDEFINED_ROOMS = {
    'empty': lambda: EnvironmentGenerator.create_empty_room(50, 50),
    'furnished': lambda: EnvironmentGenerator.create_room_with_furniture(50, 50, 5),
    'multi_room': lambda: EnvironmentGenerator.create_multi_room(80, 60),
    'corridor': lambda: EnvironmentGenerator.create_narrow_corridor(60, 8),
    'obstacle_course': lambda: EnvironmentGenerator.create_obstacle_course(60, 60),
    'stairs_test': lambda: EnvironmentGenerator.create_stairs_test(50, 50)
}


def create_environment(room_type: str = 'furnished') -> Environment:
    """
    Create environment from predefined room type

    Args:
        room_type: One of: 'empty', 'furnished', 'multi_room', 'corridor',
                   'obstacle_course', 'stairs_test'

    Returns:
        Initialized Environment
    """
    if room_type not in PREDEFINED_ROOMS:
        raise ValueError(f"Unknown room type: {room_type}. Available: {list(PREDEFINED_ROOMS.keys())}")

    env_array = PREDEFINED_ROOMS[room_type]()
    env_array = EnvironmentGenerator.add_dock(env_array)

    return Environment(env_array)

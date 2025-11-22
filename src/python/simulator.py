"""
Simulation Controller

Orchestrates the robot vacuum simulation with environment, robot, path planning, and SLAM.
"""

import numpy as np
from typing import Optional, List, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

from robot import RobotVacuum, RobotState, CleaningMode, Position
from environment import Environment, create_environment, CellType
from pathplanning import (
    AStarPlanner, SpiralCoveragePlanner, ZigzagCoveragePlanner,
    WallFollowPlanner, RandomCoveragePlanner, CoverageOptimizer
)
from slam import SLAM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """Simulation configuration"""
    room_type: str = 'furnished'
    cleaning_mode: str = 'auto'
    max_steps: int = 10000
    enable_slam: bool = True
    enable_visualization: bool = False
    random_seed: Optional[int] = None


class SimulationController:
    """
    Main simulation controller

    Manages the complete simulation loop including robot control,
    path planning, SLAM, and environment interaction.
    """

    def __init__(self, config: SimulationConfig):
        """
        Initialize simulation

        Args:
            config: Simulation configuration
        """
        self.config = config

        if config.random_seed is not None:
            np.random.seed(config.random_seed)

        # Create environment
        self.environment = create_environment(config.room_type)
        logger.info(f"Environment created: {config.room_type}")

        # Find valid starting position
        start_pos = self._find_start_position()

        # Initialize robot
        self.robot = RobotVacuum(
            position=Position(start_pos[0], start_pos[1]),
            battery_capacity=100.0,
            cleaning_width=0.3,
            speed=0.2
        )

        # Set dock position
        if self.environment.dock_position:
            self.robot.set_dock_position(
                Position(*self.environment.dock_position)
            )

        # Initialize SLAM if enabled
        self.slam: Optional[SLAM] = None
        if config.enable_slam:
            self.slam = SLAM(
                width=self.environment.width,
                height=self.environment.height,
                resolution=0.05,
                num_particles=100
            )

        # Initialize path planners
        self.astar_planner = AStarPlanner(self.environment.env)
        self.spiral_planner = SpiralCoveragePlanner(self.environment.env)
        self.zigzag_planner = ZigzagCoveragePlanner(self.environment.env)
        self.wall_follow_planner = WallFollowPlanner(self.environment.env)
        self.random_planner = RandomCoveragePlanner(
            self.environment.env,
            seed=config.random_seed
        )

        # Current path
        self.current_path: List[Tuple[int, int]] = []
        self.path_index = 0

        # Statistics
        self.steps = 0
        self.stuck_counter = 0
        self.max_stuck_attempts = 10

        logger.info("Simulation initialized")

    def _find_start_position(self) -> Tuple[int, int]:
        """Find valid starting position in environment"""
        # Try to start near dock if available
        if self.environment.dock_position:
            dock_x, dock_y = self.environment.dock_position

            # Check positions around dock
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                x, y = dock_x + dx, dock_y + dy
                if self.environment.is_valid_position(x, y):
                    return (x, y)

        # Otherwise find any free position
        free_cells = np.argwhere(self.environment.env == CellType.FREE.value)
        if len(free_cells) > 0:
            y, x = free_cells[np.random.randint(len(free_cells))]
            return (x, y)

        # Fallback to center
        return (self.environment.width // 2, self.environment.height // 2)

    def _generate_coverage_path(self) -> List[Tuple[int, int]]:
        """Generate coverage path based on cleaning mode"""
        start = self.robot.position.to_grid()

        if self.robot.mode == CleaningMode.SPIRAL:
            path = self.spiral_planner.generate_spiral_path(start)
        elif self.robot.mode == CleaningMode.ZIGZAG:
            path = self.zigzag_planner.generate_zigzag_path(start)
        elif self.robot.mode == CleaningMode.WALL_FOLLOW:
            path = self.wall_follow_planner.follow_wall(start)
        elif self.robot.mode == CleaningMode.RANDOM:
            path = self.random_planner.generate_random_path(start, target_coverage=0.95)
        else:  # AUTO - use zigzag as default
            path = self.zigzag_planner.generate_zigzag_path(start, horizontal=True)

        return CoverageOptimizer.remove_redundant_moves(path)

    def _navigate_to_position(self, target: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """Use A* to navigate to specific position"""
        start = self.robot.position.to_grid()
        return self.astar_planner.find_path(start, target)

    def step(self) -> bool:
        """
        Execute one simulation step

        Returns:
            True if simulation should continue, False if finished
        """
        self.steps += 1
        self.environment.step()

        # Update robot sensors
        self.robot.update_sensors(self.environment.env)

        # Check for cliffs
        if self.robot.sensor_data.cliff_detected:
            logger.warning("Cliff detected! Emergency stop")
            self.robot.state = RobotState.ERROR
            self.robot.stats.errors_encountered += 1
            return False

        # Check battery and return to dock if needed
        if self.robot.should_return_to_dock() and self.robot.state != RobotState.RETURNING_TO_DOCK:
            logger.info("Battery low, returning to dock")
            self.robot.state = RobotState.RETURNING_TO_DOCK

            if self.robot.dock_position:
                dock_grid = self.robot.dock_position.to_grid()
                self.current_path = self._navigate_to_position(dock_grid)
                self.path_index = 0

        # Handle different states
        if self.robot.state == RobotState.CHARGING:
            if self.robot.charge():
                # Fully charged, resume cleaning
                logger.info("Fully charged, resuming cleaning")
                self.robot.state = RobotState.CLEANING
                self.current_path = []
                self.path_index = 0
            return True

        elif self.robot.state == RobotState.RETURNING_TO_DOCK:
            # Follow path to dock
            if self.current_path and self.path_index < len(self.current_path):
                next_pos = self.current_path[self.path_index]
                current_pos = self.robot.position.to_grid()

                dx = next_pos[0] - current_pos[0]
                dy = next_pos[1] - current_pos[1]

                if self.robot.move(dx, dy):
                    self.path_index += 1

                    # Clean cell
                    self.environment.clean_cell(*next_pos)

                    # Update SLAM
                    if self.slam:
                        sensor_points = self._get_sensor_points()
                        self.slam.update(dx, dy, 0, sensor_points)
            else:
                # Reached dock
                logger.info("Reached charging dock")
                self.robot.state = RobotState.CHARGING

            return True

        elif self.robot.state == RobotState.CLEANING:
            # Generate new path if needed
            if not self.current_path or self.path_index >= len(self.current_path):
                self.current_path = self._generate_coverage_path()
                self.path_index = 0

                if not self.current_path:
                    logger.info("No more coverage path available")
                    return False

            # Follow coverage path
            if self.path_index < len(self.current_path):
                next_pos = self.current_path[self.path_index]
                current_pos = self.robot.position.to_grid()

                dx = next_pos[0] - current_pos[0]
                dy = next_pos[1] - current_pos[1]

                # Check if move is valid
                if self.environment.is_valid_position(next_pos[0], next_pos[1]):
                    if self.robot.move(dx, dy):
                        self.path_index += 1
                        self.stuck_counter = 0

                        # Clean cell
                        self.environment.clean_cell(*next_pos)

                        # Update SLAM
                        if self.slam:
                            sensor_points = self._get_sensor_points()
                            self.slam.update(dx, dy, 0, sensor_points)
                else:
                    # Invalid position, skip to next
                    self.path_index += 1
                    self.stuck_counter += 1

                    if self.stuck_counter >= self.max_stuck_attempts:
                        logger.warning("Robot stuck, generating new path")
                        self.robot.stats.stuck_count += 1
                        self.current_path = []
                        self.stuck_counter = 0

            return True

        elif self.robot.state == RobotState.IDLE:
            # Start cleaning
            self.robot.state = RobotState.CLEANING
            return True

        # Check if max steps reached
        if self.steps >= self.config.max_steps:
            logger.info("Maximum steps reached")
            return False

        return True

    def _get_sensor_points(self) -> List[Tuple[int, int]]:
        """Get detected obstacle points from sensors"""
        points = []
        x, y = self.robot.position.to_grid()

        # Simple sensor model: check nearby cells for obstacles
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                check_x, check_y = x + dx, y + dy

                if (0 <= check_x < self.environment.width and
                    0 <= check_y < self.environment.height):

                    if self.environment.env[check_y, check_x] == CellType.OBSTACLE.value:
                        points.append((check_x, check_y))

        return points

    def run(self) -> dict:
        """
        Run complete simulation

        Returns:
            Dictionary with simulation results and statistics
        """
        logger.info("Starting simulation")
        self.robot.state = RobotState.CLEANING

        while self.step():
            pass

        logger.info("Simulation complete")

        return self.get_results()

    def get_results(self) -> dict:
        """Get simulation results and statistics"""
        env_stats = self.environment.get_statistics()
        robot_status = self.robot.get_status()

        results = {
            'steps': self.steps,
            'environment': env_stats,
            'robot': robot_status,
            'cleaning_coverage': self.environment.get_cleaning_percentage(),
            'success': self.robot.state != RobotState.ERROR
        }

        if self.slam:
            results['slam'] = {
                'estimated_pose': self.slam.get_pose(),
                'map_available': True
            }

        return results

    def get_state_for_visualization(self) -> dict:
        """Get current state for visualization"""
        state = {
            'environment': self.environment.env,
            'dirt_map': self.environment.dirt_map,
            'robot_position': (self.robot.position.x, self.robot.position.y),
            'robot_state': self.robot.state.value,
            'battery_level': self.robot.battery_level,
            'path_history': [(p.x, p.y) for p in self.robot.path_history[-100:]],  # Last 100 points
            'current_path': self.current_path[self.path_index:self.path_index+50] if self.current_path else [],
            'cleaned_cells': list(self.robot.cleaned_cells),
            'steps': self.steps
        }

        if self.slam:
            state['slam_map'] = self.slam.get_map()
            state['slam_particles'] = [
                (p.x, p.y) for p in self.slam.get_particles()[:20]  # Sample of particles
            ]

        return state


def run_simulation(config: Optional[SimulationConfig] = None) -> dict:
    """
    Run a complete simulation with given configuration

    Args:
        config: Simulation configuration (uses defaults if None)

    Returns:
        Simulation results
    """
    if config is None:
        config = SimulationConfig()

    sim = SimulationController(config)
    return sim.run()


if __name__ == "__main__":
    # Example simulation run
    config = SimulationConfig(
        room_type='furnished',
        cleaning_mode='zigzag',
        max_steps=5000,
        enable_slam=True,
        random_seed=42
    )

    results = run_simulation(config)

    print("\n=== Simulation Results ===")
    print(f"Steps: {results['steps']}")
    print(f"Success: {results['success']}")
    print(f"Cleaning Coverage: {results['cleaning_coverage']:.2f}%")
    print(f"Total Distance: {results['robot']['stats']['total_distance']:.2f}")
    print(f"Area Cleaned: {results['robot']['stats']['area_cleaned']}")
    print(f"Battery Cycles: {results['robot']['stats']['battery_cycles']}")

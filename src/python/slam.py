"""
SLAM (Simultaneous Localization and Mapping) Implementation

Grid-based SLAM using occupancy grid mapping and particle filter localization.
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Particle:
    """Particle for particle filter localization"""
    x: float
    y: float
    theta: float  # Orientation in radians
    weight: float = 1.0


class OccupancyGrid:
    """
    Occupancy grid map representation

    Uses log-odds representation for probabilistic occupancy mapping.
    """

    def __init__(self, width: int, height: int, resolution: float = 0.05):
        """
        Initialize occupancy grid

        Args:
            width: Grid width in cells
            height: Grid height in cells
            resolution: Size of each cell in meters
        """
        self.width = width
        self.height = height
        self.resolution = resolution

        # Initialize with unknown (0.5 probability)
        # Using log-odds: log(p/(1-p))
        # 0 = unknown, positive = occupied, negative = free
        self.grid = np.zeros((height, width), dtype=np.float32)

        # Track which cells have been observed
        self.observed = np.zeros((height, width), dtype=bool)

        # Constants for log-odds updates
        self.log_odds_occupied = np.log(0.7 / 0.3)  # Increase when occupied observed
        self.log_odds_free = np.log(0.3 / 0.7)  # Decrease when free observed
        self.log_odds_max = 3.5  # Clamp maximum
        self.log_odds_min = -3.5  # Clamp minimum

    def update_cell(self, x: int, y: int, is_occupied: bool):
        """
        Update single cell's occupancy

        Args:
            x, y: Grid coordinates
            is_occupied: True if cell is occupied, False if free
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        if is_occupied:
            self.grid[y, x] += self.log_odds_occupied
            self.grid[y, x] = min(self.grid[y, x], self.log_odds_max)
        else:
            self.grid[y, x] += self.log_odds_free
            self.grid[y, x] = max(self.grid[y, x], self.log_odds_min)

        self.observed[y, x] = True

    def get_probability(self, x: int, y: int) -> float:
        """
        Get occupancy probability for cell

        Args:
            x, y: Grid coordinates

        Returns:
            Probability (0-1) that cell is occupied
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 0.5

        if not self.observed[y, x]:
            return 0.5  # Unknown

        # Convert log-odds to probability
        odds = np.exp(self.grid[y, x])
        return odds / (1 + odds)

    def is_occupied(self, x: int, y: int, threshold: float = 0.6) -> bool:
        """Check if cell is occupied above threshold"""
        return self.get_probability(x, y) > threshold

    def bresenham_line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int
    ) -> List[Tuple[int, int]]:
        """
        Bresenham's line algorithm for ray tracing

        Args:
            x0, y0: Start coordinates
            x1, y1: End coordinates

        Returns:
            List of grid cells along the line
        """
        cells = []

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        x, y = x0, y0

        while True:
            cells.append((x, y))

            if x == x1 and y == y1:
                break

            e2 = 2 * err

            if e2 > -dy:
                err -= dy
                x += sx

            if e2 < dx:
                err += dx
                y += sy

        return cells

    def update_from_scan(
        self,
        robot_x: int,
        robot_y: int,
        scan_points: List[Tuple[int, int]]
    ):
        """
        Update map from sensor scan

        Args:
            robot_x, robot_y: Robot position
            scan_points: List of detected obstacle points
        """
        for point_x, point_y in scan_points:
            # Trace ray from robot to obstacle
            ray = self.bresenham_line(robot_x, robot_y, point_x, point_y)

            # Mark cells along ray as free (except last)
            for x, y in ray[:-1]:
                self.update_cell(x, y, is_occupied=False)

            # Mark endpoint as occupied
            self.update_cell(point_x, point_y, is_occupied=True)

    def get_map_array(self, unknown_value: int = -1) -> np.ndarray:
        """
        Get map as discrete array

        Args:
            unknown_value: Value for unobserved cells

        Returns:
            Array with values: 0=free, 1=occupied, unknown_value=unknown
        """
        result = np.full((self.height, self.width), unknown_value, dtype=np.int8)

        for y in range(self.height):
            for x in range(self.width):
                if self.observed[y, x]:
                    result[y, x] = 1 if self.is_occupied(x, y) else 0

        return result


class ParticleFilter:
    """
    Particle filter for robot localization

    Uses Monte Carlo localization to estimate robot pose.
    """

    def __init__(
        self,
        num_particles: int = 100,
        width: int = 100,
        height: int = 100
    ):
        """
        Initialize particle filter

        Args:
            num_particles: Number of particles to use
            width: Environment width
            height: Environment height
        """
        self.num_particles = num_particles
        self.width = width
        self.height = height

        # Initialize particles randomly
        self.particles = [
            Particle(
                x=np.random.uniform(0, width),
                y=np.random.uniform(0, height),
                theta=np.random.uniform(0, 2 * np.pi),
                weight=1.0 / num_particles
            )
            for _ in range(num_particles)
        ]

    def predict(self, delta_x: float, delta_y: float, delta_theta: float, noise: float = 0.1):
        """
        Prediction step - move particles based on motion model

        Args:
            delta_x: Change in x position
            delta_y: Change in y position
            delta_theta: Change in orientation
            noise: Motion noise standard deviation
        """
        for particle in self.particles:
            # Add motion with noise
            particle.x += delta_x + np.random.normal(0, noise)
            particle.y += delta_y + np.random.normal(0, noise)
            particle.theta += delta_theta + np.random.normal(0, noise * 0.1)

            # Keep theta in [0, 2*pi]
            particle.theta = particle.theta % (2 * np.pi)

            # Bounds checking
            particle.x = np.clip(particle.x, 0, self.width - 1)
            particle.y = np.clip(particle.y, 0, self.height - 1)

    def update(self, measurement: List[Tuple[int, int]], occupancy_grid: OccupancyGrid):
        """
        Update step - weight particles based on sensor measurements

        Args:
            measurement: List of obstacle points from sensors
            occupancy_grid: Current occupancy grid map
        """
        if not measurement:
            return

        for particle in self.particles:
            # Calculate likelihood of measurement given particle position
            likelihood = 0.0

            for obs_x, obs_y in measurement:
                # Check if observation matches map at this particle's position
                # Transform observation to map coordinates based on particle pose
                map_x = int(particle.x + (obs_x - particle.x))
                map_y = int(particle.y + (obs_y - particle.y))

                if 0 <= map_x < self.width and 0 <= map_y < self.height:
                    prob = occupancy_grid.get_probability(map_x, map_y)
                    likelihood += prob

            # Update weight (with small epsilon to avoid zero)
            particle.weight = likelihood + 1e-10

        # Normalize weights
        total_weight = sum(p.weight for p in self.particles)
        if total_weight > 0:
            for particle in self.particles:
                particle.weight /= total_weight

    def resample(self):
        """Resample particles based on weights (low variance resampling)"""
        new_particles = []

        # Low variance resampling
        r = np.random.uniform(0, 1.0 / self.num_particles)
        c = self.particles[0].weight
        i = 0

        for m in range(self.num_particles):
            u = r + m * (1.0 / self.num_particles)

            while u > c:
                i += 1
                if i >= len(self.particles):
                    i = 0
                c += self.particles[i].weight

            # Copy particle (add small noise to avoid particle depletion)
            new_particle = Particle(
                x=self.particles[i].x + np.random.normal(0, 0.1),
                y=self.particles[i].y + np.random.normal(0, 0.1),
                theta=self.particles[i].theta + np.random.normal(0, 0.01),
                weight=1.0 / self.num_particles
            )

            new_particles.append(new_particle)

        self.particles = new_particles

    def get_estimated_pose(self) -> Tuple[float, float, float]:
        """
        Get estimated robot pose (weighted average)

        Returns:
            Tuple of (x, y, theta)
        """
        x = sum(p.x * p.weight for p in self.particles)
        y = sum(p.y * p.weight for p in self.particles)

        # Circular mean for theta
        sin_sum = sum(np.sin(p.theta) * p.weight for p in self.particles)
        cos_sum = sum(np.cos(p.theta) * p.weight for p in self.particles)
        theta = np.arctan2(sin_sum, cos_sum)

        return (x, y, theta)


class SLAM:
    """
    Complete SLAM system combining mapping and localization
    """

    def __init__(
        self,
        width: int,
        height: int,
        resolution: float = 0.05,
        num_particles: int = 100
    ):
        """
        Initialize SLAM system

        Args:
            width: Map width in cells
            height: Map height in cells
            resolution: Cell size in meters
            num_particles: Number of particles for localization
        """
        self.occupancy_grid = OccupancyGrid(width, height, resolution)
        self.particle_filter = ParticleFilter(num_particles, width, height)

        self.estimated_pose = (width / 2, height / 2, 0.0)

        logger.info(f"SLAM initialized: {width}x{height} map, {num_particles} particles")

    def update(
        self,
        delta_x: float,
        delta_y: float,
        delta_theta: float,
        sensor_data: List[Tuple[int, int]]
    ):
        """
        Update SLAM with motion and sensor data

        Args:
            delta_x: Change in x position
            delta_y: Change in y position
            delta_theta: Change in orientation
            sensor_data: List of obstacle points from sensors
        """
        # Prediction step
        self.particle_filter.predict(delta_x, delta_y, delta_theta)

        # Update map with sensor data
        robot_x, robot_y, _ = self.estimated_pose
        self.occupancy_grid.update_from_scan(
            int(robot_x),
            int(robot_y),
            sensor_data
        )

        # Update particle weights based on observations
        self.particle_filter.update(sensor_data, self.occupancy_grid)

        # Resample particles
        self.particle_filter.resample()

        # Update estimated pose
        self.estimated_pose = self.particle_filter.get_estimated_pose()

    def get_map(self) -> np.ndarray:
        """Get current map estimate"""
        return self.occupancy_grid.get_map_array()

    def get_pose(self) -> Tuple[float, float, float]:
        """Get estimated robot pose"""
        return self.estimated_pose

    def get_particles(self) -> List[Particle]:
        """Get current particles for visualization"""
        return self.particle_filter.particles

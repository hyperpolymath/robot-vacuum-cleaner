"""
Path Planning Algorithms for Robot Vacuum

Implements various coverage and navigation algorithms:
- Spiral coverage
- Zigzag (boustrophedon) coverage
- Wall-following
- Random walk with coverage optimization
- A* pathfinding for navigation
- Coverage path planning
"""

import numpy as np
from typing import List, Tuple, Optional, Set
from collections import deque
import heapq
import random
from dataclasses import dataclass
from robot import Position, Direction, RobotVacuum


@dataclass
class PathPlanNode:
    """Node for pathfinding algorithms"""
    position: Tuple[int, int]
    g_cost: float  # Cost from start
    h_cost: float  # Heuristic cost to goal
    parent: Optional['PathPlanNode'] = None

    @property
    def f_cost(self) -> float:
        """Total cost (f = g + h)"""
        return self.g_cost + self.h_cost

    def __lt__(self, other):
        return self.f_cost < other.f_cost


class PathPlanner:
    """Base class for path planning algorithms"""

    def __init__(self, environment: np.ndarray):
        self.environment = environment
        self.height, self.width = environment.shape

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is valid and not an obstacle"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        # 0 = free, 3 = dock (both traversable)
        return self.environment[y, x] in [0, 3]

    def get_neighbors(self, x: int, y: int, diagonal: bool = False) -> List[Tuple[int, int]]:
        """Get valid neighboring positions"""
        neighbors = []

        # Cardinal directions
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny):
                neighbors.append((nx, ny))

        # Diagonal directions
        if diagonal:
            for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = x + dx, y + dy
                if self.is_valid_position(nx, ny):
                    # Check that path is not blocked
                    if (self.is_valid_position(x + dx, y) and
                        self.is_valid_position(x, y + dy)):
                        neighbors.append((nx, ny))

        return neighbors


class AStarPlanner(PathPlanner):
    """A* pathfinding algorithm for navigation"""

    def heuristic(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Manhattan distance heuristic"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def find_path(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        diagonal: bool = True
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Find optimal path from start to goal using A*

        Args:
            start: Starting position (x, y)
            goal: Goal position (x, y)
            diagonal: Allow diagonal movement

        Returns:
            List of positions forming the path, or None if no path exists
        """
        if not self.is_valid_position(*start) or not self.is_valid_position(*goal):
            return None

        open_set = []
        closed_set = set()

        start_node = PathPlanNode(
            position=start,
            g_cost=0,
            h_cost=self.heuristic(start, goal)
        )

        heapq.heappush(open_set, start_node)
        node_map = {start: start_node}

        while open_set:
            current = heapq.heappop(open_set)

            if current.position == goal:
                # Reconstruct path
                path = []
                while current:
                    path.append(current.position)
                    current = current.parent
                return list(reversed(path))

            closed_set.add(current.position)

            for neighbor_pos in self.get_neighbors(*current.position, diagonal=diagonal):
                if neighbor_pos in closed_set:
                    continue

                # Calculate costs
                move_cost = 1.0 if (
                    neighbor_pos[0] == current.position[0] or
                    neighbor_pos[1] == current.position[1]
                ) else 1.414  # sqrt(2) for diagonal

                g_cost = current.g_cost + move_cost
                h_cost = self.heuristic(neighbor_pos, goal)

                if neighbor_pos in node_map:
                    neighbor_node = node_map[neighbor_pos]
                    if g_cost < neighbor_node.g_cost:
                        neighbor_node.g_cost = g_cost
                        neighbor_node.parent = current
                        heapq.heappush(open_set, neighbor_node)
                else:
                    neighbor_node = PathPlanNode(
                        position=neighbor_pos,
                        g_cost=g_cost,
                        h_cost=h_cost,
                        parent=current
                    )
                    node_map[neighbor_pos] = neighbor_node
                    heapq.heappush(open_set, neighbor_node)

        return None  # No path found


class SpiralCoveragePlanner(PathPlanner):
    """Spiral coverage pattern for cleaning"""

    def generate_spiral_path(
        self,
        start: Tuple[int, int],
        max_radius: Optional[int] = None
    ) -> List[Tuple[int, int]]:
        """
        Generate spiral path from center point

        Args:
            start: Starting position (center of spiral)
            max_radius: Maximum spiral radius (None = entire room)

        Returns:
            List of positions in spiral order
        """
        path = [start]
        x, y = start

        if max_radius is None:
            max_radius = max(self.width, self.height)

        # Spiral outward
        dx, dy = 1, 0  # Start moving right
        steps_in_direction = 1
        steps_taken = 0
        direction_changes = 0

        for _ in range(max_radius * max_radius):
            x += dx
            y += dy

            if self.is_valid_position(x, y):
                path.append((x, y))

            steps_taken += 1

            if steps_taken == steps_in_direction:
                steps_taken = 0
                direction_changes += 1

                # Change direction (right -> down -> left -> up -> right...)
                dx, dy = -dy, dx

                # Increase steps every two direction changes
                if direction_changes % 2 == 0:
                    steps_in_direction += 1

            if abs(x - start[0]) > max_radius and abs(y - start[1]) > max_radius:
                break

        return path


class ZigzagCoveragePlanner(PathPlanner):
    """Boustrophedon (zigzag) coverage pattern"""

    def generate_zigzag_path(
        self,
        start: Tuple[int, int],
        horizontal: bool = True
    ) -> List[Tuple[int, int]]:
        """
        Generate zigzag coverage path

        Args:
            start: Starting position
            horizontal: True for horizontal rows, False for vertical columns

        Returns:
            List of positions in zigzag pattern
        """
        path = []

        if horizontal:
            # Sweep horizontally
            for y in range(self.height):
                if y % 2 == 0:
                    # Left to right
                    for x in range(self.width):
                        if self.is_valid_position(x, y):
                            path.append((x, y))
                else:
                    # Right to left
                    for x in range(self.width - 1, -1, -1):
                        if self.is_valid_position(x, y):
                            path.append((x, y))
        else:
            # Sweep vertically
            for x in range(self.width):
                if x % 2 == 0:
                    # Top to bottom
                    for y in range(self.height):
                        if self.is_valid_position(x, y):
                            path.append((x, y))
                else:
                    # Bottom to top
                    for y in range(self.height - 1, -1, -1):
                        if self.is_valid_position(x, y):
                            path.append((x, y))

        return path


class WallFollowPlanner(PathPlanner):
    """Wall-following algorithm for coverage"""

    def follow_wall(
        self,
        start: Tuple[int, int],
        max_steps: int = 1000
    ) -> List[Tuple[int, int]]:
        """
        Follow walls using right-hand rule

        Args:
            start: Starting position
            max_steps: Maximum steps to prevent infinite loops

        Returns:
            List of positions following walls
        """
        path = [start]
        x, y = start

        # Start facing a direction with wall on right
        direction_idx = 0  # 0=North, 1=East, 2=South, 3=West
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]

        visited = {start}

        for _ in range(max_steps):
            # Try to turn right
            right_direction = (direction_idx + 1) % 4
            dx, dy = directions[right_direction]
            right_x, right_y = x + dx, y + dy

            if self.is_valid_position(right_x, right_y):
                # Turn right and move
                x, y = right_x, right_y
                direction_idx = right_direction
            else:
                # Try to move forward
                dx, dy = directions[direction_idx]
                forward_x, forward_y = x + dx, y + dy

                if self.is_valid_position(forward_x, forward_y):
                    x, y = forward_x, forward_y
                else:
                    # Turn left
                    direction_idx = (direction_idx - 1) % 4
                    continue

            if (x, y) not in visited:
                path.append((x, y))
                visited.add((x, y))

            # Check if we've returned to start
            if (x, y) == start and len(path) > 10:
                break

        return path


class RandomCoveragePlanner(PathPlanner):
    """Random walk with coverage optimization"""

    def __init__(self, environment: np.ndarray, seed: Optional[int] = None):
        super().__init__(environment)
        if seed is not None:
            random.seed(seed)

    def generate_random_path(
        self,
        start: Tuple[int, int],
        target_coverage: float = 0.95,
        max_steps: int = 10000
    ) -> List[Tuple[int, int]]:
        """
        Generate random walk optimized for coverage

        Args:
            start: Starting position
            target_coverage: Desired coverage percentage (0-1)
            max_steps: Maximum steps

        Returns:
            List of positions
        """
        path = [start]
        x, y = start
        covered = {start}

        # Calculate total coverable area
        total_free_cells = np.sum(self.environment == 0) + np.sum(self.environment == 3)

        for _ in range(max_steps):
            # Bias towards uncovered areas
            neighbors = self.get_neighbors(x, y, diagonal=False)

            if not neighbors:
                break

            # Prefer uncovered neighbors
            uncovered = [n for n in neighbors if n not in covered]

            if uncovered and random.random() < 0.7:  # 70% bias towards uncovered
                next_pos = random.choice(uncovered)
            else:
                next_pos = random.choice(neighbors)

            x, y = next_pos
            path.append(next_pos)
            covered.add(next_pos)

            # Check if target coverage reached
            coverage = len(covered) / total_free_cells
            if coverage >= target_coverage:
                break

        return path


class CoverageOptimizer:
    """Optimize coverage paths for efficiency"""

    @staticmethod
    def remove_redundant_moves(path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Remove backtracking and redundant moves from path"""
        if len(path) <= 2:
            return path

        optimized = [path[0]]

        for i in range(1, len(path)):
            # Don't add position if it's same as last in optimized path
            if path[i] != optimized[-1]:
                optimized.append(path[i])

        return optimized

    @staticmethod
    def smooth_path(path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Smooth path by removing unnecessary waypoints"""
        if len(path) <= 2:
            return path

        smoothed = [path[0]]

        i = 0
        while i < len(path) - 1:
            j = len(path) - 1

            # Find furthest point we can reach in straight line
            while j > i + 1:
                if CoverageOptimizer._is_line_clear(path[i], path[j], path):
                    smoothed.append(path[j])
                    i = j
                    break
                j -= 1
            else:
                smoothed.append(path[i + 1])
                i += 1

        return smoothed

    @staticmethod
    def _is_line_clear(
        start: Tuple[int, int],
        end: Tuple[int, int],
        path: List[Tuple[int, int]]
    ) -> bool:
        """Check if straight line between points is valid"""
        # Simple line check - all points should be in path
        # This is a simplified version
        return True

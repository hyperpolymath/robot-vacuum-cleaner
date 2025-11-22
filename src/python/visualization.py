"""
Visualization Module for Robot Vacuum Cleaner

Provides real-time and post-simulation visualization of robot behavior,
environment maps, path planning, and SLAM data.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
from matplotlib import colors
from typing import Optional, List, Tuple
import logging

from environment import Environment, CellType
from robot import RobotVacuum
from simulator import SimulationController

logger = logging.getLogger(__name__)


class Visualizer:
    """
    Main visualization class for robot vacuum simulation
    """

    def __init__(self, figsize: Tuple[int, int] = (15, 10)):
        """
        Initialize visualizer

        Args:
            figsize: Figure size in inches
        """
        self.figsize = figsize
        self.fig = None
        self.axes = None

        # Color schemes
        self.env_cmap = colors.ListedColormap([
            '#FFFFFF',  # Free space - white
            '#333333',  # Obstacle - dark gray
            '#FF6B6B',  # Cliff - red
            '#4ECDC4',  # Dock - cyan
        ])

        self.coverage_cmap = colors.ListedColormap([
            '#FFEEEE',  # Dirty - light red
            '#CCFFCC',  # Clean - light green
        ])

    def create_figure(self, num_subplots: int = 4) -> None:
        """
        Create matplotlib figure with subplots

        Args:
            num_subplots: Number of subplots (2 or 4)
        """
        if num_subplots == 2:
            self.fig, self.axes = plt.subplots(1, 2, figsize=self.figsize)
        elif num_subplots == 4:
            self.fig, self.axes = plt.subplots(2, 2, figsize=self.figsize)
            self.axes = self.axes.flatten()
        else:
            self.fig, self.axes = plt.subplots(figsize=self.figsize)
            self.axes = [self.axes]

        plt.tight_layout()

    def visualize_environment(
        self,
        environment: Environment,
        ax: Optional[plt.Axes] = None,
        title: str = "Environment Map"
    ) -> plt.Axes:
        """
        Visualize the environment

        Args:
            environment: Environment to visualize
            ax: Matplotlib axes (creates new if None)
            title: Plot title

        Returns:
            Axes object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 10))

        # Display environment
        im = ax.imshow(environment.env, cmap=self.env_cmap, vmin=0, vmax=3)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_ticks([0.375, 1.125, 1.875, 2.625])
        cbar.set_ticklabels(['Free', 'Obstacle', 'Cliff', 'Dock'])

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.grid(True, alpha=0.3)

        return ax

    def visualize_coverage(
        self,
        environment: Environment,
        robot: RobotVacuum,
        ax: Optional[plt.Axes] = None,
        title: str = "Cleaning Coverage"
    ) -> plt.Axes:
        """
        Visualize cleaning coverage

        Args:
            environment: Environment
            robot: Robot with cleaning data
            ax: Matplotlib axes
            title: Plot title

        Returns:
            Axes object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 10))

        # Create coverage map
        coverage_map = np.ones_like(environment.env)

        # Mark cleaned cells
        for x, y in robot.cleaned_cells:
            if 0 <= y < environment.height and 0 <= x < environment.width:
                coverage_map[y, x] = 0

        # Mask obstacles
        masked_coverage = np.ma.masked_where(
            environment.env == CellType.OBSTACLE.value,
            coverage_map
        )

        # Display coverage
        im = ax.imshow(masked_coverage, cmap=self.coverage_cmap, vmin=0, vmax=1, alpha=0.7)

        # Overlay environment boundaries
        ax.imshow(
            environment.env == CellType.OBSTACLE.value,
            cmap='gray',
            alpha=0.3
        )

        # Plot robot position
        ax.plot(
            robot.position.x,
            robot.position.y,
            'ro',
            markersize=15,
            label='Robot',
            markeredgecolor='black',
            markeredgewidth=2
        )

        # Plot dock if available
        if robot.dock_position:
            ax.plot(
                robot.dock_position.x,
                robot.dock_position.y,
                'cs',
                markersize=15,
                label='Dock',
                markeredgecolor='black',
                markeredgewidth=2
            )

        # Calculate and display coverage percentage
        coverage_pct = environment.get_cleaning_percentage()
        ax.text(
            0.02, 0.98,
            f'Coverage: {coverage_pct:.1f}%',
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=12,
            fontweight='bold'
        )

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

        return ax

    def visualize_path(
        self,
        environment: Environment,
        robot: RobotVacuum,
        current_path: Optional[List[Tuple[int, int]]] = None,
        ax: Optional[plt.Axes] = None,
        title: str = "Robot Path"
    ) -> plt.Axes:
        """
        Visualize robot path and trajectory

        Args:
            environment: Environment
            robot: Robot with path history
            current_path: Current planned path
            ax: Matplotlib axes
            title: Plot title

        Returns:
            Axes object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 10))

        # Display environment as background
        ax.imshow(environment.env, cmap='gray', alpha=0.3)

        # Plot historical path
        if robot.path_history:
            path_x = [p.x for p in robot.path_history]
            path_y = [p.y for p in robot.path_history]

            ax.plot(
                path_x, path_y,
                'b-',
                linewidth=2,
                alpha=0.6,
                label='Historical Path'
            )

        # Plot current planned path
        if current_path:
            plan_x = [p[0] for p in current_path]
            plan_y = [p[1] for p in current_path]

            ax.plot(
                plan_x, plan_y,
                'g--',
                linewidth=2,
                alpha=0.6,
                label='Planned Path'
            )

        # Plot robot position
        ax.plot(
            robot.position.x,
            robot.position.y,
            'ro',
            markersize=15,
            label='Robot',
            markeredgecolor='black',
            markeredgewidth=2,
            zorder=5
        )

        # Plot dock
        if robot.dock_position:
            ax.plot(
                robot.dock_position.x,
                robot.dock_position.y,
                'cs',
                markersize=15,
                label='Dock',
                markeredgecolor='black',
                markeredgewidth=2,
                zorder=5
            )

        # Display statistics
        stats_text = (
            f'Distance: {robot.stats.total_distance:.1f}m\n'
            f'Battery: {robot.battery_level:.1f}%\n'
            f'State: {robot.state.value}'
        )

        ax.text(
            0.02, 0.98,
            stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=10
        )

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

        return ax

    def visualize_slam(
        self,
        slam_map: np.ndarray,
        particles: Optional[List[Tuple[float, float]]] = None,
        robot_pose: Optional[Tuple[float, float, float]] = None,
        ax: Optional[plt.Axes] = None,
        title: str = "SLAM Map"
    ) -> plt.Axes:
        """
        Visualize SLAM mapping and localization

        Args:
            slam_map: Occupancy grid map
            particles: List of particle positions
            robot_pose: Estimated robot pose (x, y, theta)
            ax: Matplotlib axes
            title: Plot title

        Returns:
            Axes object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 10))

        # Create custom colormap for SLAM
        slam_cmap = colors.ListedColormap([
            '#FFFFFF',  # Free
            '#000000',  # Occupied
            '#CCCCCC',  # Unknown
        ])

        # Display SLAM map
        display_map = slam_map.copy()
        display_map[display_map == -1] = 2  # Unknown

        im = ax.imshow(display_map, cmap=slam_cmap, vmin=0, vmax=2)

        # Plot particles if available
        if particles:
            particles_x = [p[0] for p in particles]
            particles_y = [p[1] for p in particles]

            ax.scatter(
                particles_x, particles_y,
                c='red',
                s=20,
                alpha=0.3,
                label='Particles'
            )

        # Plot estimated robot pose
        if robot_pose:
            x, y, theta = robot_pose

            # Plot position
            ax.plot(x, y, 'bo', markersize=12, label='Estimated Pose', zorder=5)

            # Plot orientation
            dx = np.cos(theta) * 3
            dy = np.sin(theta) * 3
            ax.arrow(
                x, y, dx, dy,
                head_width=1.5,
                head_length=2,
                fc='blue',
                ec='blue',
                linewidth=2,
                zorder=5
            )

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_ticks([0.33, 1, 1.67])
        cbar.set_ticklabels(['Free', 'Occupied', 'Unknown'])

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

        return ax

    def visualize_simulation_state(
        self,
        sim: SimulationController,
        save_path: Optional[str] = None
    ) -> None:
        """
        Create comprehensive visualization of simulation state

        Args:
            sim: Simulation controller
            save_path: Path to save figure (None = show)
        """
        self.create_figure(num_subplots=4)

        # 1. Environment
        self.visualize_environment(
            sim.environment,
            ax=self.axes[0],
            title="Environment"
        )

        # 2. Coverage
        self.visualize_coverage(
            sim.environment,
            sim.robot,
            ax=self.axes[1],
            title=f"Coverage: {sim.environment.get_cleaning_percentage():.1f}%"
        )

        # 3. Path
        self.visualize_path(
            sim.environment,
            sim.robot,
            current_path=sim.current_path,
            ax=self.axes[2],
            title="Robot Path"
        )

        # 4. SLAM (if available)
        if sim.slam:
            slam_map = sim.slam.get_map()
            particles = [(p.x, p.y) for p in sim.slam.get_particles()[:50]]
            pose = sim.slam.get_pose()

            self.visualize_slam(
                slam_map,
                particles=particles,
                robot_pose=pose,
                ax=self.axes[3],
                title="SLAM Map"
            )
        else:
            # Show statistics instead
            self.plot_statistics(sim, ax=self.axes[3])

        plt.suptitle(
            f'Robot Vacuum Simulation - Step {sim.steps}',
            fontsize=16,
            fontweight='bold',
            y=1.00
        )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Visualization saved to {save_path}")
        else:
            plt.show()

    def plot_statistics(
        self,
        sim: SimulationController,
        ax: Optional[plt.Axes] = None
    ) -> plt.Axes:
        """
        Plot simulation statistics as text

        Args:
            sim: Simulation controller
            ax: Matplotlib axes

        Returns:
            Axes object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 10))

        ax.axis('off')

        stats = sim.get_results()

        stats_text = f"""
        SIMULATION STATISTICS
        ══════════════════════════════

        Steps: {stats['steps']}
        Success: {stats['success']}

        ROBOT STATUS
        ────────────────────────────────
        Position: ({sim.robot.position.x:.1f}, {sim.robot.position.y:.1f})
        Battery: {sim.robot.battery_level:.1f}%
        State: {sim.robot.state.value}
        Mode: {sim.robot.mode.value}

        PERFORMANCE
        ────────────────────────────────
        Coverage: {stats['cleaning_coverage']:.2f}%
        Distance: {stats['robot']['stats']['total_distance']:.2f}m
        Area Cleaned: {stats['robot']['stats']['area_cleaned']} cells
        Battery Cycles: {stats['robot']['stats']['battery_cycles']}

        ISSUES
        ────────────────────────────────
        Errors: {stats['robot']['stats']['errors']}
        Times Stuck: {stats['robot']['stats']['stuck_count']}

        ENVIRONMENT
        ────────────────────────────────
        Size: {stats['environment']['width']}x{stats['environment']['height']}
        Free Cells: {stats['environment']['free_cells']}
        Obstacles: {stats['environment']['obstacles']}
        """

        ax.text(
            0.1, 0.5,
            stats_text,
            transform=ax.transAxes,
            fontfamily='monospace',
            fontsize=11,
            verticalalignment='center'
        )

        ax.set_title("Statistics", fontsize=14, fontweight='bold')

        return ax


def quick_visualize(sim: SimulationController, save_path: Optional[str] = None) -> None:
    """
    Quick visualization function

    Args:
        sim: Simulation controller
        save_path: Optional path to save figure
    """
    viz = Visualizer()
    viz.visualize_simulation_state(sim, save_path=save_path)


if __name__ == "__main__":
    # Example usage
    from simulator import SimulationConfig, run_simulation

    # Run simulation
    config = SimulationConfig(
        room_type='furnished',
        cleaning_mode='zigzag',
        max_steps=1000,
        enable_slam=True,
        random_seed=42
    )

    from simulator import SimulationController
    sim = SimulationController(config)

    # Run for a while
    for _ in range(500):
        if not sim.step():
            break

    # Visualize
    quick_visualize(sim)

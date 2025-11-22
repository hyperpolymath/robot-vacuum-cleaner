"""
GraphQL Server Implementation

FastAPI + Strawberry GraphQL server for robot vacuum control and monitoring.
"""

import asyncio
import time
from typing import Optional, List, AsyncGenerator
from datetime import datetime
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))

from simulator import SimulationController, SimulationConfig
from robot import RobotState as PyRobotState, CleaningMode as PyCleaningMode


# Global simulation instance
_simulation: Optional[SimulationController] = None
_start_time = time.time()


# GraphQL Types
@strawberry.type
class Position:
    x: float
    y: float


@strawberry.enum
class RobotState(strawberry.enum.EnumMeta):
    IDLE = "idle"
    CLEANING = "cleaning"
    RETURNING_TO_DOCK = "returning_to_dock"
    CHARGING = "charging"
    ERROR = "error"
    STUCK = "stuck"


@strawberry.enum
class CleaningMode(strawberry.enum.EnumMeta):
    AUTO = "auto"
    SPOT = "spot"
    EDGE = "edge"
    SPIRAL = "spiral"
    ZIGZAG = "zigzag"
    WALL_FOLLOW = "wall_follow"
    RANDOM = "random"


@strawberry.type
class SensorData:
    obstacle_front: bool
    obstacle_left: bool
    obstacle_right: bool
    obstacle_back: bool
    cliff_detected: bool
    bumper_triggered: bool
    distance_front: float
    distance_left: float
    distance_right: float
    distance_back: float


@strawberry.type
class RobotStats:
    total_distance: float
    area_cleaned: int
    cleaning_time: float
    battery_cycles: int
    errors_encountered: int
    stuck_count: int


@strawberry.type
class RobotStatus:
    position: Position
    battery_level: float
    state: str
    mode: str
    heading: float
    sensors: SensorData
    stats: RobotStats
    timestamp: str


@strawberry.type
class EnvironmentInfo:
    width: int
    height: int
    total_area: int
    free_cells: int
    obstacles: int
    cleaning_percentage: float
    sim_time: float
    dock_position: Optional[Position]
    room_type: str


@strawberry.type
class Statistics:
    steps: int
    success: bool
    cleaning_coverage: float
    total_distance: float
    battery_cycles: int
    errors: int
    stuck_count: int


@strawberry.type
class Pose:
    x: float
    y: float
    theta: float


@strawberry.type
class Particle:
    x: float
    y: float
    theta: float
    weight: float


@strawberry.type
class SlamData:
    estimated_pose: Pose
    map_width: int
    map_height: int
    particles: List[Particle]


@strawberry.type
class CoverageMap:
    width: int
    height: int
    coverage_percentage: float
    cleaned_cells_count: int


@strawberry.type
class PathInfo:
    current_path: List[Position]
    path_history: List[Position]
    path_index: int
    path_length: int


@strawberry.type
class OperationResult:
    success: bool
    message: str
    error: Optional[str] = None


@strawberry.type
class SimulationState:
    step: int
    robot: RobotStatus
    environment: EnvironmentInfo
    cleaning_percentage: float


@strawberry.type
class StepResult:
    success: bool
    should_continue: bool
    state: SimulationState
    message: Optional[str] = None


@strawberry.type
class CleaningProgress:
    percentage: float
    area_cleaned: int
    battery_level: float
    state: str
    timestamp: str


@strawberry.type
class SimulationStep:
    step: int
    position: Position
    battery_level: float
    cleaning_percentage: float


@strawberry.type
class HealthCheck:
    status: str
    version: str
    uptime: float
    simulation_active: bool


@strawberry.input
class SimulationConfigInput:
    room_type: Optional[str] = "furnished"
    cleaning_mode: Optional[str] = "auto"
    max_steps: Optional[int] = 10000
    enable_slam: Optional[bool] = True
    random_seed: Optional[int] = None


# Helper functions
def _get_simulation() -> SimulationController:
    """Get or create simulation instance"""
    global _simulation

    if _simulation is None:
        config = SimulationConfig()
        _simulation = SimulationController(config)

    return _simulation


def _robot_status_from_sim(sim: SimulationController) -> RobotStatus:
    """Convert simulation robot status to GraphQL type"""
    status = sim.robot.get_status()

    return RobotStatus(
        position=Position(
            x=status['position']['x'],
            y=status['position']['y']
        ),
        battery_level=status['battery_level'],
        state=status['state'],
        mode=status['mode'],
        heading=status['heading'],
        sensors=SensorData(
            obstacle_front=status['sensors']['obstacle_front'],
            obstacle_left=status['sensors']['obstacle_left'],
            obstacle_right=status['sensors']['obstacle_right'],
            obstacle_back=status['sensors']['obstacle_back'],
            cliff_detected=status['sensors']['cliff_detected'],
            bumper_triggered=status['sensors']['bumper_triggered'],
            distance_front=sim.robot.sensor_data.distance_front,
            distance_left=sim.robot.sensor_data.distance_left,
            distance_right=sim.robot.sensor_data.distance_right,
            distance_back=sim.robot.sensor_data.distance_back
        ),
        stats=RobotStats(
            total_distance=status['stats']['total_distance'],
            area_cleaned=status['stats']['area_cleaned'],
            cleaning_time=status['stats']['cleaning_time'],
            battery_cycles=status['stats']['battery_cycles'],
            errors_encountered=status['stats']['errors'],
            stuck_count=status['stats']['stuck_count']
        ),
        timestamp=datetime.now().isoformat()
    )


def _environment_info_from_sim(sim: SimulationController) -> EnvironmentInfo:
    """Convert simulation environment to GraphQL type"""
    stats = sim.environment.get_statistics()

    dock_pos = None
    if stats['dock_position']:
        dock_pos = Position(x=stats['dock_position'][0], y=stats['dock_position'][1])

    return EnvironmentInfo(
        width=stats['width'],
        height=stats['height'],
        total_area=stats['total_area'],
        free_cells=stats['free_cells'],
        obstacles=stats['obstacles'],
        cleaning_percentage=stats['cleaning_percentage'],
        sim_time=stats['sim_time'],
        dock_position=dock_pos,
        room_type=sim.config.room_type
    )


# Query resolvers
@strawberry.type
class Query:
    @strawberry.field
    def robot_status(self) -> RobotStatus:
        """Get current robot status"""
        sim = _get_simulation()
        return _robot_status_from_sim(sim)

    @strawberry.field
    def environment(self) -> EnvironmentInfo:
        """Get environment information"""
        sim = _get_simulation()
        return _environment_info_from_sim(sim)

    @strawberry.field
    def statistics(self) -> Statistics:
        """Get simulation statistics"""
        sim = _get_simulation()
        results = sim.get_results()

        return Statistics(
            steps=results['steps'],
            success=results['success'],
            cleaning_coverage=results['cleaning_coverage'],
            total_distance=results['robot']['stats']['total_distance'],
            battery_cycles=results['robot']['stats']['battery_cycles'],
            errors=results['robot']['stats']['errors'],
            stuck_count=results['robot']['stats']['stuck_count']
        )

    @strawberry.field
    def slam_data(self) -> Optional[SlamData]:
        """Get SLAM data (if enabled)"""
        sim = _get_simulation()

        if sim.slam is None:
            return None

        pose = sim.slam.get_pose()
        particles = sim.slam.get_particles()[:20]  # Sample

        return SlamData(
            estimated_pose=Pose(x=pose[0], y=pose[1], theta=pose[2]),
            map_width=sim.slam.occupancy_grid.width,
            map_height=sim.slam.occupancy_grid.height,
            particles=[
                Particle(x=p.x, y=p.y, theta=p.theta, weight=p.weight)
                for p in particles
            ]
        )

    @strawberry.field
    def coverage_map(self) -> CoverageMap:
        """Get cleaning coverage map"""
        sim = _get_simulation()

        return CoverageMap(
            width=sim.environment.width,
            height=sim.environment.height,
            coverage_percentage=sim.environment.get_cleaning_percentage(),
            cleaned_cells_count=len(sim.robot.cleaned_cells)
        )

    @strawberry.field
    def available_cleaning_modes(self) -> List[str]:
        """Get available cleaning modes"""
        return ["auto", "spot", "edge", "spiral", "zigzag", "wall_follow", "random"]

    @strawberry.field
    def available_room_types(self) -> List[str]:
        """Get available room types"""
        return ["empty", "furnished", "multi_room", "corridor", "obstacle_course", "stairs_test"]

    @strawberry.field
    def path_info(self) -> Optional[PathInfo]:
        """Get path planning information"""
        sim = _get_simulation()

        if not sim.current_path:
            return None

        return PathInfo(
            current_path=[
                Position(x=float(p[0]), y=float(p[1]))
                for p in sim.current_path[sim.path_index:sim.path_index+50]
            ],
            path_history=[
                Position(x=p.x, y=p.y)
                for p in sim.robot.path_history[-100:]
            ],
            path_index=sim.path_index,
            path_length=len(sim.current_path)
        )

    @strawberry.field
    def health(self) -> HealthCheck:
        """Health check"""
        global _simulation, _start_time

        return HealthCheck(
            status="healthy",
            version="1.0.0",
            uptime=time.time() - _start_time,
            simulation_active=_simulation is not None
        )


# Mutation resolvers
@strawberry.type
class Mutation:
    @strawberry.mutation
    def start_cleaning(self, mode: Optional[str] = None) -> OperationResult:
        """Start cleaning operation"""
        try:
            sim = _get_simulation()

            if mode:
                sim.robot.mode = PyCleaningMode(mode)

            sim.robot.state = PyRobotState.CLEANING

            return OperationResult(
                success=True,
                message=f"Cleaning started in {mode or 'auto'} mode"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to start cleaning",
                error=str(e)
            )

    @strawberry.mutation
    def stop_cleaning(self) -> OperationResult:
        """Stop cleaning operation"""
        try:
            sim = _get_simulation()
            sim.robot.state = PyRobotState.IDLE

            return OperationResult(
                success=True,
                message="Cleaning stopped"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to stop cleaning",
                error=str(e)
            )

    @strawberry.mutation
    def return_to_dock(self) -> OperationResult:
        """Return robot to charging dock"""
        try:
            sim = _get_simulation()
            sim.robot.state = PyRobotState.RETURNING_TO_DOCK

            return OperationResult(
                success=True,
                message="Returning to dock"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to return to dock",
                error=str(e)
            )

    @strawberry.mutation
    def init_simulation(self, config: SimulationConfigInput) -> OperationResult:
        """Initialize new simulation"""
        global _simulation

        try:
            sim_config = SimulationConfig(
                room_type=config.room_type or "furnished",
                cleaning_mode=config.cleaning_mode or "auto",
                max_steps=config.max_steps or 10000,
                enable_slam=config.enable_slam if config.enable_slam is not None else True,
                random_seed=config.random_seed
            )

            _simulation = SimulationController(sim_config)

            return OperationResult(
                success=True,
                message=f"Simulation initialized: {sim_config.room_type}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to initialize simulation",
                error=str(e)
            )

    @strawberry.mutation
    def step_simulation(self) -> StepResult:
        """Execute single simulation step"""
        try:
            sim = _get_simulation()
            should_continue = sim.step()

            state = SimulationState(
                step=sim.steps,
                robot=_robot_status_from_sim(sim),
                environment=_environment_info_from_sim(sim),
                cleaning_percentage=sim.environment.get_cleaning_percentage()
            )

            return StepResult(
                success=True,
                should_continue=should_continue,
                state=state,
                message=f"Step {sim.steps} completed"
            )
        except Exception as e:
            sim = _get_simulation()
            state = SimulationState(
                step=sim.steps,
                robot=_robot_status_from_sim(sim),
                environment=_environment_info_from_sim(sim),
                cleaning_percentage=sim.environment.get_cleaning_percentage()
            )

            return StepResult(
                success=False,
                should_continue=False,
                state=state,
                message=f"Step failed: {str(e)}"
            )

    @strawberry.mutation
    def reset_simulation(self) -> OperationResult:
        """Reset simulation"""
        global _simulation

        try:
            _simulation = None
            return OperationResult(
                success=True,
                message="Simulation reset"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to reset simulation",
                error=str(e)
            )


# Subscription resolvers
@strawberry.type
class Subscription:
    @strawberry.subscription
    async def robot_status_updates(self, interval: int = 1) -> AsyncGenerator[RobotStatus, None]:
        """Subscribe to robot status updates"""
        while True:
            sim = _get_simulation()
            yield _robot_status_from_sim(sim)
            await asyncio.sleep(interval)

    @strawberry.subscription
    async def cleaning_progress(self, interval: int = 1) -> AsyncGenerator[CleaningProgress, None]:
        """Subscribe to cleaning progress updates"""
        while True:
            sim = _get_simulation()

            yield CleaningProgress(
                percentage=sim.environment.get_cleaning_percentage(),
                area_cleaned=len(sim.robot.cleaned_cells),
                battery_level=sim.robot.battery_level,
                state=sim.robot.state.value,
                timestamp=datetime.now().isoformat()
            )

            await asyncio.sleep(interval)

    @strawberry.subscription
    async def simulation_steps(self) -> AsyncGenerator[SimulationStep, None]:
        """Subscribe to simulation steps"""
        sim = _get_simulation()

        while True:
            should_continue = sim.step()

            yield SimulationStep(
                step=sim.steps,
                position=Position(x=sim.robot.position.x, y=sim.robot.position.y),
                battery_level=sim.robot.battery_level,
                cleaning_percentage=sim.environment.get_cleaning_percentage()
            )

            if not should_continue:
                break

            await asyncio.sleep(0.1)


# Create schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)

# Create FastAPI app
app = FastAPI(
    title="Robot Vacuum Cleaner API",
    description="GraphQL API for robot vacuum cleaner control and monitoring",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GraphQL router
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Robot Vacuum Cleaner API",
        "version": "1.0.0",
        "graphql": "/graphql",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global _simulation, _start_time

    return {
        "status": "healthy",
        "uptime": time.time() - _start_time,
        "simulation_active": _simulation is not None
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

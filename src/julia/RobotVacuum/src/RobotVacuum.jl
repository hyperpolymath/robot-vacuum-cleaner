"""
    RobotVacuum

High-performance robot vacuum cleaner simulator in Julia.

Provides autonomous navigation, path planning, SLAM, and sensor simulation
for robotic vacuum cleaners.

# Examples
```julia
using RobotVacuum

# Create environment
env = create_empty_room(50, 50)

# Initialize robot
robot = Robot(Position(25.0, 25.0))

# Run simulation
config = SimulationConfig(room_type="furnished", max_steps=5000)
results = run_simulation(config)

println("Coverage: \$(results.cleaning_coverage)%")
```
"""
module RobotVacuum

using StaticArrays
using LinearAlgebra
using Statistics
using Random
using Distributions
using Logging

# Core types
export Position, Velocity, Pose, SensorData, RobotStats

# Robot
export Robot, RobotState, CleaningMode
export move_robot!, charge!, should_return_to_dock
export set_dock_position!, reset_stats!, get_status

# Environment
export Environment, CellType
export create_empty_room, create_room_with_furniture
export is_valid_position, clean_cell!, is_dirty
export get_cleaning_percentage

# Path planning
export AStarPlanner, find_path
export SpiralPlanner, generate_spiral
export ZigzagPlanner, generate_zigzag
export WallFollowPlanner, follow_wall
export RandomPlanner, generate_random_path

# SLAM
export SLAM, OccupancyGrid, ParticleFilter
export update_slam!, get_map, get_pose

# Simulation
export SimulationConfig, Simulator
export run_simulation, step!

# Include source files
include("types.jl")
include("robot.jl")
include("environment.jl")
include("pathplanning.jl")
include("slam.jl")
include("simulator.jl")

# Module initialization
function __init__()
    @info "RobotVacuum.jl v1.0.0 loaded"
end

end # module

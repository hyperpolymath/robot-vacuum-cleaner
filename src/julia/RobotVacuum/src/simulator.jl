"""
Simulation controller for robot vacuum cleaner.
"""

"""
    SimulationConfig

Configuration for simulation run.

# Fields
- `room_type::String`: Type of room to simulate
- `cleaning_mode::CleaningMode`: Cleaning mode to use
- `max_steps::Int`: Maximum simulation steps
- `enable_slam::Bool`: Enable SLAM
- `random_seed::Union{Int,Nothing}`: Random seed for reproducibility
"""
struct SimulationConfig
    room_type::String
    cleaning_mode::CleaningMode
    max_steps::Int
    enable_slam::Bool
    random_seed::Union{Int,Nothing}
end

function SimulationConfig(;
    room_type::String="furnished",
    cleaning_mode::CleaningMode=Auto,
    max_steps::Int=10000,
    enable_slam::Bool=true,
    random_seed::Union{Int,Nothing}=nothing
)
    SimulationConfig(room_type, cleaning_mode, max_steps, enable_slam, random_seed)
end

"""
    Simulator

Main simulation controller.

# Fields
- `robot::Robot`: Robot instance
- `environment::Environment`: Environment instance
- `config::SimulationConfig`: Configuration
- `steps::Int`: Current step count
- `slam::Union{SLAM,Nothing}`: SLAM system (if enabled)
"""
mutable struct Simulator
    robot::Robot
    environment::Environment
    config::SimulationConfig
    steps::Int
    slam::Union{SLAM,Nothing}
end

function Simulator(robot::Robot, environment::Environment, config::SimulationConfig)
    slam = config.enable_slam ? SLAM(environment.width, environment.height) : nothing

    Simulator(robot, environment, config, 0, slam)
end

"""
    step!(sim::Simulator) -> Bool

Execute one simulation step. Returns true if simulation should continue.
"""
function step!(sim::Simulator)::Bool
    sim.steps += 1
    step!(sim.environment)

    # Simple simulation logic
    if sim.robot.state == Idle
        sim.robot.state = Cleaning
    elseif sim.robot.state == Cleaning
        if should_return_to_dock(sim.robot)
            sim.robot.state = ReturningToDock
        end
    elseif sim.robot.state == Charging
        if charge!(sim.robot)
            sim.robot.state = Cleaning
        end
    end

    # Check max steps
    sim.steps >= sim.config.max_steps ? false : true
end

"""
    run_simulation(config::SimulationConfig) -> Dict

Run complete simulation and return results.
"""
function run_simulation(config::SimulationConfig)::Dict{String,Any}
    @info "Starting simulation"

    if !isnothing(config.random_seed)
        Random.seed!(config.random_seed)
    end

    # Create environment based on room type
    env = if config.room_type == "empty"
        create_empty_room(50, 50)
    elseif config.room_type == "furnished"
        create_room_with_furniture(50, 50, 5)
    else
        create_empty_room(50, 50)
    end

    # Find starting position (center)
    start_pos = Position(env.width / 2, env.height / 2)

    # Create robot
    robot = Robot(start_pos)
    robot.mode = config.cleaning_mode

    # Create simulator
    sim = Simulator(robot, env, config)

    # Run simulation
    while step!(sim)
        # Simulation loop
    end

    @info "Simulation complete after $(sim.steps) steps"

    # Return results
    Dict{String,Any}(
        "steps" => sim.steps,
        "cleaning_coverage" => get_cleaning_percentage(sim.environment),
        "total_distance" => sim.robot.stats.total_distance,
        "battery_cycles" => sim.robot.stats.battery_cycles,
        "success" => sim.robot.state != Error
    )
end

"""
Robot vacuum cleaner core implementation.
"""

@enum RobotState begin
    Idle
    Cleaning
    ReturningToDock
    Charging
    Error
    Stuck
end

@enum CleaningMode begin
    Auto
    Spot
    Edge
    Spiral
    Zigzag
    WallFollow
    Random
end

"""
    Robot

Robot vacuum cleaner with sensors, state management, and navigation.

# Fields
- `position::Position`: Current position
- `battery_capacity::Float64`: Maximum battery capacity
- `battery_level::Float64`: Current battery level
- `cleaning_width::Float64`: Width of cleaning path
- `speed::Float64`: Movement speed
- `sensor_range::Float64`: Sensor detection range
- `state::RobotState`: Current operational state
- `mode::CleaningMode`: Current cleaning mode
- `heading::Float64`: Current heading in radians
- `dock_position::Union{Position,Nothing}`: Charging dock location
- `sensor_data::SensorData`: Current sensor readings
- `stats::RobotStats`: Operational statistics
- `cleaned_cells::Set{Tuple{Int,Int}}`: Set of cleaned grid cells
- `visited_cells::Set{Tuple{Int,Int}}`: Set of visited grid cells
- `path_history::Vector{Position}`: Historical path
"""
mutable struct Robot
    position::Position
    battery_capacity::Float64
    battery_level::Float64
    cleaning_width::Float64
    speed::Float64
    sensor_range::Float64
    state::RobotState
    mode::CleaningMode
    heading::Float64
    dock_position::Union{Position,Nothing}
    sensor_data::SensorData
    stats::RobotStats
    cleaned_cells::Set{Tuple{Int64,Int64}}
    visited_cells::Set{Tuple{Int64,Int64}}
    path_history::Vector{Position}
end

"""
    Robot(position::Position; kwargs...) -> Robot

Create a new robot vacuum cleaner.

# Arguments
- `position::Position`: Starting position

# Keywords
- `battery_capacity::Float64=100.0`: Maximum battery
- `cleaning_width::Float64=0.3`: Cleaning path width
- `speed::Float64=0.2`: Movement speed
- `sensor_range::Float64=2.0`: Sensor range
"""
function Robot(position::Position;
               battery_capacity::Float64=100.0,
               cleaning_width::Float64=0.3,
               speed::Float64=0.2,
               sensor_range::Float64=2.0)
    Robot(
        position,
        battery_capacity,
        battery_capacity,  # Start fully charged
        cleaning_width,
        speed,
        sensor_range,
        Idle,
        Auto,
        0.0,
        nothing,
        SensorData(),
        RobotStats(),
        Set{Tuple{Int64,Int64}}(),
        Set{Tuple{Int64,Int64}}(),
        [position]
    )
end

"""
    move_robot!(robot::Robot, dx::Float64, dy::Float64) -> Bool

Move robot by given delta. Returns true if movement successful.
"""
function move_robot!(robot::Robot, dx::Float64, dy::Float64)::Bool
    if robot.battery_level <= 0.0
        robot.state = Error
        @warn "Cannot move: battery depleted"
        return false
    end

    # Update position
    robot.position = robot.position + Position(dx, dy)
    push!(robot.path_history, robot.position)

    # Update stats
    dist = sqrt(dx^2 + dy^2)
    robot.stats.total_distance += dist

    # Consume battery
    battery_consumption = dist * 0.1
    robot.battery_level = max(0.0, robot.battery_level - battery_consumption)

    # Mark cell as visited and cleaned
    grid_pos = to_grid(robot.position)
    push!(robot.visited_cells, grid_pos)
    push!(robot.cleaned_cells, grid_pos)
    robot.stats.area_cleaned = length(robot.cleaned_cells)

    true
end

"""
    should_return_to_dock(robot::Robot) -> Bool

Check if robot should return to charging dock.
"""
function should_return_to_dock(robot::Robot)::Bool
    if robot.battery_level < 20.0
        return true
    end

    if !isnothing(robot.dock_position)
        dist_to_dock = distance(robot.position, robot.dock_position)
        # Estimate battery needed with 50% safety margin
        estimated_battery_needed = dist_to_dock * 0.1 * 1.5
        if robot.battery_level < estimated_battery_needed + 10.0
            return true
        end
    end

    false
end

"""
    charge!(robot::Robot, charge_rate::Float64=10.0) -> Bool

Charge robot battery. Returns true if fully charged.
"""
function charge!(robot::Robot, charge_rate::Float64=10.0)::Bool
    if robot.state != Charging
        robot.state = Charging
    end

    robot.battery_level = min(robot.battery_capacity, robot.battery_level + charge_rate)

    if robot.battery_level >= robot.battery_capacity
        robot.stats.battery_cycles += 1
        @info "Battery fully charged"
        return true
    end

    false
end

"""
    set_dock_position!(robot::Robot, position::Position)

Set the charging dock position.
"""
function set_dock_position!(robot::Robot, position::Position)
    robot.dock_position = position
    @info "Dock position set to ($(position.x), $(position.y))"
end

"""
    reset_stats!(robot::Robot)

Reset robot operational statistics.
"""
function reset_stats!(robot::Robot)
    reset!(robot.stats)
    empty!(robot.cleaned_cells)
    empty!(robot.visited_cells)
    empty!(robot.path_history)
    push!(robot.path_history, robot.position)
    @info "Statistics reset"
end

"""
    get_status(robot::Robot) -> Dict

Get robot status as dictionary.
"""
function get_status(robot::Robot)::Dict{String,Any}
    Dict(
        "position" => Dict("x" => robot.position.x, "y" => robot.position.y),
        "battery_level" => robot.battery_level,
        "state" => string(robot.state),
        "mode" => string(robot.mode),
        "heading" => robot.heading,
        "stats" => Dict(
            "total_distance" => robot.stats.total_distance,
            "area_cleaned" => robot.stats.area_cleaned,
            "cleaning_time" => robot.stats.cleaning_time,
            "battery_cycles" => robot.stats.battery_cycles,
            "errors" => robot.stats.errors_encountered,
            "stuck_count" => robot.stats.stuck_count
        ),
        "sensors" => Dict(
            "obstacle_front" => robot.sensor_data.obstacle_front,
            "obstacle_left" => robot.sensor_data.obstacle_left,
            "obstacle_right" => robot.sensor_data.obstacle_right,
            "cliff_detected" => robot.sensor_data.cliff_detected
        )
    )
end

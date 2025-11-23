"""
Core types and data structures for robot vacuum simulation.
"""

# 2D Position
struct Position
    x::Float64
    y::Float64
end

Position() = Position(0.0, 0.0)

"""
    distance(p1::Position, p2::Position) -> Float64

Calculate Euclidean distance between two positions.
"""
function distance(p1::Position, p2::Position)::Float64
    sqrt((p1.x - p2.x)^2 + (p1.y - p2.y)^2)
end

"""
    manhattan_distance(p1::Position, p2::Position) -> Float64

Calculate Manhattan distance between two positions.
"""
function manhattan_distance(p1::Position, p2::Position)::Float64
    abs(p1.x - p2.x) + abs(p1.y - p2.y)
end

"""
    to_grid(p::Position) -> Tuple{Int, Int}

Convert position to grid coordinates.
"""
function to_grid(p::Position)::Tuple{Int64,Int64}
    (floor(Int, p.x), floor(Int, p.y))
end

# Operator overloading
Base.:+(p1::Position, p2::Position) = Position(p1.x + p2.x, p1.y + p2.y)
Base.:-(p1::Position, p2::Position) = Position(p1.x - p2.x, p1.y - p2.y)
Base.:*(p::Position, scalar::Real) = Position(p.x * scalar, p.y * scalar)

# 2D Velocity
struct Velocity
    vx::Float64
    vy::Float64
end

Velocity() = Velocity(0.0, 0.0)

"""
    magnitude(v::Velocity) -> Float64

Calculate velocity magnitude.
"""
function magnitude(v::Velocity)::Float64
    sqrt(v.vx^2 + v.vy^2)
end

"""
    normalize(v::Velocity) -> Velocity

Normalize velocity to unit vector.
"""
function Base.normalize(v::Velocity)::Velocity
    mag = magnitude(v)
    mag > 0.0 ? Velocity(v.vx / mag, v.vy / mag) : v
end

# 2D Pose (position + orientation)
struct Pose
    x::Float64
    y::Float64
    theta::Float64  # Orientation in radians
end

Pose(x, y) = Pose(x, y, 0.0)

"""
    position(pose::Pose) -> Position

Extract position from pose.
"""
position(pose::Pose) = Position(pose.x, pose.y)

"""
    distance(pose1::Pose, pose2::Pose) -> Float64

Calculate distance between two poses.
"""
function distance(pose1::Pose, pose2::Pose)::Float64
    sqrt((pose1.x - pose2.x)^2 + (pose1.y - pose2.y)^2)
end

"""
    angle_diff(pose1::Pose, pose2::Pose) -> Float64

Calculate angular difference between poses (normalized to [-π, π]).
"""
function angle_diff(pose1::Pose, pose2::Pose)::Float64
    diff = pose2.theta - pose1.theta

    # Normalize to [-π, π]
    while diff > π
        diff -= 2π
    end
    while diff < -π
        diff += 2π
    end

    diff
end

# Sensor data
mutable struct SensorData
    obstacle_front::Bool
    obstacle_left::Bool
    obstacle_right::Bool
    obstacle_back::Bool
    cliff_detected::Bool
    bumper_triggered::Bool
    distance_front::Float64
    distance_left::Float64
    distance_right::Float64
    distance_back::Float64
end

function SensorData()
    SensorData(
        false, false, false, false,  # obstacles
        false, false,                 # cliff, bumper
        Inf, Inf, Inf, Inf          # distances
    )
end

# Robot statistics
mutable struct RobotStats
    total_distance::Float64
    area_cleaned::Int
    cleaning_time::Float64
    battery_cycles::Int
    errors_encountered::Int
    stuck_count::Int
end

RobotStats() = RobotStats(0.0, 0, 0.0, 0, 0, 0)

function reset!(stats::RobotStats)
    stats.total_distance = 0.0
    stats.area_cleaned = 0
    stats.cleaning_time = 0.0
    stats.battery_cycles = 0
    stats.errors_encountered = 0
    stats.stuck_count = 0
end

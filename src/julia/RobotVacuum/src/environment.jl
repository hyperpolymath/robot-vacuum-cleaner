"""
Environment simulation for robot vacuum testing.
"""

@enum CellType::UInt8 begin
    Free = 0
    Obstacle = 1
    Cliff = 2
    Dock = 3
end

"""
    Environment

Simulation environment with grid representation and cleaning tracking.

# Fields
- `grid::Matrix{UInt8}`: Environment grid
- `width::Int`: Grid width
- `height::Int`: Grid height
- `dock_position::Union{Tuple{Int,Int},Nothing}`: Dock location
- `dirt_map::BitMatrix`: Dirty cells tracking
- `sim_time::Float64`: Simulation time elapsed
"""
mutable struct Environment
    grid::Matrix{UInt8}
    width::Int
    height::Int
    dock_position::Union{Tuple{Int,Int},Nothing}
    dirt_map::BitMatrix
    sim_time::Float64
end

"""
    Environment(width::Int, height::Int) -> Environment

Create empty environment.
"""
function Environment(width::Int, height::Int)
    grid = zeros(UInt8, height, width)
    dirt_map = trues(height, width)

    Environment(grid, width, height, nothing, dirt_map, 0.0)
end

"""
    create_empty_room(width::Int, height::Int) -> Environment

Create rectangular room with walls.
"""
function create_empty_room(width::Int, height::Int)::Environment
    env = Environment(width, height)

    # Add walls
    env.grid[1, :] .= UInt8(Obstacle)      # Top wall
    env.grid[end, :] .= UInt8(Obstacle)    # Bottom wall
    env.grid[:, 1] .= UInt8(Obstacle)      # Left wall
    env.grid[:, end] .= UInt8(Obstacle)    # Right wall

    env
end

"""
    create_room_with_furniture(width::Int, height::Int, num_obstacles::Int=5) -> Environment

Create room with random furniture obstacles.
"""
function create_room_with_furniture(width::Int, height::Int, num_obstacles::Int=5)::Environment
    env = create_empty_room(width, height)

    # Add random furniture
    for _ in 1:num_obstacles
        furn_width = rand(2:5)
        furn_height = rand(2:5)

        x = rand(5:(width - furn_width - 5))
        y = rand(5:(height - furn_height - 5))

        env.grid[y:(y+furn_height-1), x:(x+furn_width-1)] .= UInt8(Obstacle)
    end

    env
end

"""
    is_valid_position(env::Environment, x::Int, y::Int) -> Bool

Check if position is valid (not obstacle or out of bounds).
"""
function is_valid_position(env::Environment, x::Int, y::Int)::Bool
    if x < 1 || x > env.width || y < 1 || y > env.height
        return false
    end

    cell_type = CellType(env.grid[y, x])
    cell_type == Free || cell_type == Dock
end

"""
    clean_cell!(env::Environment, x::Int, y::Int)

Mark cell as cleaned.
"""
function clean_cell!(env::Environment, x::Int, y::Int)
    if 1 <= x <= env.width && 1 <= y <= env.height
        env.dirt_map[y, x] = false
    end
end

"""
    is_dirty(env::Environment, x::Int, y::Int) -> Bool

Check if cell is dirty.
"""
function is_dirty(env::Environment, x::Int, y::Int)::Bool
    if 1 <= x <= env.width && 1 <= y <= env.height
        return env.dirt_map[y, x]
    end
    false
end

"""
    get_cleaning_percentage(env::Environment) -> Float64

Calculate percentage of area cleaned.
"""
function get_cleaning_percentage(env::Environment)::Float64
    total_cleanable = count(==(UInt8(Free)), env.grid)

    if total_cleanable == 0
        return 100.0
    end

    cleaned = 0
    for i in 1:env.height, j in 1:env.width
        if env.grid[i, j] == UInt8(Free) && !env.dirt_map[i, j]
            cleaned += 1
        end
    end

    (cleaned / total_cleanable) * 100.0
end

"""
    step!(env::Environment, delta_time::Float64=0.1)

Advance simulation time.
"""
function step!(env::Environment, delta_time::Float64=0.1)
    env.sim_time += delta_time
end

"""
    reset!(env::Environment)

Reset environment to initial state.
"""
function Base.reset!(env::Environment)
    env.dirt_map .= true
    env.sim_time = 0.0
end

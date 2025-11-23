"""
Path planning algorithms for robot vacuum navigation.
"""

using DataStructures: PriorityQueue, enqueue!, dequeue!

"""
    AStarPlanner

A* pathfinding algorithm for navigation.
"""
struct AStarPlanner
    environment::Environment
end

"""
    find_path(planner::AStarPlanner, start::Tuple{Int,Int}, goal::Tuple{Int,Int}) -> Union{Vector{Tuple{Int,Int}}, Nothing}

Find optimal path from start to goal using A*.
"""
function find_path(planner::AStarPlanner, start::Tuple{Int,Int}, goal::Tuple{Int,Int})::Union{Vector{Tuple{Int,Int}},Nothing}
    if !is_valid_position(planner.environment, start[1], start[2]) ||
       !is_valid_position(planner.environment, goal[1], goal[2])
        return nothing
    end

    open_set = PriorityQueue{Tuple{Int,Int},Float64}()
    enqueue!(open_set, start, 0.0)

    came_from = Dict{Tuple{Int,Int},Tuple{Int,Int}}()
    g_score = Dict{Tuple{Int,Int},Float64}(start => 0.0)

    while !isempty(open_set)
        current = dequeue!(open_set)

        if current == goal
            # Reconstruct path
            path = Tuple{Int,Int}[]
            while current ∈ keys(came_from)
                pushfirst!(path, current)
                current = came_from[current]
            end
            pushfirst!(path, start)
            return path
        end

        for neighbor in get_neighbors(planner.environment, current)
            tentative_g = get(g_score, current, Inf) + 1.0

            if tentative_g < get(g_score, neighbor, Inf)
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                enqueue!(open_set, neighbor, f_score)
            end
        end
    end

    nothing  # No path found
end

function heuristic(pos1::Tuple{Int,Int}, pos2::Tuple{Int,Int})::Float64
    abs(pos1[1] - pos2[1]) + abs(pos1[2] - pos2[2])  # Manhattan distance
end

function get_neighbors(env::Environment, pos::Tuple{Int,Int})::Vector{Tuple{Int,Int}}
    neighbors = Tuple{Int,Int}[]
    (x, y) = pos

    for (dx, dy) in [(0, 1), (1, 0), (0, -1), (-1, 0)]
        nx, ny = x + dx, y + dy
        if is_valid_position(env, nx, ny)
            push!(neighbors, (nx, ny))
        end
    end

    neighbors
end

"""
    SpiralPlanner

Spiral coverage pattern planner.
"""
struct SpiralPlanner
    environment::Environment
end

"""
    generate_spiral(planner::SpiralPlanner, start::Tuple{Int,Int}, max_radius::Int=50) -> Vector{Tuple{Int,Int}}

Generate spiral path from center point.
"""
function generate_spiral(planner::SpiralPlanner, start::Tuple{Int,Int}, max_radius::Int=50)::Vector{Tuple{Int,Int}}
    path = [start]
    (x, y) = start

    dx, dy = 1, 0
    steps_in_direction = 1
    steps_taken = 0
    direction_changes = 0

    for _ in 1:(max_radius * max_radius)
        x += dx
        y += dy

        if is_valid_position(planner.environment, x, y)
            push!(path, (x, y))
        end

        steps_taken += 1

        if steps_taken == steps_in_direction
            steps_taken = 0
            direction_changes += 1

            # Rotate direction
            dx, dy = -dy, dx

            if direction_changes % 2 == 0
                steps_in_direction += 1
            end
        end

        if abs(x - start[1]) > max_radius && abs(y - start[2]) > max_radius
            break
        end
    end

    path
end

"""
    ZigzagPlanner

Zigzag (boustrophedon) coverage planner.
"""
struct ZigzagPlanner
    environment::Environment
end

"""
    generate_zigzag(planner::ZigzagPlanner) -> Vector{Tuple{Int,Int}}

Generate zigzag coverage path.
"""
function generate_zigzag(planner::ZigzagPlanner)::Vector{Tuple{Int,Int}}
    path = Tuple{Int,Int}[]

    for y in 1:planner.environment.height
        if y % 2 == 1
            # Left to right
            for x in 1:planner.environment.width
                if is_valid_position(planner.environment, x, y)
                    push!(path, (x, y))
                end
            end
        else
            # Right to left
            for x in planner.environment.width:-1:1
                if is_valid_position(planner.environment, x, y)
                    push!(path, (x, y))
                end
            end
        end
    end

    path
end

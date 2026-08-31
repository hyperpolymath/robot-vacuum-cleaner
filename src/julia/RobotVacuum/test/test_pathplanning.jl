"""
Tests for Path Planning module.
"""

@testset "Path Planning" begin
    @testset "A* Planner" begin
        env = create_empty_room(20, 20)
        planner = AStarPlanner(env)

        # Test path finding in empty room
        start = (5, 5)
        goal = (15, 15)
        path = find_path(planner, start, goal)

        @test !isempty(path)
        @test first(path) == start
        @test last(path) == goal

        # Path should be continuous
        for i in 1:(length(path)-1)
            current = path[i]
            next = path[i+1]
            # Adjacent cells (Manhattan distance = 1)
            dist = abs(current[1] - next[1]) + abs(current[2] - next[2])
            @test dist == 1
        end
    end

    @testset "A* with Obstacles" begin
        env = create_empty_room(10, 10)

        # Create a wall
        for i in 3:7
            set_cell!(env, 5, i, Obstacle)
        end

        planner = AStarPlanner(env)
        start = (2, 5)
        goal = (8, 5)
        path = find_path(planner, start, goal)

        # Should find path around obstacle
        @test !isempty(path)
        @test first(path) == start
        @test last(path) == goal

        # Path should not go through obstacles
        for pos in path
            @test get_cell(env, pos[1], pos[2]) != Obstacle
        end
    end

    @testset "A* No Path" begin
        env = create_empty_room(10, 10)

        # Create walls enclosing goal
        for i in 4:6
            set_cell!(env, 4, i, Obstacle)
            set_cell!(env, 6, i, Obstacle)
            set_cell!(env, i, 4, Obstacle)
            set_cell!(env, i, 6, Obstacle)
        end

        planner = AStarPlanner(env)
        start = (2, 2)
        goal = (5, 5)  # Enclosed
        path = find_path(planner, start, goal)

        # Should return empty path if no path exists
        @test isempty(path)
    end

    @testset "Spiral Planner" begin
        env = create_empty_room(10, 10)
        planner = SpiralPlanner(env)

        start = (5, 5)
        waypoints = generate_waypoints(planner, start)

        @test !isempty(waypoints)
        @test first(waypoints) == start

        # All waypoints should be valid
        for wp in waypoints
            @test is_valid_position(env, wp[1], wp[2])
        end
    end

    @testset "Zigzag Planner" begin
        env = create_empty_room(15, 15)
        planner = ZigzagPlanner(env, 1.0)

        start = (1, 1)
        waypoints = generate_waypoints(planner, start)

        @test !isempty(waypoints)

        # All waypoints should be valid
        for wp in waypoints
            @test is_valid_position(env, wp[1], wp[2])
        end

        # Should cover the room systematically
        @test length(waypoints) >= 10
    end

    @testset "Wall Follow Planner" begin
        env = create_room_with_furniture(20, 20, 3)
        planner = WallFollowPlanner(env)

        start = (5, 5)
        waypoints = generate_waypoints(planner, start)

        @test !isempty(waypoints)

        # All waypoints should be valid
        for wp in waypoints
            @test is_valid_position(env, wp[1], wp[2])
        end
    end

    @testset "Random Planner" begin
        env = create_empty_room(10, 10)
        planner = RandomPlanner(env)

        start = (5, 5)
        waypoints = generate_waypoints(planner, start)

        @test !isempty(waypoints)

        # All waypoints should be valid
        for wp in waypoints
            @test is_valid_position(env, wp[1], wp[2])
        end

        # Random planner should generate multiple waypoints
        @test length(waypoints) >= 5
    end

    @testset "Planner Comparison" begin
        env = create_empty_room(10, 10)
        start = (2, 2)

        # Different planners should generate different strategies
        spiral = SpiralPlanner(env)
        zigzag = ZigzagPlanner(env, 1.0)
        random = RandomPlanner(env)

        spiral_wp = generate_waypoints(spiral, start)
        zigzag_wp = generate_waypoints(zigzag, start)
        random_wp = generate_waypoints(random, start)

        # All should generate waypoints
        @test !isempty(spiral_wp)
        @test !isempty(zigzag_wp)
        @test !isempty(random_wp)

        # Patterns should differ
        @test spiral_wp != zigzag_wp
    end
end

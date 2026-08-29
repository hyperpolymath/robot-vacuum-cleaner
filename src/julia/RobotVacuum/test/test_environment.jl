"""
Tests for Environment module.
"""

@testset "Environment" begin
    @testset "Environment Creation" begin
        env = Environment(20, 30)

        @test env.width == 20
        @test env.height == 30
        @test size(env.grid) == (30, 20)  # height x width
        @test size(env.dirt_map) == (30, 20)
    end

    @testset "Cell Type Operations" begin
        env = Environment(10, 10)

        # Set and get cell types
        set_cell!(env, 5, 5, Obstacle)
        @test get_cell(env, 5, 5) == Obstacle

        set_cell!(env, 3, 3, Cliff)
        @test get_cell(env, 3, 3) == Cliff

        set_cell!(env, 7, 7, Dock)
        @test get_cell(env, 7, 7) == Dock

        # Default should be Free
        @test get_cell(env, 1, 1) == Free
    end

    @testset "Boundary Checking" begin
        env = Environment(10, 10)

        @test is_valid_position(env, 0, 0) == true
        @test is_valid_position(env, 5, 5) == true
        @test is_valid_position(env, 9, 9) == true

        @test is_valid_position(env, -1, 5) == false
        @test is_valid_position(env, 5, -1) == false
        @test is_valid_position(env, 10, 5) == false
        @test is_valid_position(env, 5, 10) == false
    end

    @testset "Dirt Management" begin
        env = Environment(10, 10)

        # Initially no dirt cleaned
        @test env.cells_cleaned == 0

        # Add and clean dirt
        env.dirt_map[5, 5] = true
        @test env.dirt_map[5, 5] == true

        clean_cell!(env, 5, 5)
        @test env.dirt_map[5, 5] == false
        @test env.cells_cleaned == 1
    end

    @testset "Cleaning Percentage" begin
        env = Environment(10, 10)
        # 10x10 = 100 cells total

        # No cells cleaned
        @test get_cleaning_percentage(env) == 0.0

        # Clean some cells
        env.cells_cleaned = 25
        @test get_cleaning_percentage(env) ≈ 25.0

        # Clean all cells
        env.cells_cleaned = 100
        @test get_cleaning_percentage(env) ≈ 100.0
    end

    @testset "Room Generation" begin
        # Test empty room
        env = create_empty_room(15, 20)
        @test env.width == 15
        @test env.height == 20

        # Should have all Free cells (except maybe dock)
        free_count = sum(env.grid .== UInt8(Free))
        @test free_count >= 290  # Most cells should be free

        # Test furnished room
        env = create_room_with_furniture(20, 20, 5)
        @test env.width == 20
        @test env.height == 20

        # Should have some obstacles
        obstacle_count = sum(env.grid .== UInt8(Obstacle))
        @test obstacle_count > 0
    end

    @testset "Environment Step" begin
        env = Environment(10, 10)
        initial_steps = env.steps

        step!(env)

        @test env.steps == initial_steps + 1
    end

    @testset "Multiple Environments" begin
        env1 = Environment(10, 10)
        env2 = Environment(20, 20)

        @test env1.width != env2.width
        @test env1.height != env2.height

        # Modifications to one shouldn't affect the other
        set_cell!(env1, 5, 5, Obstacle)
        @test get_cell(env1, 5, 5) == Obstacle
        @test get_cell(env2, 5, 5) == Free
    end
end

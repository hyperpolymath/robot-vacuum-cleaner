"""
Tests for Simulator module.
"""

@testset "Simulator" begin
    @testset "SimulationConfig" begin
        config = SimulationConfig()

        @test config.room_type == "furnished"
        @test config.cleaning_mode == Auto
        @test config.max_steps == 10000
        @test config.enable_slam == true
        @test config.random_seed === nothing

        # Custom config
        config2 = SimulationConfig(
            room_type="empty",
            cleaning_mode=Spot,
            max_steps=5000,
            enable_slam=false,
            random_seed=42
        )

        @test config2.room_type == "empty"
        @test config2.cleaning_mode == Spot
        @test config2.max_steps == 5000
        @test config2.enable_slam == false
        @test config2.random_seed == 42
    end

    @testset "Simulator Creation" begin
        env = create_empty_room(20, 20)
        robot = Robot(Position(10.0, 10.0))
        config = SimulationConfig(max_steps=100)

        sim = Simulator(robot, env, config)

        @test sim.robot.position.x == 10.0
        @test sim.environment.width == 20
        @test sim.config.max_steps == 100
        @test sim.steps == 0
        @test !isnothing(sim.slam)  # SLAM enabled by default
    end

    @testset "Simulator without SLAM" begin
        env = create_empty_room(20, 20)
        robot = Robot(Position(10.0, 10.0))
        config = SimulationConfig(enable_slam=false)

        sim = Simulator(robot, env, config)

        @test sim.slam === nothing
    end

    @testset "Simulator Step" begin
        env = create_empty_room(20, 20)
        robot = Robot(Position(10.0, 10.0))
        config = SimulationConfig(max_steps=100)

        sim = Simulator(robot, env, config)

        @test sim.steps == 0
        @test sim.robot.state == Idle

        # First step should start cleaning
        continue_sim = step!(sim)

        @test continue_sim == true
        @test sim.steps == 1
        @test sim.robot.state == Cleaning
    end

    @testset "Simulator Max Steps" begin
        env = create_empty_room(10, 10)
        robot = Robot(Position(5.0, 5.0))
        config = SimulationConfig(max_steps=10)

        sim = Simulator(robot, env, config)

        # Run until max steps
        for i in 1:9
            continue_sim = step!(sim)
            @test continue_sim == true
        end

        @test sim.steps == 9

        # One more step should hit max
        continue_sim = step!(sim)
        @test sim.steps == 10
        @test continue_sim == false
    end

    @testset "Robot State Transitions" begin
        env = create_empty_room(20, 20)
        robot = Robot(Position(10.0, 10.0))
        config = SimulationConfig(max_steps=100)

        sim = Simulator(robot, env, config)

        # Start idle
        @test sim.robot.state == Idle

        # After step should be cleaning
        step!(sim)
        @test sim.robot.state == Cleaning

        # Manually set low battery
        sim.robot.battery_level = 0.05
        step!(sim)
        @test sim.robot.state == ReturningToDock

        # At dock, start charging
        sim.robot.state = Charging
        sim.robot.battery_level = 0.5
        step!(sim)
        # Should still be charging or back to cleaning if charged
        @test sim.robot.state in [Charging, Cleaning]
    end

    @testset "Run Simulation Empty Room" begin
        config = SimulationConfig(
            room_type="empty",
            cleaning_mode=Auto,
            max_steps=100,
            enable_slam=false,
            random_seed=42
        )

        results = run_simulation(config)

        @test haskey(results, "steps")
        @test haskey(results, "cleaning_coverage")
        @test haskey(results, "total_distance")
        @test haskey(results, "battery_cycles")
        @test haskey(results, "success")

        @test results["steps"] > 0
        @test results["steps"] <= 100
        @test results["cleaning_coverage"] >= 0.0
        @test results["cleaning_coverage"] <= 100.0
        @test results["total_distance"] >= 0.0
        @test results["battery_cycles"] >= 0
        @test isa(results["success"], Bool)
    end

    @testset "Run Simulation Furnished Room" begin
        config = SimulationConfig(
            room_type="furnished",
            cleaning_mode=Auto,
            max_steps=200,
            enable_slam=true,
            random_seed=123
        )

        results = run_simulation(config)

        @test results["steps"] > 0
        @test results["steps"] <= 200
        @test results["cleaning_coverage"] >= 0.0
        @test results["total_distance"] >= 0.0
    end

    @testset "Simulation Reproducibility" begin
        config1 = SimulationConfig(
            room_type="empty",
            max_steps=50,
            random_seed=999
        )

        config2 = SimulationConfig(
            room_type="empty",
            max_steps=50,
            random_seed=999
        )

        results1 = run_simulation(config1)
        results2 = run_simulation(config2)

        # Same seed should give same results
        @test results1["steps"] == results2["steps"]
        @test results1["cleaning_coverage"] ≈ results2["cleaning_coverage"]
    end

    @testset "Different Cleaning Modes" begin
        modes = [Auto, Spot, Edge, Manual]

        for mode in modes
            config = SimulationConfig(
                room_type="empty",
                cleaning_mode=mode,
                max_steps=50,
                random_seed=42
            )

            results = run_simulation(config)
            @test results["steps"] > 0
            @test results["success"] == true
        end
    end

    @testset "Simulation Statistics" begin
        config = SimulationConfig(
            room_type="empty",
            max_steps=100,
            random_seed=42
        )

        results = run_simulation(config)

        # Distance should increase with steps
        @test results["total_distance"] > 0.0

        # Coverage should be positive
        @test results["cleaning_coverage"] > 0.0

        # Should complete successfully
        @test results["success"] == true
    end

    @testset "SLAM Integration" begin
        config = SimulationConfig(
            room_type="furnished",
            max_steps=100,
            enable_slam=true,
            random_seed=42
        )

        # Should run without errors
        results = run_simulation(config)
        @test results["success"] == true
    end

    @testset "Simulation Without SLAM" begin
        config = SimulationConfig(
            room_type="furnished",
            max_steps=100,
            enable_slam=false,
            random_seed=42
        )

        # Should run without errors
        results = run_simulation(config)
        @test results["success"] == true
    end
end

"""
Tests for Robot module.
"""

@testset "Robot" begin
    @testset "Robot Creation" begin
        pos = Position(10.0, 10.0)
        robot = Robot(pos)

        @test robot.position.x == 10.0
        @test robot.position.y == 10.0
        @test robot.battery_level == 1.0
        @test robot.state == Idle
        @test robot.mode == Auto
        @test robot.stats.total_distance == 0.0
    end

    @testset "Robot Movement" begin
        robot = Robot(Position(0.0, 0.0))
        initial_battery = robot.battery_level

        # Move robot
        success = move_robot!(robot, 3.0, 4.0)

        @test success == true
        @test robot.position.x == 3.0
        @test robot.position.y == 4.0
        @test robot.battery_level < initial_battery
        @test robot.stats.total_distance ≈ 5.0
    end

    @testset "Battery Management" begin
        robot = Robot(Position(0.0, 0.0))
        robot.battery_level = 0.05

        @test should_return_to_dock(robot) == true

        robot.battery_level = 0.5
        @test should_return_to_dock(robot) == false
    end

    @testset "Charging" begin
        robot = Robot(Position(0.0, 0.0))
        robot.battery_level = 0.5
        robot.state = Charging

        # Charge should increase battery
        initial_battery = robot.battery_level
        is_full = charge!(robot)

        @test robot.battery_level > initial_battery
        @test robot.battery_level <= 1.0

        # Charge to full
        robot.battery_level = 0.99
        is_full = charge!(robot)
        @test is_full == true
        @test robot.battery_level == 1.0
    end

    @testset "Sensor Update" begin
        robot = Robot(Position(5.0, 5.0))
        sensors = SensorData(
            [1.5, 2.0, 3.0],
            [true, false, false],
            false,
            0.8
        )

        update_sensors!(robot, sensors)

        @test robot.sensors.distances == [1.5, 2.0, 3.0]
        @test robot.sensors.obstacles == [true, false, false]
        @test robot.sensors.battery_level == 0.8
    end

    @testset "Robot States" begin
        robot = Robot(Position(0.0, 0.0))

        @test robot.state == Idle

        robot.state = Cleaning
        @test robot.state == Cleaning

        robot.state = ReturningToDock
        @test robot.state == ReturningToDock

        robot.state = Charging
        @test robot.state == Charging

        robot.state = Error
        @test robot.state == Error

        robot.state = Stuck
        @test robot.state == Stuck
    end

    @testset "Cleaning Modes" begin
        robot = Robot(Position(0.0, 0.0))

        robot.mode = Auto
        @test robot.mode == Auto

        robot.mode = Spot
        @test robot.mode == Spot

        robot.mode = Edge
        @test robot.mode == Edge

        robot.mode = Manual
        @test robot.mode == Manual
    end
end

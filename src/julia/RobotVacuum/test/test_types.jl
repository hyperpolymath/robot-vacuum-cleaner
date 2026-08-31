"""
Tests for core types module.
"""

@testset "Types" begin
    @testset "Position" begin
        p1 = Position(0.0, 0.0)
        p2 = Position(3.0, 4.0)

        @test p1.x == 0.0
        @test p1.y == 0.0
        @test p2.x == 3.0
        @test p2.y == 4.0

        # Test distance calculation
        @test distance(p1, p2) ≈ 5.0
        @test distance(p2, p1) ≈ 5.0
        @test distance(p1, p1) ≈ 0.0
    end

    @testset "Velocity" begin
        v = Velocity(1.0, 2.0)
        @test v.dx == 1.0
        @test v.dy == 2.0

        # Test magnitude
        @test magnitude(v) ≈ sqrt(5.0)
    end

    @testset "Pose" begin
        pose = Pose(Position(10.0, 20.0), π/4)
        @test pose.position.x == 10.0
        @test pose.position.y == 20.0
        @test pose.orientation ≈ π/4
    end

    @testset "SensorData" begin
        sensors = SensorData(
            [1.0, 2.0, 3.0],  # distances
            [false, false, true],  # obstacles
            false,  # cliff_detected
            0.75  # battery_level
        )

        @test length(sensors.distances) == 3
        @test sensors.distances[1] == 1.0
        @test sensors.obstacles[3] == true
        @test sensors.cliff_detected == false
        @test sensors.battery_level == 0.75
    end

    @testset "RobotStats" begin
        stats = RobotStats(100.0, 50.0, 2, 10)
        @test stats.total_distance == 100.0
        @test stats.area_cleaned == 50.0
        @test stats.battery_cycles == 2
        @test stats.obstacles_detected == 10
    end
end

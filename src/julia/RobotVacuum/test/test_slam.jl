"""
Tests for SLAM module.
"""

@testset "SLAM" begin
    @testset "OccupancyGrid" begin
        grid = OccupancyGrid(100, 100, 0.1)

        @test size(grid.grid) == (100, 100)
        @test grid.resolution == 0.1

        # Initial grid should be at default probability
        @test all(grid.grid .≈ 0.5)

        # Update occupancy
        update_occupancy!(grid, 50, 50, true)
        @test grid.grid[50, 50] > 0.5

        update_occupancy!(grid, 30, 30, false)
        @test grid.grid[30, 30] < 0.5
    end

    @testset "Particle" begin
        particle = Particle(
            Pose(Position(10.0, 20.0), π/3),
            0.8
        )

        @test particle.pose.position.x == 10.0
        @test particle.pose.position.y == 20.0
        @test particle.pose.orientation ≈ π/3
        @test particle.weight == 0.8
    end

    @testset "ParticleFilter" begin
        pf = ParticleFilter(100, 50.0, 50.0)

        @test length(pf.particles) == 100

        # All particles should have normalized weights
        total_weight = sum(p.weight for p in pf.particles)
        @test total_weight ≈ 1.0

        # Particles should be distributed around initial position
        for particle in pf.particles
            @test particle.pose.position.x >= 0.0
            @test particle.pose.position.y >= 0.0
            @test particle.weight > 0.0
        end
    end

    @testset "Particle Filter Prediction" begin
        pf = ParticleFilter(50, 25.0, 25.0)

        # Store initial positions
        initial_positions = [p.pose.position for p in pf.particles]

        # Predict movement
        velocity = Velocity(1.0, 0.0)
        predict!(pf, velocity, 1.0)

        # Particles should have moved
        new_positions = [p.pose.position for p in pf.particles]
        @test new_positions != initial_positions

        # Average movement should be approximately velocity * dt
        avg_dx = mean(new_positions[i].x - initial_positions[i].x for i in 1:length(pf.particles))
        @test avg_dx ≈ 1.0 atol=0.5
    end

    @testset "Particle Filter Update" begin
        pf = ParticleFilter(50, 25.0, 25.0)

        # Create sensor measurement
        measurement = SensorData(
            [2.0, 3.0, 2.5],
            [true, true, true],
            false,
            1.0
        )

        # Update particles
        update!(pf, measurement)

        # Weights should still be normalized
        total_weight = sum(p.weight for p in pf.particles)
        @test total_weight ≈ 1.0

        # Some particles should have different weights
        weights = [p.weight for p in pf.particles]
        @test length(unique(weights)) > 1
    end

    @testset "Particle Filter Resample" begin
        pf = ParticleFilter(100, 25.0, 25.0)

        # Set some particles to have very high weights
        pf.particles[1].weight = 0.9
        for i in 2:100
            pf.particles[i].weight = 0.001
        end
        normalize_weights!(pf)

        # Resample
        resample!(pf)

        # Should still have same number of particles
        @test length(pf.particles) == 100

        # Weights should be normalized
        total_weight = sum(p.weight for p in pf.particles)
        @test total_weight ≈ 1.0
    end

    @testset "Particle Filter Estimate" begin
        pf = ParticleFilter(100, 25.0, 25.0)

        # Get estimated pose
        pose = get_estimated_pose(pf)

        @test pose.position.x >= 0.0
        @test pose.position.y >= 0.0
        @test -π <= pose.orientation <= π

        # Estimate should be around the mean of particles
        mean_x = mean(p.pose.position.x for p in pf.particles)
        mean_y = mean(p.pose.position.y for p in pf.particles)

        @test abs(pose.position.x - mean_x) < 5.0
        @test abs(pose.position.y - mean_y) < 5.0
    end

    @testset "SLAM Integration" begin
        slam = SLAM(50, 50)

        @test size(slam.occupancy_grid.grid) == (50, 50)
        @test !isnothing(slam.particle_filter)
        @test length(slam.particle_filter.particles) > 0
    end

    @testset "SLAM Update" begin
        slam = SLAM(50, 50)

        # Get initial pose estimate
        initial_pose = get_estimated_pose(slam.particle_filter)

        # Update SLAM with movement and sensor data
        velocity = Velocity(0.5, 0.0)
        sensors = SensorData(
            [2.0, 2.5, 3.0],
            [true, false, true],
            false,
            0.9
        )

        update!(slam, velocity, sensors, 1.0)

        # Pose estimate should have changed
        new_pose = get_estimated_pose(slam.particle_filter)

        # Position should have moved (accounting for noise)
        @test abs(new_pose.position.x - initial_pose.position.x) >= 0.1
    end

    @testset "SLAM Map Building" begin
        slam = SLAM(100, 100)

        # Update with obstacle detections
        for i in 1:10
            sensors = SensorData(
                [1.5, 2.0, 2.5],
                [true, true, false],
                false,
                1.0
            )
            update!(slam, Velocity(0.1, 0.0), sensors, 1.0)
        end

        # Map should have been updated
        # Some cells should have changed from initial 0.5 probability
        changed_cells = sum(slam.occupancy_grid.grid .!= 0.5)
        @test changed_cells > 0
    end
end

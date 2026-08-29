"""
Main test runner for RobotVacuum Julia package.
"""

using Test
using RobotVacuum

@testset "RobotVacuum.jl" begin
    include("test_types.jl")
    include("test_robot.jl")
    include("test_environment.jl")
    include("test_pathplanning.jl")
    include("test_slam.jl")
    include("test_simulator.jl")
end

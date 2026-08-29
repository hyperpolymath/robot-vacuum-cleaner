"""
Main test runner for RobotVacuum Julia package.
"""

using Test
using RobotVacuum

const TESTS_DIR = joinpath(@__DIR__, "..", "..", "..", "..", "tests", "julia")

@testset "RobotVacuum.jl" begin
    include(joinpath(TESTS_DIR, "test_types.jl"))
    include(joinpath(TESTS_DIR, "test_robot.jl"))
    include(joinpath(TESTS_DIR, "test_environment.jl"))
    include(joinpath(TESTS_DIR, "test_pathplanning.jl"))
    include(joinpath(TESTS_DIR, "test_slam.jl"))
    include(joinpath(TESTS_DIR, "test_simulator.jl"))
end

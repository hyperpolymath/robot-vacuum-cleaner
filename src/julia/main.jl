#!/usr/bin/env julia

"""
Robot Vacuum Cleaner Simulator - Command Line Interface

Usage:
    julia main.jl [options]

Options:
    --room-type TYPE         Room type: empty, furnished (default: furnished)
    --cleaning-mode MODE     Cleaning mode: auto, spot, edge, manual (default: auto)
    --max-steps STEPS        Maximum simulation steps (default: 10000)
    --disable-slam          Disable SLAM (default: enabled)
    --seed SEED             Random seed for reproducibility
    --help                  Show this help message
"""

# Add RobotVacuum package to load path
push!(LOAD_PATH, joinpath(@__DIR__, "RobotVacuum"))

using RobotVacuum
using Printf

function parse_args(args::Vector{String})
    config = Dict{String,Any}(
        "room_type" => "furnished",
        "cleaning_mode" => "auto",
        "max_steps" => 10000,
        "enable_slam" => true,
        "random_seed" => nothing
    )

    i = 1
    while i <= length(args)
        arg = args[i]

        if arg == "--help" || arg == "-h"
            print_help()
            exit(0)
        elseif arg == "--room-type"
            i += 1
            config["room_type"] = args[i]
        elseif arg == "--cleaning-mode"
            i += 1
            config["cleaning_mode"] = args[i]
        elseif arg == "--max-steps"
            i += 1
            config["max_steps"] = parse(Int, args[i])
        elseif arg == "--disable-slam"
            config["enable_slam"] = false
        elseif arg == "--seed"
            i += 1
            config["random_seed"] = parse(Int, args[i])
        else
            println("Unknown argument: $arg")
            print_help()
            exit(1)
        end

        i += 1
    end

    return config
end

function print_help()
    println("""
    Robot Vacuum Cleaner Simulator - Command Line Interface

    Usage:
        julia main.jl [options]

    Options:
        --room-type TYPE         Room type: empty, furnished (default: furnished)
        --cleaning-mode MODE     Cleaning mode: auto, spot, edge, manual (default: auto)
        --max-steps STEPS        Maximum simulation steps (default: 10000)
        --disable-slam          Disable SLAM (default: enabled)
        --seed SEED             Random seed for reproducibility
        --help                  Show this help message

    Examples:
        # Run with default settings
        julia main.jl

        # Run empty room with 5000 steps
        julia main.jl --room-type empty --max-steps 5000

        # Run with specific seed for reproducibility
        julia main.jl --seed 42

        # Run spot cleaning mode without SLAM
        julia main.jl --cleaning-mode spot --disable-slam
    """)
end

function mode_from_string(mode_str::String)::CleaningMode
    mode_lower = lowercase(mode_str)
    if mode_lower == "auto"
        return Auto
    elseif mode_lower == "spot"
        return Spot
    elseif mode_lower == "edge"
        return Edge
    elseif mode_lower == "manual"
        return Manual
    else
        println("Unknown cleaning mode: $mode_str, using Auto")
        return Auto
    end
end

function print_banner()
    println("""
    ╔═══════════════════════════════════════════════╗
    ║   Robot Vacuum Cleaner Simulator (Julia)     ║
    ║   High-Performance Autonomous Cleaning        ║
    ╚═══════════════════════════════════════════════╝
    """)
end

function print_config(config::Dict{String,Any})
    println("\n📋 Simulation Configuration:")
    println("   Room Type:      $(config["room_type"])")
    println("   Cleaning Mode:  $(config["cleaning_mode"])")
    println("   Max Steps:      $(config["max_steps"])")
    println("   SLAM Enabled:   $(config["enable_slam"])")
    if config["random_seed"] !== nothing
        println("   Random Seed:    $(config["random_seed"])")
    end
    println()
end

function print_results(results::Dict{String,Any})
    println("\n" * "="^50)
    println("📊 Simulation Results")
    println("="^50)
    println()

    @printf "  Steps Executed:      %d\n" results["steps"]
    @printf "  Cleaning Coverage:   %.2f%%\n" results["cleaning_coverage"]
    @printf "  Total Distance:      %.2f units\n" results["total_distance"]
    @printf "  Battery Cycles:      %d\n" results["battery_cycles"]
    @printf "  Success:             %s\n" results["success"] ? "✅ Yes" : "❌ No"

    println()
    println("="^50)
end

function main()
    print_banner()

    # Parse command line arguments
    config_dict = parse_args(ARGS)
    print_config(config_dict)

    # Create simulation configuration
    cleaning_mode = mode_from_string(config_dict["cleaning_mode"])

    sim_config = SimulationConfig(
        room_type=config_dict["room_type"],
        cleaning_mode=cleaning_mode,
        max_steps=config_dict["max_steps"],
        enable_slam=config_dict["enable_slam"],
        random_seed=config_dict["random_seed"]
    )

    # Run simulation
    println("🤖 Starting simulation...")
    println()

    try
        results = run_simulation(sim_config)
        print_results(results)

        # Exit code based on success
        exit(results["success"] ? 0 : 1)
    catch e
        println("\n❌ Simulation failed with error:")
        println(e)
        for (exc, bt) in Base.catch_stack()
            showerror(stdout, exc, bt)
            println()
        end
        exit(1)
    end
end

# Run main if executed as script
if abspath(PROGRAM_FILE) == @__FILE__
    main()
end

//! Robot Vacuum Cleaner CLI Application

use clap::Parser;
use env_logger::Env;
use robot_vacuum_cleaner::{Robot, Environment, Simulator, Position};
use robot_vacuum_cleaner::simulator::{SimulationConfig, SimulationResults};

/// Robot Vacuum Cleaner Simulator
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Room width
    #[arg(short, long, default_value_t = 50)]
    width: usize,

    /// Room height
    #[arg(short = 'H', long, default_value_t = 50)]
    height: usize,

    /// Maximum simulation steps
    #[arg(short, long, default_value_t = 10000)]
    max_steps: usize,

    /// Enable SLAM
    #[arg(short, long)]
    slam: bool,

    /// Starting X position
    #[arg(short, long, default_value_t = 25.0)]
    start_x: f64,

    /// Starting Y position
    #[arg(short, long, default_value_t = 25.0)]
    start_y: f64,

    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
}

fn main() {
    let args = Args::parse();

    // Initialize logger
    let log_level = if args.verbose { "debug" } else { "info" };
    env_logger::Builder::from_env(Env::default().default_filter_or(log_level)).init();

    log::info!("Robot Vacuum Cleaner Simulator v{}", robot_vacuum_cleaner::VERSION);
    log::info!("Initializing simulation...");

    // Create environment
    let environment = Environment::create_empty_room(args.width, args.height);
    log::info!("Environment created: {}x{}", args.width, args.height);

    // Create robot
    let robot = Robot::new(Position::new(args.start_x, args.start_y));
    log::info!("Robot initialized at ({}, {})", args.start_x, args.start_y);

    // Create simulation config
    let config = SimulationConfig {
        max_steps: args.max_steps,
        enable_slam: args.slam,
        tick_rate: 0.1,
    };

    // Create and run simulator
    let mut simulator = Simulator::new(robot, environment, config);
    let results = simulator.run();

    // Print results
    println!("\n=== Simulation Results ===");
    println!("Steps: {}", results.steps);
    println!("Success: {}", results.success);
    println!("Cleaning Coverage: {:.2}%", results.cleaning_coverage);
    println!("Total Distance: {:.2}m", results.total_distance);
    println!("Battery Cycles: {}", results.battery_cycles);
    println!("==========================\n");

    if results.success {
        std::process::exit(0);
    } else {
        std::process::exit(1);
    }
}

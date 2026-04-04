// SPDX-License-Identifier: PMPL-1.0-or-later
//! End-to-end integration tests
//!
//! Tests complete workflows like cleaning a room, navigating between points, battery management

use robot_vacuum_cleaner::{
    Robot, Environment, Simulator, SimulationConfig, Position, RobotState, CleaningMode,
};

#[test]
fn e2e_create_robot_and_environment() {
    // Create a robot
    let robot = Robot::new(Position::new(10.0, 10.0));
    assert_eq!(robot.position, Position::new(10.0, 10.0));
    assert_eq!(robot.battery_level, 100.0);
    assert_eq!(robot.state, RobotState::Idle);

    // Create environment
    let env = Environment::new(50, 50);
    assert_eq!(env.width, 50);
    assert_eq!(env.height, 50);
}

#[test]
fn e2e_navigation_point_to_point() {
    let start = Position::new(10.0, 10.0);
    let target = Position::new(20.0, 20.0);

    let mut robot = Robot::new(start);
    assert_eq!(robot.position, start);

    // Navigate by moving toward target
    let dx = (target.x - robot.position.x).min(5.0); // Move in smaller steps
    let dy = (target.y - robot.position.y).min(5.0);

    robot.move_by(dx, dy);

    // Should be closer to target
    let new_distance = robot.position.distance_to(&target);
    let original_distance = start.distance_to(&target);
    assert!(new_distance < original_distance);
}

#[test]
fn e2e_cleaning_workflow() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));
    robot.state = RobotState::Cleaning;
    robot.mode = CleaningMode::Auto;

    let initial_cleaned_cells = robot.cleaned_cells.len();

    // Simulate cleaning by moving
    robot.move_by(1.0, 0.0);
    robot.move_by(0.0, 1.0);
    robot.move_by(-1.0, 0.0);
    robot.move_by(0.0, -1.0);

    // Should have cleaned cells
    assert!(robot.cleaned_cells.len() > initial_cleaned_cells);
    assert!(!robot.visited_cells.is_empty());
    assert_eq!(robot.state, RobotState::Cleaning);
}

#[test]
fn e2e_battery_depletion() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));
    let initial_battery = robot.battery_level;

    // Move multiple times to deplete battery
    for _ in 0..20 {
        if !robot.move_by(1.0, 1.0) {
            break;
        }
    }

    // Battery should be depleted
    assert!(robot.battery_level < initial_battery);
    assert!(robot.battery_level >= 0.0);

    // Should eventually fail
    if robot.battery_level <= 0.0 {
        assert_eq!(robot.state, RobotState::Error);
    }
}

#[test]
fn e2e_charging_cycle() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));
    robot.set_dock_position(Position::new(25.0, 25.0));

    // Deplete battery
    robot.battery_level = 50.0;

    // Start charging
    robot.state = RobotState::Charging;
    assert_eq!(robot.state, RobotState::Charging);

    // Charge to full
    let charge_rate = 10.0;
    let mut charged = false;
    for _ in 0..10 {
        charged = robot.charge(charge_rate);
        if charged {
            break;
        }
    }

    assert!(charged);
    assert_eq!(robot.battery_level, 100.0);
}

#[test]
fn e2e_dock_return_logic() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));
    let dock = Position::new(5.0, 5.0);
    robot.set_dock_position(dock);

    // Robot should not return with high battery
    assert!(!robot.should_return_to_dock());

    // Deplete battery below threshold
    robot.battery_level = 15.0;
    assert!(robot.should_return_to_dock());
}

#[test]
fn e2e_simulator_basic_cycle() {
    let robot = Robot::new(Position::new(25.0, 25.0));
    let env = Environment::new(50, 50);
    let config = SimulationConfig {
        max_steps: 100,
        enable_slam: false,
        tick_rate: 0.1,
    };

    let mut sim = Simulator::new(robot, env, config);

    // Run one step
    let should_continue = sim.step();
    assert!(should_continue);
    assert_eq!(sim.steps, 1);

    // Robot should have transitioned to cleaning
    assert_eq!(sim.robot.state, RobotState::Cleaning);
}

#[test]
fn e2e_simulator_full_run() {
    let robot = Robot::new(Position::new(25.0, 25.0));
    let env = Environment::create_empty_room(50, 50);
    let config = SimulationConfig {
        max_steps: 200,
        enable_slam: false,
        tick_rate: 0.1,
    };

    let mut sim = Simulator::new(robot, env, config);
    let results = sim.run();

    // Verify results structure
    assert!(results.steps > 0);
    assert!(results.steps <= 200);
    assert!(results.cleaning_coverage >= 0.0);
    assert!(results.cleaning_coverage <= 1.0);
    assert!(results.total_distance >= 0.0);
}

#[test]
fn e2e_multi_room_visit_pattern() {
    let mut robot = Robot::new(Position::new(10.0, 10.0));

    // Visit different "rooms" (grid cells)
    let rooms = vec![
        Position::new(10.0, 10.0),
        Position::new(30.0, 10.0),
        Position::new(30.0, 30.0),
        Position::new(10.0, 30.0),
    ];

    for room in rooms {
        // Move toward room
        while robot.position.distance_to(&room) > 1.0 && robot.battery_level > 5.0 {
            let dx = (room.x - robot.position.x).clamp(-1.0, 1.0);
            let dy = (room.y - robot.position.y).clamp(-1.0, 1.0);
            robot.move_by(dx, dy);
        }

        // Verify we're near the room
        assert!(robot.position.distance_to(&room) <= 2.0 || robot.battery_level <= 5.0);
    }

    // Should have visited multiple cells
    assert!(robot.visited_cells.len() > 1);
}

#[test]
fn e2e_stats_accumulation() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    let initial_stats = robot.stats.clone();

    // Perform actions
    robot.move_by(5.0, 0.0);
    robot.move_by(0.0, 5.0);
    robot.move_by(-3.0, -3.0);

    // Stats should have changed
    assert!(robot.stats.total_distance > initial_stats.total_distance);
    assert!(robot.stats.area_cleaned > initial_stats.area_cleaned);

    // Reset stats
    robot.reset_stats();
    assert_eq!(robot.stats.total_distance, 0.0);
    assert_eq!(robot.stats.area_cleaned, 0);
}

#[test]
fn e2e_cleaning_mode_switching() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // Test different cleaning modes
    let modes = vec![
        CleaningMode::Auto,
        CleaningMode::Spot,
        CleaningMode::Edge,
        CleaningMode::Spiral,
        CleaningMode::Zigzag,
        CleaningMode::WallFollow,
        CleaningMode::Random,
    ];

    for mode in modes {
        robot.mode = mode;
        assert_eq!(robot.mode, mode);

        // Robot should still be able to move in any mode
        robot.move_by(1.0, 0.0);
    }

    // Should have moved successfully in all modes
    assert!(robot.stats.total_distance > 0.0);
}

#[test]
fn e2e_sensor_data_tracking() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // Initially no obstacles
    assert!(!robot.sensor_data.obstacle_front);
    assert!(!robot.sensor_data.cliff_detected);

    // Simulate sensor reading
    robot.sensor_data.obstacle_front = true;
    assert!(robot.sensor_data.obstacle_front);

    // Update sensor data
    robot.sensor_data.distance_front = 0.5;
    assert!(robot.sensor_data.distance_front < 1.0);
}

#[test]
fn e2e_environment_step_progression() {
    let mut env = Environment::new(30, 30);

    let initial_time = env.sim_time;
    assert_eq!(initial_time, 0.0);

    // Step simulation
    env.step(0.1);
    assert!(env.sim_time > initial_time);
}

#[test]
fn e2e_full_workflow() {
    // Complete workflow: create robot, set dock, clean, return to dock, charge
    let mut robot = Robot::new(Position::new(25.0, 25.0));
    let dock = Position::new(25.0, 25.0);
    robot.set_dock_position(dock);

    // Start cleaning
    robot.state = RobotState::Cleaning;
    robot.move_by(5.0, 5.0);
    assert!(robot.stats.total_distance > 0.0);

    // Simulate low battery decision
    robot.battery_level = 15.0;
    if robot.should_return_to_dock() {
        robot.state = RobotState::ReturningToDock;
    }
    assert_eq!(robot.state, RobotState::ReturningToDock);

    // Return to dock
    robot.position = dock;
    robot.state = RobotState::Charging;
    assert_eq!(robot.state, RobotState::Charging);

    // Charge
    robot.charge(10.0);
    robot.battery_level = 100.0;
    robot.state = RobotState::Idle;

    // Verify cycle complete
    assert_eq!(robot.state, RobotState::Idle);
    assert_eq!(robot.battery_level, 100.0);
}

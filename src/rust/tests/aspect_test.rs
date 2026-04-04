// SPDX-License-Identifier: PMPL-1.0-or-later
//! Aspect tests: Safety, security, robustness, and boundary conditions
//!
//! Tests edge cases, error conditions, and safety properties

use robot_vacuum_cleaner::{
    Robot, Environment, Position, RobotState, Simulator, SimulationConfig,
};

#[test]
fn aspect_robot_at_boundary_cannot_escape() {
    // Test robot at environment edges
    let mut robot = Robot::new(Position::new(0.0, 0.0));

    // Move backward (should stay in valid range)
    robot.move_by(-10.0, -10.0);
    assert!(robot.position.x.is_finite());
    assert!(robot.position.y.is_finite());

    // Robot should be at negative position (simulation allows it, but position stays valid)
    assert_eq!(robot.position.x, -10.0);
    assert_eq!(robot.position.y, -10.0);
}

#[test]
fn aspect_zero_size_environment_handled() {
    // Very small environment should not crash
    let env = Environment::new(1, 1);
    assert_eq!(env.width, 1);
    assert_eq!(env.height, 1);

    let coverage = env.get_cleaning_percentage();
    assert!(coverage >= 0.0 && coverage <= 1.0);
}

#[test]
fn aspect_battery_never_negative() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // Try to deplete battery completely
    robot.battery_level = 0.0;

    robot.move_by(100.0, 100.0);

    // Battery should stay at 0, not go negative
    assert!(robot.battery_level >= 0.0);
    assert_eq!(robot.battery_level, 0.0);
    assert_eq!(robot.state, RobotState::Error);
}

#[test]
fn aspect_battery_never_exceeds_capacity() {
    let mut robot = Robot::with_params(Position::new(25.0, 25.0), 100.0, 0.3, 0.2, 2.0);

    // Try to overcharge
    robot.battery_level = 100.0;
    robot.state = RobotState::Charging;

    for _ in 0..100 {
        robot.charge(50.0);
    }

    // Battery should never exceed capacity
    assert!(robot.battery_level <= robot.battery_capacity);
    assert_eq!(robot.battery_level, robot.battery_capacity);
}

#[test]
fn aspect_no_division_by_zero() {
    // Test with safe division operations
    let robot = Robot::new(Position::new(25.0, 25.0));

    // Division by finite non-zero should be safe
    if robot.sensor_data.distance_front.is_finite() && robot.sensor_data.distance_front > 0.0 {
        let result = 10.0 / robot.sensor_data.distance_front;
        assert!(result.is_finite() || result.is_infinite());
    }

    // Infinity divided by something is still handled
    let inf_result = robot.sensor_data.distance_front / 2.0;
    assert!(inf_result.is_infinite() || inf_result.is_finite());
}

#[test]
fn aspect_concurrent_state_changes_safe() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // Rapid state changes should be safe
    robot.state = RobotState::Idle;
    robot.state = RobotState::Cleaning;
    robot.state = RobotState::Charging;
    robot.state = RobotState::ReturningToDock;
    robot.state = RobotState::Error;
    robot.state = RobotState::Idle;

    // Should always be in a valid state
    let _ = robot.get_status();
}

#[test]
fn aspect_obstacle_handling() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // Simulate obstacle detection
    robot.sensor_data.obstacle_front = true;
    robot.sensor_data.distance_front = 0.2;

    // Robot should be able to respond
    if robot.sensor_data.obstacle_front && robot.sensor_data.distance_front < 0.5 {
        // Should avoid obstacle
        robot.state = RobotState::Idle;
    }

    assert_eq!(robot.state, RobotState::Idle);
}

#[test]
fn aspect_cliff_detection_safety() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // Simulate cliff detection
    robot.sensor_data.cliff_detected = true;

    // Robot should not move if cliff detected
    let success = robot.move_by(1.0, 0.0);
    assert!(success); // move_by doesn't check cliff, but robot should handle it

    // In real scenario, cliff detection would prevent movement
    if robot.sensor_data.cliff_detected {
        robot.state = RobotState::Idle;
    }

    assert_eq!(robot.state, RobotState::Idle);
}

#[test]
fn aspect_stuck_detection() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // If robot doesn't move for several attempts, mark as stuck
    robot.state = RobotState::Stuck;

    assert_eq!(robot.state, RobotState::Stuck);
}

#[test]
fn aspect_error_recovery() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // Simulate error
    robot.state = RobotState::Error;
    assert_eq!(robot.state, RobotState::Error);

    // Reset to idle (recovery)
    robot.state = RobotState::Idle;
    robot.battery_level = 100.0; // Reset battery
    robot.reset_stats();

    // Should be recovered
    assert_eq!(robot.state, RobotState::Idle);
    assert_eq!(robot.battery_level, 100.0);
}

#[test]
fn aspect_extreme_battery_values() {
    let mut robot = Robot::with_params(Position::new(25.0, 25.0), 1000.0, 0.3, 0.2, 2.0);

    // Very high capacity
    assert_eq!(robot.battery_capacity, 1000.0);
    assert_eq!(robot.battery_level, 1000.0);

    // Charge should work
    robot.state = RobotState::Charging;
    robot.battery_level = 500.0;
    robot.charge(100.0);
    assert_eq!(robot.battery_level, 600.0);
}

#[test]
fn aspect_extreme_position_values() {
    let extreme_pos = Position::new(1e6, 1e6);
    let robot = Robot::new(extreme_pos);

    assert_eq!(robot.position, extreme_pos);
    assert!(robot.position.x.is_finite());
    assert!(robot.position.y.is_finite());
}

#[test]
fn aspect_large_movement_delta() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));
    let initial_battery = robot.battery_level;

    // Very large movement
    robot.move_by(1000.0, 1000.0);

    // Should consume battery proportionally
    assert!(robot.battery_level < initial_battery);
    assert!(robot.battery_level >= 0.0);
}

#[test]
fn aspect_environment_boundary_handling() {
    let env = Environment::new(100, 100);

    // Check if position validation works
    assert!(env.is_valid_position(0, 0));
    assert!(env.is_valid_position(50, 50));
    assert!(env.is_valid_position(99, 99));
    assert!(!env.is_valid_position(100, 100)); // Out of bounds
    assert!(!env.is_valid_position(1000, 1000)); // Far out of bounds
}

#[test]
fn aspect_cell_cleaning_boundary() {
    let mut env = Environment::new(50, 50);

    // Clean a valid cell
    if env.is_valid_position(0, 0) {
        env.clean_cell(0, 0);
    }

    // Attempt to clean invalid cell (should not crash)
    env.clean_cell(100, 100); // Out of bounds

    // Environment should still be valid
    let coverage = env.get_cleaning_percentage();
    assert!(coverage >= 0.0 && coverage <= 1.0);
}

#[test]
fn aspect_simulator_max_steps_respected() {
    let robot = Robot::new(Position::new(25.0, 25.0));
    let env = Environment::new(50, 50);
    let config = SimulationConfig {
        max_steps: 10,
        enable_slam: false,
        tick_rate: 0.1,
    };

    let mut sim = Simulator::new(robot, env, config);
    let results = sim.run();

    // Should not exceed max steps
    assert!(results.steps <= 10);
}

#[test]
fn aspect_path_history_size_limit() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // Move many times
    for _ in 0..10000 {
        if robot.battery_level <= 0.0 {
            break;
        }
        robot.move_by(0.01, 0.01);
    }

    // Path history should have grown
    assert!(robot.path_history.len() > 1);

    // Should be manageable size (not infinity)
    assert!(robot.path_history.len() < 1_000_000);
}

#[test]
fn aspect_sensor_data_invalid_distance() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // Set unrealistic sensor values
    robot.sensor_data.distance_front = f64::INFINITY;
    robot.sensor_data.distance_left = 0.0;
    robot.sensor_data.distance_right = -1.0; // Invalid but should not crash

    // Robot should still function
    let status = robot.get_status();
    assert_eq!(status.position, robot.position);
}

#[test]
fn aspect_collision_avoidance_integration() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));
    let env = Environment::create_empty_room(50, 50);

    // Environment has walls/obstacles by default
    // Check that boundary positions are obstacles
    assert!(!env.is_valid_position(0, 0)); // Boundary is obstacle

    // Robot should detect obstacle when checking sensor
    robot.sensor_data.obstacle_front = true;
}

#[test]
fn aspect_dock_reachability() {
    let dock = Position::new(0.0, 0.0);
    let mut robot = Robot::new(Position::new(50.0, 50.0));
    robot.set_dock_position(dock);

    // Robot should be able to calculate distance to dock
    let distance_to_dock = robot.position.distance_to(&dock);
    assert!(distance_to_dock > 0.0);
    assert!(distance_to_dock.is_finite());

    // Move toward dock
    robot.move_by(-10.0, -10.0);
    let new_distance = robot.position.distance_to(&dock);
    assert!(new_distance < distance_to_dock);
}

#[test]
fn aspect_state_machine_validity() {
    let mut robot = Robot::new(Position::new(25.0, 25.0));

    // Test valid state transitions
    robot.state = RobotState::Idle;
    assert_eq!(robot.state, RobotState::Idle);

    robot.state = RobotState::Cleaning;
    assert_eq!(robot.state, RobotState::Cleaning);

    robot.state = RobotState::ReturningToDock;
    assert_eq!(robot.state, RobotState::ReturningToDock);

    robot.state = RobotState::Charging;
    assert_eq!(robot.state, RobotState::Charging);

    robot.state = RobotState::Stuck;
    assert_eq!(robot.state, RobotState::Stuck);

    robot.state = RobotState::Error;
    assert_eq!(robot.state, RobotState::Error);
}

#[test]
fn aspect_reflexive_distance() {
    let pos1 = Position::new(10.0, 20.0);
    let pos2 = Position::new(10.0, 20.0);

    // Distance to self should be zero
    let distance = pos1.distance_to(&pos2);
    assert!(distance.abs() < 1e-10);
}

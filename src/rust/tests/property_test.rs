// SPDX-License-Identifier: PMPL-1.0-or-later
//! Property-based tests using proptest
//!
//! Tests invariants that should hold for all valid robot states

use proptest::prelude::*;
use robot_vacuum_cleaner::{Robot, Position, Environment, Simulator, SimulationConfig};

// Strategy for generating valid positions within reasonable bounds
fn position_strategy() -> impl Strategy<Value = Position> {
    (0.0..100.0_f64, 0.0..100.0_f64).prop_map(|(x, y)| Position::new(x, y))
}

// Strategy for valid battery levels
fn battery_strategy() -> impl Strategy<Value = f64> {
    0.0..=100.0_f64
}

// Strategy for valid movement deltas
fn movement_delta_strategy() -> impl Strategy<Value = (f64, f64)> {
    (-10.0..10.0_f64, -10.0..10.0_f64)
}

proptest! {
    /// Robot position is always within valid bounds after movement
    #[test]
    fn prop_robot_position_stays_valid(
        pos in position_strategy(),
        (dx, dy) in movement_delta_strategy()
    ) {
        let mut robot = Robot::new(pos);
        robot.set_dock_position(Position::new(50.0, 50.0));

        let _ = robot.move_by(dx, dy);

        // Position should be finite (not NaN or infinite)
        prop_assert!(robot.position.x.is_finite());
        prop_assert!(robot.position.y.is_finite());
    }

    /// Battery level always stays within [0.0, 100.0]
    #[test]
    fn prop_battery_stays_in_valid_range(
        pos in position_strategy(),
        initial_battery in battery_strategy(),
    ) {
        let mut robot = Robot::with_params(pos, 100.0, 0.3, 0.2, 2.0);
        robot.battery_level = initial_battery;

        // Move several times
        for _ in 0..10 {
            let _ = robot.move_by(1.0, 1.0);
        }

        // Battery should never exceed capacity or go below 0
        prop_assert!(robot.battery_level >= 0.0);
        prop_assert!(robot.battery_level <= robot.battery_capacity);
    }

    /// Total distance is always non-negative and monotonically increasing
    #[test]
    fn prop_distance_monotonic(
        pos in position_strategy(),
        movements in prop::collection::vec(((-5.0..5.0_f64), (-5.0..5.0_f64)), 1..20)
    ) {
        let mut robot = Robot::new(pos);
        let mut prev_distance = robot.stats.total_distance;

        for (dx, dy) in movements {
            let _ = robot.move_by(dx, dy);
            let curr_distance = robot.stats.total_distance;

            // Distance should never decrease
            prop_assert!(curr_distance >= prev_distance);
            prop_assert!(curr_distance >= 0.0);
            prev_distance = curr_distance;
        }
    }

    /// Cleaned cells count is always ≤ visited cells count
    #[test]
    fn prop_cleaned_cells_subset_of_visited(
        pos in position_strategy(),
        movements in prop::collection::vec(((-5.0..5.0_f64), (-5.0..5.0_f64)), 1..20)
    ) {
        let mut robot = Robot::new(pos);

        for (dx, dy) in movements {
            let _ = robot.move_by(dx, dy);
        }

        // All cleaned cells should be in visited cells
        for cleaned_cell in &robot.cleaned_cells {
            prop_assert!(robot.visited_cells.contains(cleaned_cell),
                        "Cleaned cell {:?} not in visited cells", cleaned_cell);
        }

        // Cleaned count should not exceed visited count
        prop_assert!(robot.cleaned_cells.len() <= robot.visited_cells.len());
    }

    /// Coverage percentage always in [0.0, 1.0]
    #[test]
    fn prop_coverage_percentage_valid(
        width in 5usize..50,
        height in 5usize..50
    ) {
        let env = Environment::new(width, height);
        let coverage = env.get_cleaning_percentage();

        prop_assert!(coverage >= 0.0);
        prop_assert!(coverage <= 1.0);
    }

    /// Robot state should never spontaneously change (without action)
    #[test]
    fn prop_robot_state_consistency(
        pos in position_strategy(),
        (dx, dy) in movement_delta_strategy()
    ) {
        let mut robot = Robot::new(pos);
        let initial_state = robot.state;

        // Move shouldn't change state
        let _ = robot.move_by(dx, dy);

        // State should remain unless we explicitly change it
        prop_assert_eq!(robot.state, initial_state);
    }

    /// Charging increases battery level monotonically
    #[test]
    fn prop_charging_increases_battery(
        pos in position_strategy(),
        initial_battery in 0.0..100.0_f64,
        charge_rate in 1.0..50.0_f64
    ) {
        let mut robot = Robot::with_params(pos, 100.0, 0.3, 0.2, 2.0);
        robot.battery_level = initial_battery.min(99.0); // Must have room to charge
        robot.state = robot_vacuum_cleaner::RobotState::Charging;

        let before = robot.battery_level;
        robot.charge(charge_rate);
        let after = robot.battery_level;

        // Battery should increase or stay the same if already full
        prop_assert!(after >= before);
        prop_assert!(after <= robot.battery_capacity);
    }

    /// Path history grows with each movement
    #[test]
    fn prop_path_history_growth(
        pos in position_strategy(),
        movements in prop::collection::vec(((-2.0..2.0_f64), (-2.0..2.0_f64)), 1..20)
    ) {
        let mut robot = Robot::new(pos);
        let initial_path_len = robot.path_history.len();

        for (dx, dy) in movements {
            if robot.battery_level > 0.0 {
                let _ = robot.move_by(dx, dy);
            }
        }

        // Path history should grow or stay same (if battery depleted)
        prop_assert!(robot.path_history.len() >= initial_path_len);
    }

    /// Dock position once set should never change (unless explicitly set again)
    #[test]
    fn prop_dock_position_stable(
        pos in position_strategy(),
        dock_pos in position_strategy(),
        (dx, dy) in movement_delta_strategy()
    ) {
        let mut robot = Robot::new(pos);
        robot.set_dock_position(dock_pos);
        let set_dock = robot.dock_position;

        // Move should not change dock position
        let _ = robot.move_by(dx, dy);

        prop_assert_eq!(robot.dock_position, set_dock);
    }

    /// Manhattan distance is always >= Euclidean distance
    #[test]
    fn prop_manhattan_euclidean_relationship(
        p1 in position_strategy(),
        p2 in position_strategy()
    ) {
        let euclidean = p1.distance_to(&p2);
        let manhattan = p1.manhattan_distance(&p2);

        // Manhattan distance >= Euclidean distance (for valid metrics)
        prop_assert!(manhattan >= euclidean - 1e-10);
    }
}

#[cfg(test)]
mod smoke_tests {
    use super::*;

    /// Smoke test: Robot can be created and moved
    #[test]
    fn smoke_robot_creation_and_movement() {
        let mut robot = Robot::new(Position::new(10.0, 10.0));
        assert_eq!(robot.position, Position::new(10.0, 10.0));

        robot.move_by(5.0, 5.0);
        assert!(robot.position.x > 10.0);
        assert!(robot.position.y > 10.0);
    }

    /// Smoke test: Environment can be created
    #[test]
    fn smoke_environment_creation() {
        let env = Environment::new(50, 50);
        assert_eq!(env.width, 50);
        assert_eq!(env.height, 50);
    }

    /// Smoke test: Simulator can run
    #[test]
    fn smoke_simulator_basic() {
        let robot = Robot::new(Position::new(25.0, 25.0));
        let env = Environment::new(50, 50);
        let config = SimulationConfig {
            max_steps: 100,
            enable_slam: false,
            tick_rate: 0.1,
        };

        let mut sim = Simulator::new(robot, env, config);
        let _results = sim.run();
    }
}

//! Robot vacuum core implementation

use crate::types::{Position, SensorData, RobotStats};
use serde::{Deserialize, Serialize};
use std::collections::HashSet;

/// Robot operational states
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RobotState {
    Idle,
    Cleaning,
    ReturningToDock,
    Charging,
    Error,
    Stuck,
}

/// Cleaning modes
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CleaningMode {
    Auto,
    Spot,
    Edge,
    Spiral,
    Zigzag,
    WallFollow,
    Random,
}

/// Robot vacuum cleaner
#[derive(Debug, Clone)]
pub struct Robot {
    pub position: Position,
    pub battery_capacity: f64,
    pub battery_level: f64,
    pub cleaning_width: f64,
    pub speed: f64,
    pub sensor_range: f64,
    pub state: RobotState,
    pub mode: CleaningMode,
    pub heading: f64,
    pub dock_position: Option<Position>,
    pub sensor_data: SensorData,
    pub stats: RobotStats,
    pub cleaned_cells: HashSet<(usize, usize)>,
    pub visited_cells: HashSet<(usize, usize)>,
    pub path_history: Vec<Position>,
}

impl Robot {
    /// Create a new robot
    pub fn new(position: Position) -> Self {
        let mut path_history = Vec::new();
        path_history.push(position);

        Self {
            position,
            battery_capacity: 100.0,
            battery_level: 100.0,
            cleaning_width: 0.3,
            speed: 0.2,
            sensor_range: 2.0,
            state: RobotState::Idle,
            mode: CleaningMode::Auto,
            heading: 0.0,
            dock_position: None,
            sensor_data: SensorData::default(),
            stats: RobotStats::default(),
            cleaned_cells: HashSet::new(),
            visited_cells: HashSet::new(),
            path_history,
        }
    }

    /// Create robot with custom parameters
    pub fn with_params(
        position: Position,
        battery_capacity: f64,
        cleaning_width: f64,
        speed: f64,
        sensor_range: f64,
    ) -> Self {
        let mut robot = Self::new(position);
        robot.battery_capacity = battery_capacity;
        robot.battery_level = battery_capacity;
        robot.cleaning_width = cleaning_width;
        robot.speed = speed;
        robot.sensor_range = sensor_range;
        robot
    }

    /// Move robot by given delta
    pub fn move_by(&mut self, dx: f64, dy: f64) -> bool {
        if self.battery_level <= 0.0 {
            self.state = RobotState::Error;
            log::warn!("Cannot move: battery depleted");
            return false;
        }

        // Update position
        self.position = Position::new(self.position.x + dx, self.position.y + dy);
        self.path_history.push(self.position);

        // Update stats
        let distance = (dx * dx + dy * dy).sqrt();
        self.stats.total_distance += distance;

        // Consume battery (proportional to distance)
        let battery_consumption = distance * 0.1;
        self.battery_level = (self.battery_level - battery_consumption).max(0.0);

        // Mark cell as visited and cleaned
        let grid_pos = self.position.to_grid();
        self.visited_cells.insert(grid_pos);
        self.cleaned_cells.insert(grid_pos);
        self.stats.area_cleaned = self.cleaned_cells.len();

        true
    }

    /// Check if robot should return to dock
    pub fn should_return_to_dock(&self) -> bool {
        if self.battery_level < 20.0 {
            return true;
        }

        if let Some(dock_pos) = self.dock_position {
            let distance_to_dock = self.position.distance_to(&dock_pos);
            // Estimate battery needed to return
            let estimated_battery_needed = distance_to_dock * 0.1 * 1.5; // 50% safety margin
            if self.battery_level < estimated_battery_needed + 10.0 {
                return true;
            }
        }

        false
    }

    /// Charge the robot battery
    pub fn charge(&mut self, charge_rate: f64) -> bool {
        if self.state != RobotState::Charging {
            self.state = RobotState::Charging;
        }

        self.battery_level = (self.battery_level + charge_rate).min(self.battery_capacity);

        if self.battery_level >= self.battery_capacity {
            self.stats.battery_cycles += 1;
            log::info!("Battery fully charged");
            return true;
        }

        false
    }

    /// Set dock position
    pub fn set_dock_position(&mut self, position: Position) {
        self.dock_position = Some(position);
        log::info!("Dock position set to ({}, {})", position.x, position.y);
    }

    /// Reset statistics
    pub fn reset_stats(&mut self) {
        self.stats = RobotStats::default();
        self.cleaned_cells.clear();
        self.visited_cells.clear();
        self.path_history.clear();
        self.path_history.push(self.position);
        log::info!("Statistics reset");
    }

    /// Get robot status as JSON-serializable struct
    pub fn get_status(&self) -> RobotStatus {
        RobotStatus {
            position: self.position,
            battery_level: self.battery_level,
            state: self.state,
            mode: self.mode,
            heading: self.heading,
            sensor_data: self.sensor_data.clone(),
            stats: self.stats.clone(),
        }
    }
}

/// Serializable robot status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RobotStatus {
    pub position: Position,
    pub battery_level: f64,
    pub state: RobotState,
    pub mode: CleaningMode,
    pub heading: f64,
    pub sensor_data: SensorData,
    pub stats: RobotStats,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_robot_creation() {
        let robot = Robot::new(Position::new(10.0, 10.0));
        assert_eq!(robot.position, Position::new(10.0, 10.0));
        assert_eq!(robot.battery_level, 100.0);
        assert_eq!(robot.state, RobotState::Idle);
    }

    #[test]
    fn test_robot_with_params() {
        let robot = Robot::with_params(
            Position::new(5.0, 5.0),
            200.0,
            0.5,
            0.3,
            3.0,
        );
        assert_eq!(robot.battery_capacity, 200.0);
        assert_eq!(robot.cleaning_width, 0.5);
        assert_eq!(robot.speed, 0.3);
        assert_eq!(robot.sensor_range, 3.0);
    }

    #[test]
    fn test_robot_movement() {
        let mut robot = Robot::new(Position::new(10.0, 10.0));
        let initial_battery = robot.battery_level;

        let success = robot.move_by(1.0, 0.0);

        assert!(success);
        assert_eq!(robot.position, Position::new(11.0, 10.0));
        assert!(robot.battery_level < initial_battery);
        assert_eq!(robot.path_history.len(), 2);
    }

    #[test]
    fn test_robot_movement_with_depleted_battery() {
        let mut robot = Robot::new(Position::new(10.0, 10.0));
        robot.battery_level = 0.0;

        let success = robot.move_by(1.0, 1.0);

        assert!(!success);
        assert_eq!(robot.state, RobotState::Error);
    }

    #[test]
    fn test_should_return_to_dock_low_battery() {
        let mut robot = Robot::new(Position::new(10.0, 10.0));
        robot.battery_level = 15.0;
        assert!(robot.should_return_to_dock());
    }

    #[test]
    fn test_should_return_to_dock_sufficient_battery() {
        let robot = Robot::new(Position::new(10.0, 10.0));
        assert!(!robot.should_return_to_dock());
    }

    #[test]
    fn test_charging() {
        let mut robot = Robot::new(Position::new(10.0, 10.0));
        robot.battery_level = 50.0;
        robot.state = RobotState::Charging;

        let fully_charged = robot.charge(10.0);

        assert!(!fully_charged);
        assert_eq!(robot.battery_level, 60.0);

        // Charge until full
        for _ in 0..5 {
            robot.charge(10.0);
        }

        assert_eq!(robot.battery_level, 100.0);
    }

    #[test]
    fn test_dock_position() {
        let mut robot = Robot::new(Position::new(10.0, 10.0));
        robot.set_dock_position(Position::new(5.0, 5.0));

        assert_eq!(robot.dock_position, Some(Position::new(5.0, 5.0)));
    }

    #[test]
    fn test_stats_tracking() {
        let mut robot = Robot::new(Position::new(10.0, 10.0));

        robot.move_by(5.0, 0.0);
        robot.move_by(0.0, 5.0);

        assert!(robot.stats.total_distance > 0.0);
        assert!(!robot.cleaned_cells.is_empty());
        assert!(!robot.visited_cells.is_empty());
    }

    #[test]
    fn test_reset_stats() {
        let mut robot = Robot::new(Position::new(10.0, 10.0));

        robot.move_by(5.0, 5.0);
        robot.reset_stats();

        assert_eq!(robot.stats.total_distance, 0.0);
        assert_eq!(robot.stats.area_cleaned, 0);
        assert!(robot.cleaned_cells.is_empty());
        assert!(robot.visited_cells.is_empty());
    }

    #[test]
    fn test_get_status() {
        let robot = Robot::new(Position::new(10.0, 10.0));
        let status = robot.get_status();

        assert_eq!(status.position, robot.position);
        assert_eq!(status.battery_level, robot.battery_level);
        assert_eq!(status.state, robot.state);
    }
}

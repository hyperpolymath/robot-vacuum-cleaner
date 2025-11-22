//! Core types and data structures

use serde::{Deserialize, Serialize};
use std::ops::{Add, Sub};

/// 2D Position
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Position {
    pub x: f64,
    pub y: f64,
}

impl Position {
    /// Create a new position
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    /// Calculate Euclidean distance to another position
    pub fn distance_to(&self, other: &Position) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }

    /// Convert to grid coordinates
    pub fn to_grid(&self) -> (usize, usize) {
        (self.x as usize, self.y as usize)
    }

    /// Manhattan distance to another position
    pub fn manhattan_distance(&self, other: &Position) -> f64 {
        (self.x - other.x).abs() + (self.y - other.y).abs()
    }
}

impl Add for Position {
    type Output = Self;

    fn add(self, other: Self) -> Self {
        Self {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

impl Sub for Position {
    type Output = Self;

    fn sub(self, other: Self) -> Self {
        Self {
            x: self.x - other.x,
            y: self.y - other.y,
        }
    }
}

/// 2D Velocity vector
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Velocity {
    pub vx: f64,
    pub vy: f64,
}

impl Velocity {
    /// Create a new velocity
    pub fn new(vx: f64, vy: f64) -> Self {
        Self { vx, vy }
    }

    /// Get velocity magnitude
    pub fn magnitude(&self) -> f64 {
        (self.vx * self.vx + self.vy * self.vy).sqrt()
    }

    /// Normalize velocity to unit vector
    pub fn normalize(&self) -> Self {
        let mag = self.magnitude();
        if mag > 0.0 {
            Self {
                vx: self.vx / mag,
                vy: self.vy / mag,
            }
        } else {
            *self
        }
    }
}

/// 2D Pose (position + orientation)
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Pose {
    pub x: f64,
    pub y: f64,
    pub theta: f64, // Orientation in radians
}

impl Pose {
    /// Create a new pose
    pub fn new(x: f64, y: f64, theta: f64) -> Self {
        Self { x, y, theta }
    }

    /// Get position component
    pub fn position(&self) -> Position {
        Position::new(self.x, self.y)
    }

    /// Calculate distance to another pose
    pub fn distance_to(&self, other: &Pose) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }

    /// Calculate angular difference to another pose
    pub fn angle_to(&self, other: &Pose) -> f64 {
        let mut diff = other.theta - self.theta;

        // Normalize to [-π, π]
        while diff > std::f64::consts::PI {
            diff -= 2.0 * std::f64::consts::PI;
        }
        while diff < -std::f64::consts::PI {
            diff += 2.0 * std::f64::consts::PI;
        }

        diff
    }
}

/// Sensor readings
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SensorData {
    pub obstacle_front: bool,
    pub obstacle_left: bool,
    pub obstacle_right: bool,
    pub obstacle_back: bool,
    pub cliff_detected: bool,
    pub bumper_triggered: bool,
    pub distance_front: f64,
    pub distance_left: f64,
    pub distance_right: f64,
    pub distance_back: f64,
}

impl Default for SensorData {
    fn default() -> Self {
        Self {
            obstacle_front: false,
            obstacle_left: false,
            obstacle_right: false,
            obstacle_back: false,
            cliff_detected: false,
            bumper_triggered: false,
            distance_front: f64::INFINITY,
            distance_left: f64::INFINITY,
            distance_right: f64::INFINITY,
            distance_back: f64::INFINITY,
        }
    }
}

/// Robot statistics
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct RobotStats {
    pub total_distance: f64,
    pub area_cleaned: usize,
    pub cleaning_time: f64,
    pub battery_cycles: usize,
    pub errors_encountered: usize,
    pub stuck_count: usize,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::PI;

    #[test]
    fn test_position_distance() {
        let p1 = Position::new(0.0, 0.0);
        let p2 = Position::new(3.0, 4.0);
        assert!((p1.distance_to(&p2) - 5.0).abs() < 1e-10);
    }

    #[test]
    fn test_position_add() {
        let p1 = Position::new(1.0, 2.0);
        let p2 = Position::new(3.0, 4.0);
        let result = p1 + p2;
        assert_eq!(result, Position::new(4.0, 6.0));
    }

    #[test]
    fn test_position_sub() {
        let p1 = Position::new(5.0, 7.0);
        let p2 = Position::new(2.0, 3.0);
        let result = p1 - p2;
        assert_eq!(result, Position::new(3.0, 4.0));
    }

    #[test]
    fn test_position_to_grid() {
        let p = Position::new(5.7, 10.3);
        assert_eq!(p.to_grid(), (5, 10));
    }

    #[test]
    fn test_position_manhattan() {
        let p1 = Position::new(0.0, 0.0);
        let p2 = Position::new(3.0, 4.0);
        assert_eq!(p1.manhattan_distance(&p2), 7.0);
    }

    #[test]
    fn test_velocity_magnitude() {
        let v = Velocity::new(3.0, 4.0);
        assert!((v.magnitude() - 5.0).abs() < 1e-10);
    }

    #[test]
    fn test_velocity_normalize() {
        let v = Velocity::new(3.0, 4.0);
        let normalized = v.normalize();
        assert!((normalized.magnitude() - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_pose_position() {
        let pose = Pose::new(5.0, 10.0, PI / 2.0);
        let pos = pose.position();
        assert_eq!(pos, Position::new(5.0, 10.0));
    }

    #[test]
    fn test_pose_angle_to() {
        let pose1 = Pose::new(0.0, 0.0, 0.0);
        let pose2 = Pose::new(0.0, 0.0, PI / 2.0);
        let angle_diff = pose1.angle_to(&pose2);
        assert!((angle_diff - PI / 2.0).abs() < 1e-10);
    }

    #[test]
    fn test_sensor_data_default() {
        let sensor = SensorData::default();
        assert!(!sensor.obstacle_front);
        assert!(!sensor.cliff_detected);
        assert!(sensor.distance_front.is_infinite());
    }

    #[test]
    fn test_robot_stats_default() {
        let stats = RobotStats::default();
        assert_eq!(stats.total_distance, 0.0);
        assert_eq!(stats.area_cleaned, 0);
    }
}

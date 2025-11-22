//! Robot Vacuum Cleaner - High Performance Rust Implementation
//!
//! This library provides a high-performance implementation of a robot vacuum
//! cleaner simulator with advanced path planning, SLAM, and control algorithms.

pub mod robot;
pub mod environment;
pub mod pathfinding;
pub mod slam;
pub mod simulator;
pub mod types;

pub use robot::{Robot, RobotState, CleaningMode};
pub use environment::{Environment, CellType};
pub use simulator::Simulator;
pub use types::{Position, Velocity, Pose};

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Result type for robot vacuum operations
pub type Result<T> = anyhow::Result<T>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version() {
        assert!(!VERSION.is_empty());
    }
}

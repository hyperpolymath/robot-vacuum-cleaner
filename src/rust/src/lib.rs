// SPDX-License-Identifier: MPL-2.0
//! Robot Vacuum Cleaner - High Performance Rust Implementation
//!
//! This library provides a high-performance implementation of a robot vacuum
//! cleaner simulator with advanced path planning, SLAM, and control algorithms.

#![forbid(unsafe_code)]
pub mod environment;
pub mod pathfinding;
pub mod robot;
pub mod simulator;
pub mod slam;
pub mod types;

pub use environment::{CellType, Environment};
pub use robot::{CleaningMode, Robot, RobotState};
pub use simulator::{SimulationConfig, SimulationResults, Simulator};
pub use types::{Pose, Position, Velocity};

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

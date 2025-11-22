//! Simulation controller

use crate::robot::{Robot, RobotState};
use crate::environment::Environment;
use crate::pathfinding::AStarPlanner;

/// Simulation configuration
pub struct SimulationConfig {
    pub max_steps: usize,
    pub enable_slam: bool,
    pub tick_rate: f64,
}

impl Default for SimulationConfig {
    fn default() -> Self {
        Self {
            max_steps: 10000,
            enable_slam: false,
            tick_rate: 0.1,
        }
    }
}

/// Main simulator
pub struct Simulator {
    pub robot: Robot,
    pub environment: Environment,
    pub config: SimulationConfig,
    pub steps: usize,
}

impl Simulator {
    /// Create new simulator
    pub fn new(robot: Robot, environment: Environment, config: SimulationConfig) -> Self {
        Self {
            robot,
            environment,
            config,
            steps: 0,
        }
    }

    /// Execute one simulation step
    pub fn step(&mut self) -> bool {
        self.steps += 1;
        self.environment.step(self.config.tick_rate);

        // Simple simulation logic
        match self.robot.state {
            RobotState::Idle => {
                self.robot.state = RobotState::Cleaning;
            }
            RobotState::Cleaning => {
                // Check if should return to dock
                if self.robot.should_return_to_dock() {
                    self.robot.state = RobotState::ReturningToDock;
                }
            }
            RobotState::Charging => {
                if self.robot.charge(10.0) {
                    self.robot.state = RobotState.Cleaning;
                }
            }
            _ => {}
        }

        // Check max steps
        if self.steps >= self.config.max_steps {
            return false;
        }

        true
    }

    /// Run complete simulation
    pub fn run(&mut self) -> SimulationResults {
        log::info!("Starting simulation");

        while self.step() {
            // Simulation loop
        }

        log::info!("Simulation complete after {} steps", self.steps);

        SimulationResults {
            steps: self.steps,
            cleaning_coverage: self.environment.get_cleaning_percentage(),
            total_distance: self.robot.stats.total_distance,
            battery_cycles: self.robot.stats.battery_cycles,
            success: self.robot.state != RobotState::Error,
        }
    }
}

/// Simulation results
#[derive(Debug, Clone)]
pub struct SimulationResults {
    pub steps: usize,
    pub cleaning_coverage: f64,
    pub total_distance: f64,
    pub battery_cycles: usize,
    pub success: bool,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::Position;

    #[test]
    fn test_simulator_creation() {
        let robot = Robot::new(Position::new(15.0, 15.0));
        let env = Environment::create_empty_room(30, 30);
        let config = SimulationConfig::default();

        let sim = Simulator::new(robot, env, config);

        assert_eq!(sim.steps, 0);
    }

    #[test]
    fn test_simulator_step() {
        let robot = Robot::new(Position::new(15.0, 15.0));
        let env = Environment::create_empty_room(30, 30);
        let config = SimulationConfig::default();

        let mut sim = Simulator::new(robot, env, config);

        let should_continue = sim.step();

        assert!(should_continue);
        assert_eq!(sim.steps, 1);
    }
}

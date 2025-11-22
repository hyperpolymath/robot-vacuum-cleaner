//! Environment simulation

use ndarray::Array2;
use serde::{Deserialize, Serialize};

/// Cell types in the environment
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[repr(u8)]
pub enum CellType {
    Free = 0,
    Obstacle = 1,
    Cliff = 2,
    Dock = 3,
}

impl From<u8> for CellType {
    fn from(value: u8) -> Self {
        match value {
            0 => CellType::Free,
            1 => CellType::Obstacle,
            2 => CellType::Cliff,
            3 => CellType::Dock,
            _ => CellType::Free,
        }
    }
}

/// Environment representation
#[derive(Debug, Clone)]
pub struct Environment {
    pub grid: Array2<u8>,
    pub width: usize,
    pub height: usize,
    pub dock_position: Option<(usize, usize)>,
    pub dirty_map: Array2<bool>,
    pub sim_time: f64,
}

impl Environment {
    /// Create a new environment
    pub fn new(width: usize, height: usize) -> Self {
        let grid = Array2::zeros((height, width));
        let dirty_map = Array2::from_elem((height, width), true);

        Self {
            grid,
            width,
            height,
            dock_position: None,
            dirty_map,
            sim_time: 0.0,
        }
    }

    /// Create environment from existing grid
    pub fn from_grid(grid: Array2<u8>) -> Self {
        let (height, width) = grid.dim();
        let dirty_map = Array2::from_elem((height, width), true);

        // Find dock position
        let mut dock_position = None;
        for ((y, x), &cell) in grid.indexed_iter() {
            if cell == CellType::Dock as u8 {
                dock_position = Some((x, y));
                break;
            }
        }

        Self {
            grid,
            width,
            height,
            dock_position,
            dirty_map,
            sim_time: 0.0,
        }
    }

    /// Create an empty room with walls
    pub fn create_empty_room(width: usize, height: usize) -> Self {
        let mut grid = Array2::zeros((height, width));

        // Add walls
        for x in 0..width {
            grid[[0, x]] = CellType::Obstacle as u8;
            grid[[height - 1, x]] = CellType::Obstacle as u8;
        }

        for y in 0..height {
            grid[[y, 0]] = CellType::Obstacle as u8;
            grid[[y, width - 1]] = CellType::Obstacle as u8;
        }

        Self::from_grid(grid)
    }

    /// Check if position is valid (not obstacle or cliff)
    pub fn is_valid_position(&self, x: usize, y: usize) -> bool {
        if x >= self.width || y >= self.height {
            return false;
        }

        let cell_type = CellType::from(self.grid[[y, x]]);
        matches!(cell_type, CellType::Free | CellType::Dock)
    }

    /// Clean a cell
    pub fn clean_cell(&mut self, x: usize, y: usize) {
        if x < self.width && y < self.height {
            self.dirty_map[[y, x]] = false;
        }
    }

    /// Check if cell is dirty
    pub fn is_dirty(&self, x: usize, y: usize) -> bool {
        if x < self.width && y < self.height {
            self.dirty_map[[y, x]]
        } else {
            false
        }
    }

    /// Get cleaning percentage
    pub fn get_cleaning_percentage(&self) -> f64 {
        let total_cleanable = self.grid.iter()
            .filter(|&&cell| cell == CellType::Free as u8)
            .count();

        if total_cleanable == 0 {
            return 100.0;
        }

        let cleaned = self.grid.indexed_iter()
            .filter(|&((y, x), &cell)| {
                cell == CellType::Free as u8 && !self.dirty_map[[y, x]]
            })
            .count();

        (cleaned as f64 / total_cleanable as f64) * 100.0
    }

    /// Step simulation
    pub fn step(&mut self, delta_time: f64) {
        self.sim_time += delta_time;
    }

    /// Reset environment
    pub fn reset(&mut self) {
        self.dirty_map.fill(true);
        self.sim_time = 0.0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_environment_creation() {
        let env = Environment::new(50, 40);
        assert_eq!(env.width, 50);
        assert_eq!(env.height, 40);
        assert_eq!(env.sim_time, 0.0);
    }

    #[test]
    fn test_create_empty_room() {
        let env = Environment::create_empty_room(30, 30);
        assert_eq!(env.grid[[0, 15]], CellType::Obstacle as u8); // Top wall
        assert_eq!(env.grid[[29, 15]], CellType::Obstacle as u8); // Bottom wall
        assert_eq!(env.grid[[15, 0]], CellType::Obstacle as u8); // Left wall
        assert_eq!(env.grid[[15, 29]], CellType::Obstacle as u8); // Right wall
        assert_eq!(env.grid[[15, 15]], CellType::Free as u8); // Center
    }

    #[test]
    fn test_is_valid_position() {
        let env = Environment::create_empty_room(30, 30);
        assert!(env.is_valid_position(15, 15)); // Center is valid
        assert!(!env.is_valid_position(0, 0)); // Wall is not valid
        assert!(!env.is_valid_position(100, 100)); // Out of bounds
    }

    #[test]
    fn test_clean_cell() {
        let mut env = Environment::create_empty_room(30, 30);
        assert!(env.is_dirty(15, 15));

        env.clean_cell(15, 15);
        assert!(!env.is_dirty(15, 15));
    }

    #[test]
    fn test_cleaning_percentage() {
        let mut env = Environment::create_empty_room(30, 30);
        let initial_pct = env.get_cleaning_percentage();
        assert!(initial_pct < 1.0);

        // Clean some cells
        for x in 10..20 {
            for y in 10..20 {
                if env.is_valid_position(x, y) {
                    env.clean_cell(x, y);
                }
            }
        }

        let final_pct = env.get_cleaning_percentage();
        assert!(final_pct > initial_pct);
    }

    #[test]
    fn test_environment_step() {
        let mut env = Environment::new(30, 30);
        env.step(0.1);
        assert!((env.sim_time - 0.1).abs() < 1e-10);
    }

    #[test]
    fn test_environment_reset() {
        let mut env = Environment::create_empty_room(30, 30);
        env.clean_cell(15, 15);
        env.sim_time = 100.0;

        env.reset();

        assert!(env.is_dirty(15, 15));
        assert_eq!(env.sim_time, 0.0);
    }

    #[test]
    fn test_cell_type_conversion() {
        assert_eq!(CellType::from(0), CellType::Free);
        assert_eq!(CellType::from(1), CellType::Obstacle);
        assert_eq!(CellType::from(2), CellType::Cliff);
        assert_eq!(CellType::from(3), CellType::Dock);
        assert_eq!(CellType::from(99), CellType::Free); // Unknown defaults to Free
    }
}

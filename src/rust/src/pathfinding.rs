//! Path finding and coverage planning algorithms

use crate::types::Position;
use crate::environment::Environment;
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::cmp::Ordering;

/// A* pathfinding node
#[derive(Debug, Clone)]
struct AStarNode {
    position: (usize, usize),
    g_cost: f64,
    h_cost: f64,
    parent: Option<(usize, usize)>,
}

impl AStarNode {
    fn f_cost(&self) -> f64 {
        self.g_cost + self.h_cost
    }
}

impl PartialEq for AStarNode {
    fn eq(&self, other: &Self) -> bool {
        self.f_cost() == other.f_cost()
    }
}

impl Eq for AStarNode {}

impl PartialOrd for AStarNode {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        other.f_cost().partial_cmp(&self.f_cost())
    }
}

impl Ord for AStarNode {
    fn cmp(&self, other: &Self) -> Ordering {
        self.partial_cmp(other).unwrap_or(Ordering::Equal)
    }
}

/// A* pathfinding algorithm
pub struct AStarPlanner<'a> {
    environment: &'a Environment,
}

impl<'a> AStarPlanner<'a> {
    /// Create new A* planner
    pub fn new(environment: &'a Environment) -> Self {
        Self { environment }
    }

    /// Manhattan distance heuristic
    fn heuristic(&self, pos1: (usize, usize), pos2: (usize, usize)) -> f64 {
        ((pos1.0 as i32 - pos2.0 as i32).abs() + (pos1.1 as i32 - pos2.1 as i32).abs()) as f64
    }

    /// Get valid neighbors
    fn get_neighbors(&self, pos: (usize, usize), diagonal: bool) -> Vec<(usize, usize)> {
        let mut neighbors = Vec::new();
        let (x, y) = pos;

        // Cardinal directions
        for (dx, dy) in [(0, 1), (1, 0), (0, -1), (-1, 0)].iter() {
            let nx = (x as i32 + dx) as usize;
            let ny = (y as i32 + dy) as usize;

            if self.environment.is_valid_position(nx, ny) {
                neighbors.push((nx, ny));
            }
        }

        // Diagonal directions
        if diagonal {
            for (dx, dy) in [(1, 1), (1, -1), (-1, 1), (-1, -1)].iter() {
                let nx = (x as i32 + dx) as usize;
                let ny = (y as i32 + dy) as usize;

                if self.environment.is_valid_position(nx, ny) {
                    neighbors.push((nx, ny));
                }
            }
        }

        neighbors
    }

    /// Find path from start to goal
    pub fn find_path(
        &self,
        start: (usize, usize),
        goal: (usize, usize),
        diagonal: bool,
    ) -> Option<Vec<(usize, usize)>> {
        if !self.environment.is_valid_position(start.0, start.1)
            || !self.environment.is_valid_position(goal.0, goal.1)
        {
            return None;
        }

        let mut open_set = BinaryHeap::new();
        let mut closed_set = HashSet::new();
        let mut node_map: HashMap<(usize, usize), AStarNode> = HashMap::new();

        let start_node = AStarNode {
            position: start,
            g_cost: 0.0,
            h_cost: self.heuristic(start, goal),
            parent: None,
        };

        open_set.push(start_node.clone());
        node_map.insert(start, start_node);

        while let Some(current) = open_set.pop() {
            if current.position == goal {
                // Reconstruct path
                let mut path = Vec::new();
                let mut pos = goal;

                while let Some(node) = node_map.get(&pos) {
                    path.push(pos);
                    if let Some(parent) = node.parent {
                        pos = parent;
                    } else {
                        break;
                    }
                }

                path.reverse();
                return Some(path);
            }

            closed_set.insert(current.position);

            for neighbor_pos in self.get_neighbors(current.position, diagonal) {
                if closed_set.contains(&neighbor_pos) {
                    continue;
                }

                let move_cost = if neighbor_pos.0 == current.position.0
                    || neighbor_pos.1 == current.position.1
                {
                    1.0
                } else {
                    1.414 // sqrt(2) for diagonal
                };

                let g_cost = current.g_cost + move_cost;
                let h_cost = self.heuristic(neighbor_pos, goal);

                let neighbor_node = AStarNode {
                    position: neighbor_pos,
                    g_cost,
                    h_cost,
                    parent: Some(current.position),
                };

                if let Some(existing) = node_map.get(&neighbor_pos) {
                    if g_cost < existing.g_cost {
                        node_map.insert(neighbor_pos, neighbor_node.clone());
                        open_set.push(neighbor_node);
                    }
                } else {
                    node_map.insert(neighbor_pos, neighbor_node.clone());
                    open_set.push(neighbor_node);
                }
            }
        }

        None // No path found
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_astar_straight_line() {
        let env = Environment::create_empty_room(30, 30);
        let planner = AStarPlanner::new(&env);

        let path = planner.find_path((5, 5), (10, 5), false);

        assert!(path.is_some());
        let path = path.unwrap();
        assert!(!path.is_empty());
        assert_eq!(path[0], (5, 5));
        assert_eq!(path[path.len() - 1], (10, 5));
    }

    #[test]
    fn test_astar_diagonal() {
        let env = Environment::create_empty_room(30, 30);
        let planner = AStarPlanner::new(&env);

        let path_diagonal = planner.find_path((5, 5), (10, 10), true);
        let path_straight = planner.find_path((5, 5), (10, 10), false);

        assert!(path_diagonal.is_some());
        assert!(path_straight.is_some());

        // Diagonal path should be shorter
        assert!(path_diagonal.unwrap().len() < path_straight.unwrap().len());
    }

    #[test]
    fn test_heuristic() {
        let env = Environment::new(10, 10);
        let planner = AStarPlanner::new(&env);

        let dist = planner.heuristic((0, 0), (3, 4));
        assert_eq!(dist, 7.0); // Manhattan distance
    }
}

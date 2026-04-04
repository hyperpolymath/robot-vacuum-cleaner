// SPDX-License-Identifier: PMPL-1.0-or-later
//! Benchmarks for robot vacuum operations
//!
//! Performance baseline tests for critical operations

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use robot_vacuum_cleaner::{Robot, Position, Environment, Simulator, SimulationConfig};

fn bench_robot_creation(c: &mut Criterion) {
    c.bench_function("robot_creation", |b| {
        b.iter(|| {
            let pos = black_box(Position::new(25.0, 25.0));
            Robot::new(pos)
        });
    });
}

fn bench_robot_movement(c: &mut Criterion) {
    c.bench_function("robot_movement_single", |b| {
        let mut robot = Robot::new(Position::new(25.0, 25.0));
        b.iter(|| {
            let dx = black_box(1.0);
            let dy = black_box(1.0);
            robot.move_by(dx, dy)
        });
    });
}

fn bench_robot_movement_sequence(c: &mut Criterion) {
    c.bench_function("robot_movement_100_steps", |b| {
        b.iter(|| {
            let mut robot = Robot::new(Position::new(25.0, 25.0));
            for i in 0..100 {
                if robot.battery_level > 0.0 {
                    let dx = if i % 2 == 0 { 1.0 } else { -1.0 };
                    robot.move_by(dx, 0.0);
                }
            }
            black_box(robot)
        });
    });
}

fn bench_position_distance(c: &mut Criterion) {
    c.bench_function("position_euclidean_distance", |b| {
        let p1 = Position::new(0.0, 0.0);
        let p2 = Position::new(100.0, 100.0);
        b.iter(|| {
            let pos1 = black_box(&p1);
            let pos2 = black_box(&p2);
            pos1.distance_to(pos2)
        });
    });
}

fn bench_position_manhattan_distance(c: &mut Criterion) {
    c.bench_function("position_manhattan_distance", |b| {
        let p1 = Position::new(0.0, 0.0);
        let p2 = Position::new(100.0, 100.0);
        b.iter(|| {
            let pos1 = black_box(&p1);
            let pos2 = black_box(&p2);
            pos1.manhattan_distance(pos2)
        });
    });
}

fn bench_battery_consumption(c: &mut Criterion) {
    c.bench_function("battery_depletion_50_steps", |b| {
        b.iter(|| {
            let mut robot = Robot::new(Position::new(25.0, 25.0));
            for _ in 0..50 {
                if robot.battery_level > 0.0 {
                    robot.move_by(black_box(0.5), black_box(0.5));
                }
            }
            black_box(robot.battery_level)
        });
    });
}

fn bench_charging(c: &mut Criterion) {
    c.bench_function("battery_charging_to_full", |b| {
        b.iter(|| {
            let mut robot = Robot::new(Position::new(25.0, 25.0));
            robot.battery_level = 50.0;
            robot.state = robot_vacuum_cleaner::RobotState::Charging;
            while robot.battery_level < 100.0 {
                robot.charge(10.0);
            }
            black_box(robot.battery_level)
        });
    });
}

fn bench_environment_small(c: &mut Criterion) {
    c.bench_function("environment_creation_10x10", |b| {
        b.iter(|| {
            let env = Environment::new(black_box(10), black_box(10));
            black_box(env)
        });
    });
}

fn bench_environment_medium(c: &mut Criterion) {
    c.bench_function("environment_creation_50x50", |b| {
        b.iter(|| {
            let env = Environment::new(black_box(50), black_box(50));
            black_box(env)
        });
    });
}

fn bench_environment_large(c: &mut Criterion) {
    c.bench_function("environment_creation_200x200", |b| {
        b.iter(|| {
            let env = Environment::new(black_box(200), black_box(200));
            black_box(env)
        });
    });
}

fn bench_cleaning_percentage(c: &mut Criterion) {
    let env = Environment::new(50, 50);
    c.bench_function("cleaning_percentage_calculation_50x50", |b| {
        b.iter(|| {
            let e = black_box(&env);
            e.get_cleaning_percentage()
        });
    });
}

fn bench_simulator_step_small(c: &mut Criterion) {
    c.bench_function("simulator_step_small_env", |b| {
        let robot = Robot::new(Position::new(15.0, 15.0));
        let env = Environment::new(30, 30);
        let config = SimulationConfig::default();
        let mut sim = Simulator::new(robot, env, config);

        b.iter(|| {
            let should_continue = black_box(sim.step());
            black_box(should_continue)
        });
    });
}

fn bench_simulator_run_short(c: &mut Criterion) {
    c.bench_function("simulator_run_100_steps", |b| {
        b.iter(|| {
            let robot = Robot::new(Position::new(25.0, 25.0));
            let env = Environment::new(50, 50);
            let config = SimulationConfig {
                max_steps: 100,
                enable_slam: false,
                tick_rate: 0.1,
            };
            let mut sim = Simulator::new(robot, env, config);
            let results = sim.run();
            black_box(results)
        });
    });
}

fn bench_simulator_run_long(c: &mut Criterion) {
    c.bench_function("simulator_run_1000_steps", |b| {
        b.iter(|| {
            let robot = Robot::new(Position::new(25.0, 25.0));
            let env = Environment::new(50, 50);
            let config = SimulationConfig {
                max_steps: 1000,
                enable_slam: false,
                tick_rate: 0.1,
            };
            let mut sim = Simulator::new(robot, env, config);
            let results = sim.run();
            black_box(results)
        });
    });
}

fn bench_stats_tracking(c: &mut Criterion) {
    c.bench_function("stats_accumulation_100_moves", |b| {
        b.iter(|| {
            let mut robot = Robot::new(Position::new(25.0, 25.0));
            for i in 0..100 {
                let dx = if i % 2 == 0 { 0.5 } else { -0.5 };
                robot.move_by(dx, 0.0);
            }
            black_box((robot.stats.total_distance, robot.stats.area_cleaned))
        });
    });
}

fn bench_dock_decision(c: &mut Criterion) {
    c.bench_function("should_return_to_dock_decision", |b| {
        let mut robot = Robot::new(Position::new(25.0, 25.0));
        robot.set_dock_position(Position::new(25.0, 25.0));

        b.iter(|| {
            let should_return = black_box(robot.should_return_to_dock());
            black_box(should_return)
        });
    });
}

fn bench_cleaning_cells_tracking(c: &mut Criterion) {
    c.bench_function("cleaned_cells_tracking_50_moves", |b| {
        b.iter(|| {
            let mut robot = Robot::new(Position::new(25.0, 25.0));
            for i in 0..50 {
                if robot.battery_level > 0.0 {
                    let angle = i as f64 * 0.1;
                    let dx = angle.cos();
                    let dy = angle.sin();
                    robot.move_by(dx, dy);
                }
            }
            black_box((robot.cleaned_cells.len(), robot.visited_cells.len()))
        });
    });
}

criterion_group!(
    benches,
    bench_robot_creation,
    bench_robot_movement,
    bench_robot_movement_sequence,
    bench_position_distance,
    bench_position_manhattan_distance,
    bench_battery_consumption,
    bench_charging,
    bench_environment_small,
    bench_environment_medium,
    bench_environment_large,
    bench_cleaning_percentage,
    bench_simulator_step_small,
    bench_simulator_run_short,
    bench_simulator_run_long,
    bench_stats_tracking,
    bench_dock_decision,
    bench_cleaning_cells_tracking,
);

criterion_main!(benches);

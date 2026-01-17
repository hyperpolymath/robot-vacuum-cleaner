// SPDX-License-Identifier: MIT
//! Pathfinding algorithm benchmarks

use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_astar(_c: &mut Criterion) {
    // TODO: Implement pathfinding benchmarks when pathfinding module is available
}

criterion_group!(benches, benchmark_astar);
criterion_main!(benches);

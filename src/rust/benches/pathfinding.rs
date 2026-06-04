// SPDX-License-Identifier: MPL-2.0
// Copyright (c) Jonathan D.A. Jewell <j.d.a.jewell@open.ac.uk>
//! Pathfinding algorithm benchmarks

use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_astar(_c: &mut Criterion) {
    // TODO: Implement pathfinding benchmarks when pathfinding module is available
}

criterion_group!(benches, benchmark_astar);
criterion_main!(benches);

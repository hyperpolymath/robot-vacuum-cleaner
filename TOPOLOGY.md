<!-- SPDX-License-Identifier: PMPL-1.0-or-later -->
<!-- TOPOLOGY.md — Project architecture map and completion dashboard -->
<!-- Last updated: 2026-02-19 -->

# Robot Vacuum Cleaner — Project Topology

## System Architecture

```
                        ┌─────────────────────────────────────────┐
                        │              OPERATOR / CLIENT          │
                        │        (GraphQL API, Web Dashboard)     │
                        └───────────────────┬─────────────────────┘
                                            │
                                            ▼
                        ┌─────────────────────────────────────────┐
                        │           SIMULATION CONTROLLER         │
                        │  ┌───────────┐  ┌───────────────────┐  │
                        │  │ Julia API │  │  Rust Compute     │  │
                        │  │ (GraphQL) │  │  Core             │  │
                        │  └─────┬─────┘  └────────┬──────────┘  │
                        └────────│─────────────────│──────────────┘
                                 │                 │
                                 ▼                 ▼
                        ┌─────────────────────────────────────────┐
                        │           SIMULATION ENGINE             │
                        │  ┌───────────┐  ┌───────────────────┐  │
                        │  │ Path      │  │  SLAM System      │  │
                        │  │ Planning  │  │  (Particle Filter)│  │
                        │  └─────┬─────┘  └────────┬──────────┘  │
                        └────────│─────────────────│──────────────┘
                                 │                 │
                                 ▼                 ▼
                        ┌─────────────────────────────────────────┐
                        │             VIRTUAL WORLD               │
                        │  ┌───────────┐  ┌───────────────────┐  │
                        │  │ Room Map  │  │  Sensor Sim       │  │
                        │  │ (Occupancy)│ │  (Bumper/Cliff)   │  │
                        │  └───────────┘  └───────────────────┘  │
                        └─────────────────────────────────────────┘

                        ┌─────────────────────────────────────────┐
                        │          REPO INFRASTRUCTURE            │
                        │  Justfile Automation  .machine_readable/  │
                        │  Wolfi Containers     Prometheus/Grafana  │
                        └─────────────────────────────────────────┘
```

## Completion Dashboard

```
COMPONENT                          STATUS              NOTES
─────────────────────────────────  ──────────────────  ─────────────────────────────────
CORE SIMULATION
  Julia Simulator (main.jl)         ██████████ 100%    High-perf numericals stable
  Rust Compute Core                 ██████████ 100%    Compute-intensive ops verified
  Path Planning (A*, Spiral)        ██████████ 100%    All 5 algorithms active
  SLAM Implementation               ████████░░  80%    Particle filter stable

INTERFACES & INFRA
  GraphQL API (Julia)               ██████████ 100%    Mutation/Query hooks verified
  Real-time Visualization           ██████████ 100%    matplotlib integration stable
  Monitoring (Prometheus)           ██████████ 100%    Metrics collection verified

REPO INFRASTRUCTURE
  Justfile Automation               ██████████ 100%    Standard build/setup tasks
  .machine_readable/                ██████████ 100%    STATE tracking active
  Wolfi / Chainguard Build          ██████████ 100%    Reproducible containers stable

─────────────────────────────────────────────────────────────────────────────
OVERALL:                            █████████░  ~90%   Feature-complete simulator
```

## Key Dependencies

```
Room Map ────────► SLAM System ───────► Path Planning ──────► Movement
     │                 │                   │                    │
     ▼                 ▼                   ▼                    ▼
Sensor Sim ──────► State Update ─────► Julia Engine ───────► GraphQL
```

## Update Protocol

This file is maintained by both humans and AI agents. When updating:

1. **After completing a component**: Change its bar and percentage
2. **After adding a component**: Add a new row in the appropriate section
3. **After architectural changes**: Update the ASCII diagram
4. **Date**: Update the `Last updated` comment at the top of this file

Progress bars use: `█` (filled) and `░` (empty), 10 characters wide.
Percentages: 0%, 10%, 20%, ... 100% (in 10% increments).

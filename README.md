# Robot Vacuum Cleaner Simulator

A comprehensive, production-grade robot vacuum cleaner simulation system with dual Python and Rust implementations, GraphQL API, SLAM algorithms, and enterprise CI/CD infrastructure.

[![CI/CD](https://github.com/Hyperpolymath/robot-vacuum-cleaner/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/Hyperpolymath/robot-vacuum-cleaner/actions)
[![codecov](https://codecov.io/gh/Hyperpolymath/robot-vacuum-cleaner/branch/main/graph/badge.svg)](https://codecov.io/gh/Hyperpolymath/robot-vacuum-cleaner)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

### Core Functionality
- **Autonomous Navigation**: Advanced path planning with multiple algorithms (A*, spiral, zigzag, wall-follow, random)
- **SLAM Implementation**: Simultaneous Localization and Mapping with particle filter
- **Sensor Simulation**: Obstacle detection, cliff detection, bumper sensors
- **Battery Management**: Realistic battery consumption and charging dock behavior
- **Multiple Cleaning Modes**: Auto, spot, edge, spiral, zigzag, wall-follow, random
- **Real-time Visualization**: matplotlib-based visualization of robot behavior and environment

### Technology Stack

#### Languages & Frameworks
- **Python 3.11+**: Primary simulation and API implementation
- **Rust**: High-performance variant for compute-intensive operations
- **GraphQL**: Strawberry + FastAPI for modern API layer
- **NumPy/SciPy**: Numerical computing and algorithms

#### Infrastructure
- **Containers**: Podman with Chainguard Wolfi base images for supply chain security
- **CI/CD**: Comprehensive GitHub Actions and GitLab CI pipelines
- **Monitoring**: Prometheus + Grafana stack
- **Salt**: Offline development and maintenance support

#### Security & Quality
- **Security Scanning**: Trivy, GitLeaks, Bandit, OWASP Dependency Check, Snyk
- **Code Quality**: Black, isort, Flake8, Pylint, MyPy, Rust clippy
- **Testing**: pytest with 70%+ coverage requirement, Rust cargo test
- **Pre-commit Hooks**: Automated linting, formatting, and security checks

## Quick Start

### Prerequisites

```bash
# Python 3.11+
python --version

# Rust (latest stable)
rustc --version

# Podman or Docker
podman --version

# Salt (optional, for infrastructure management)
salt-call --version
```

### Installation

#### Python Environment

```bash
# Clone repository
git clone https://github.com/Hyperpolymath/robot-vacuum-cleaner.git
cd robot-vacuum-cleaner

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Install git hooks
./scripts/install-hooks.sh
```

#### Rust Build

```bash
cd src/rust
cargo build --release
cargo test
```

#### Container Build

```bash
# Build with Podman
podman build -f docker/Containerfile -t robot-vacuum:latest .

# Or use compose
podman-compose -f docker/compose.yaml up -d
```

### Usage

#### Python Simulator

```python
from src.python.simulator import SimulationConfig, SimulationController
from src.python.visualization import quick_visualize

# Configure simulation
config = SimulationConfig(
    room_type='furnished',
    cleaning_mode='zigzag',
    max_steps=5000,
    enable_slam=True,
    random_seed=42
)

# Run simulation
sim = SimulationController(config)
for _ in range(1000):
    if not sim.step():
        break

# Visualize results
quick_visualize(sim)

# Get results
results = sim.get_results()
print(f"Coverage: {results['cleaning_coverage']:.2f}%")
```

#### GraphQL API

```bash
# Start the API server
python src/graphql/server.py

# Or with uvicorn
uvicorn src.graphql.server:app --host 0.0.0.0 --port 8000

# Access GraphQL playground
open http://localhost:8000/graphql
```

Example GraphQL queries:

```graphql
# Get robot status
query {
  robotStatus {
    position { x y }
    batteryLevel
    state
    stats {
      totalDistance
      areaCleaned
    }
  }
}

# Start cleaning
mutation {
  startCleaning(mode: "zigzag") {
    success
    message
  }
}
```

#### Rust CLI

```bash
# Build and run
cd src/rust
cargo run --release -- --width 50 --height 50 --max-steps 10000

# With options
cargo run --release -- \
  --width 80 \
  --height 60 \
  --max-steps 15000 \
  --slam \
  --start-x 40.0 \
  --start-y 30.0 \
  --verbose
```

## Architecture

### Project Structure

```
robot-vacuum-cleaner/
├── src/
│   ├── python/          # Python implementation
│   │   ├── robot.py           # Robot core
│   │   ├── environment.py     # Environment simulation
│   │   ├── pathplanning.py    # Path planning algorithms
│   │   ├── slam.py            # SLAM implementation
│   │   ├── simulator.py       # Simulation controller
│   │   └── visualization.py   # Visualization module
│   ├── rust/            # Rust implementation
│   │   ├── src/
│   │   │   ├── robot.rs
│   │   │   ├── environment.rs
│   │   │   ├── pathfinding.rs
│   │   │   ├── slam.rs
│   │   │   └── simulator.rs
│   │   └── Cargo.toml
│   └── graphql/         # GraphQL API
│       ├── schema.graphql
│       └── server.py
├── tests/
│   ├── python/          # Python tests
│   └── integration/     # Integration tests
├── docker/              # Container configurations
│   ├── Containerfile    # Production container
│   ├── Containerfile.dev
│   └── compose.yaml
├── .github/
│   └── workflows/       # GitHub Actions CI/CD
├── .gitlab-ci.yml       # GitLab CI/CD
├── salt/                # Salt configuration
│   ├── minion.d/
│   └── states/
├── hooks/               # Git hooks
├── scripts/             # Utility scripts
├── monitoring/          # Prometheus/Grafana configs
└── docs/                # Documentation

```

### Path Planning Algorithms

1. **A\* Pathfinding**: Optimal path to goal with configurable heuristics
2. **Spiral Coverage**: Expanding spiral pattern from center
3. **Zigzag (Boustrophedon)**: Systematic row-by-row coverage
4. **Wall Following**: Right-hand rule for perimeter coverage
5. **Random Walk**: Coverage-optimized random exploration

### SLAM System

- **Occupancy Grid Mapping**: Probabilistic grid representation
- **Particle Filter**: Monte Carlo localization
- **Log-odds Updates**: Efficient probability updates
- **Bresenham Ray Tracing**: Fast line-of-sight calculations

## Development

### Running Tests

```bash
# Python tests
pytest tests/python/ -v --cov=src/python

# Rust tests
cd src/rust && cargo test

# Integration tests
pytest tests/integration/ -v

# With coverage report
pytest --cov=src/python --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/
cd src/rust && cargo fmt

# Lint
flake8 src/ tests/
pylint src/
cd src/rust && cargo clippy

# Type checking
mypy src/

# Security scanning
bandit -r src/python/
trivy fs .
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## CI/CD

### GitHub Actions

Comprehensive pipeline including:
- Code quality checks (Black, isort, Flake8, Pylint, MyPy)
- Security scanning (Trivy, GitLeaks, Bandit, Snyk, OWASP)
- Multi-version Python testing (3.10, 3.11, 3.12)
- Rust testing and clippy
- Container building and scanning
- SonarCloud analysis
- Integration tests
- Automated deployment

### GitLab CI

Mirror of GitHub Actions with additional features:
- Scheduled security scans
- Multiple environment deployments (staging, production)
- Dependency caching
- Parallel test execution
- Custom runners support

## Container Deployment

### Development

```bash
# Start development stack
podman-compose -f docker/compose.yaml --profile dev up -d

# View logs
podman-compose -f docker/compose.yaml logs -f api-dev

# Stop services
podman-compose -f docker/compose.yaml down
```

### Production

```bash
# Build production image
podman build -f docker/Containerfile -t robot-vacuum:latest .

# Run with monitoring
podman-compose -f docker/compose.yaml --profile monitoring up -d

# Access services
# API: http://localhost:8000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

## Monitoring

### Prometheus Metrics

- Robot battery level
- Cleaning coverage percentage
- Distance traveled
- API request rates
- Error rates
- System resources

### Grafana Dashboards

Pre-configured dashboards for:
- Robot status overview
- Cleaning performance
- API performance
- System health

Access: http://localhost:3000 (admin/admin)

## Salt Infrastructure

### Development Environment Setup

```bash
# Apply development state
salt-call --local state.apply development

# Setup CI/CD tools
salt-call --local state.apply cicd

# Configure monitoring
salt-call --local state.apply monitoring
```

### Offline Support

Salt minion configuration enables:
- Automated dependency installation
- Development environment provisioning
- Build and test orchestration
- Offline CI/CD execution

## Security

### Supply Chain Security

- **Chainguard Wolfi**: Minimal, security-focused container base images
- **Trivy Scanning**: Container and filesystem vulnerability detection
- **SBOM Generation**: Software Bill of Materials with Syft
- **Dependency Scanning**: Regular security audits
- **GitLeaks**: Secrets detection in commits

### Security Best Practices

- No secrets in code or containers
- Regular dependency updates
- Automated security scanning in CI
- Supply chain verification
- Least privilege access

## Performance

### Python Performance

- NumPy vectorization for grid operations
- Efficient path planning with A*
- Optimized SLAM updates
- Memory-efficient data structures

### Rust Performance

- Zero-cost abstractions
- SIMD optimizations where applicable
- Parallel processing with Rayon
- Release build optimizations (LTO, codegen-units=1)

### Benchmarks

Run benchmarks:

```bash
cd src/rust
cargo bench --features benchmarks
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Ensure all tests pass and pre-commit hooks succeed
5. Commit with conventional commit format
6. Push to your fork
7. Open a Pull Request

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build

## License

MIT License - see LICENSE file for details

## Acknowledgments

- SLAM algorithms inspired by probabilistic robotics research
- Path planning based on classical robotics algorithms
- Container security following Chainguard best practices
- CI/CD patterns from industry standards

## Roadmap

- [ ] Advanced SLAM with loop closure
- [ ] Multi-robot coordination
- [ ] Machine learning-based navigation
- [ ] Mobile app integration
- [ ] Cloud deployment configurations
- [ ] Advanced visualization with 3D rendering
- [ ] Real-time WebSocket updates
- [ ] Historical data analysis and optimization

## Support

- Documentation: See `docs/` directory
- Issues: GitHub Issues
- Discussions: GitHub Discussions

## Authors

Robot Vacuum Team

---

**Built with ❤️ using Python, Rust, and modern DevOps practices**

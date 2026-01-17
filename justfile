# Justfile for Robot Vacuum Cleaner
# https://github.com/casey/just

# Default recipe (show help)
default:
    @just --list

# Setup development environment
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔧 Setting up development environment..."

    # Check Julia version
    julia --version

    # Setup Julia packages
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.instantiate()'

    # Install git hooks
    if [ -f ./scripts/install-hooks.sh ]; then
        ./scripts/install-hooks.sh
    fi

    # Install pre-commit
    pre-commit install

    # Setup Rust
    cd src/rust && cargo build

    echo "✅ Setup complete!"

# Install dependencies only
install:
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.instantiate()'
    cd src/rust && cargo build

# Run all tests
test:
    @just test-julia
    @just test-rust

# Run Julia tests
test-julia:
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.test()'

# Run Rust tests
test-rust:
    cd src/rust && cargo test --verbose

# Run tests with coverage
coverage:
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.add("Coverage"); using Coverage; coverage = process_folder(); covered_lines, total_lines = get_summary(coverage); println("Coverage: ", covered_lines/total_lines * 100, "%")'
    @echo "📊 Julia coverage complete"

# Format code
fmt:
    @just fmt-julia
    @just fmt-rust

# Format Julia code
fmt-julia:
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.add("JuliaFormatter"); using JuliaFormatter; format("src"); format("../../../tests/julia")'

# Format Rust code
fmt-rust:
    cd src/rust && cargo fmt

# Lint code
lint:
    @just lint-julia
    @just lint-rust

# Lint Julia code
lint-julia:
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.add("Lint"); using Lint; lintpkg("RobotVacuum")' || true
    @echo "✅ Julia lint complete"

# Lint Rust code
lint-rust:
    cd src/rust && cargo clippy -- -D warnings

# Run security checks
security:
    @just security-julia
    @just security-rust
    @just security-secrets
    @just security-containers

# Security: Julia
security-julia:
    @echo "🔒 Running Julia security checks..."
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.audit()' || true

# Security: Rust
security-rust:
    cd src/rust && cargo audit || true

# Security: Secret detection
security-secrets:
    gitleaks detect --source . --verbose || true

# Security: Container scanning
security-containers:
    trivy fs . --severity HIGH,CRITICAL || true

# Run all quality checks
quality: fmt lint security test

# Build Julia package
build-julia:
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.build()'

# Build Rust binary
build-rust:
    cd src/rust && cargo build --release

# Build containers
build-containers:
    podman build -f docker/Containerfile -t robot-vacuum:latest .

# Build everything
build: build-julia build-rust build-containers

# Run Julia simulator
run-julia:
    julia --project=src/julia/RobotVacuum src/julia/main.jl

# Run Rust simulator
run-rust:
    cd src/rust && cargo run --release

# Run GraphQL server (Julia)
run-api:
    julia --project=src/julia/RobotVacuum src/julia/graphql_server.jl

# Start all services with compose
up:
    podman-compose -f docker/compose.yaml up -d

# Start development services
up-dev:
    podman-compose -f docker/compose.yaml --profile dev up -d

# Start with monitoring
up-monitoring:
    podman-compose -f docker/compose.yaml --profile monitoring up -d

# Stop all services
down:
    podman-compose -f docker/compose.yaml down

# View logs
logs:
    podman-compose -f docker/compose.yaml logs -f

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info
    rm -rf htmlcov/ .coverage coverage.xml
    rm -rf .pytest_cache/ .mypy_cache/
    rm -rf src/rust/target/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Deep clean (including venv)
clean-all: clean
    rm -rf venv/

# Run pre-commit hooks manually
pre-commit:
    pre-commit run --all-files

# Validate RSR compliance
validate:
    @just validate-rsr

# RSR Framework validation
validate-rsr:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔍 Validating RSR Framework compliance..."
    echo ""

    # Check required files
    echo "📄 Checking required files..."
    files=(
        "README.md"
        "LICENSE.txt"
        "SECURITY.md"
        "CONTRIBUTING.md"
        "CODE_OF_CONDUCT.md"
        "MAINTAINERS.md"
        "CHANGELOG.md"
        ".well-known/security.txt"
        ".well-known/ai.txt"
        ".well-known/humans.txt"
    )

    missing=0
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            echo "  ✅ $file"
        else
            echo "  ❌ $file (missing)"
            missing=$((missing + 1))
        fi
    done

    echo ""
    echo "📊 RSR Compliance Summary:"
    echo "  Required files: $((${#files[@]} - missing))/${#files[@]}"

    if [ $missing -eq 0 ]; then
        echo "  ✅ All required files present"
    else
        echo "  ⚠️  $missing file(s) missing"
    fi

    # Check test coverage
    echo ""
    echo "🧪 Running tests for coverage check..."
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.test()' || true

    echo ""
    echo "🔒 Security checks..."
    trivy fs . --severity CRITICAL --quiet || echo "  ⚠️  Some vulnerabilities found"

    echo ""
    if [ $missing -eq 0 ]; then
        echo "✅ RSR Framework compliance: PASS"
        exit 0
    else
        echo "⚠️  RSR Framework compliance: INCOMPLETE"
        exit 1
    fi

# Generate documentation
docs:
    cd docs && sphinx-build -b html . _build/html

# Serve documentation
docs-serve:
    cd docs/_build/html && julia -e 'using HTTP; HTTP.serve(HTTP.Files.FileServer("."), "0.0.0.0", 8080)'

# Create new release
release VERSION:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📦 Creating release {{VERSION}}..."

    # Update version in files
    echo "{{VERSION}}" > VERSION

    # Run tests
    just test

    # Build artifacts
    just build

    # Create git tag
    git tag -a "v{{VERSION}}" -m "Release {{VERSION}}"

    echo "✅ Release {{VERSION}} ready!"
    echo "Push with: git push origin v{{VERSION}}"

# Benchmark Rust code
benchmark:
    cd src/rust && cargo bench

# Profile Julia code
profile:
    julia --project=src/julia/RobotVacuum --track-allocation=user src/julia/main.jl
    @echo "📊 Profile data generated"

# Check dependencies for updates
deps-check:
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.status()'
    cd src/rust && cargo outdated || cargo install cargo-outdated && cargo outdated

# Update dependencies
deps-update:
    cd src/julia/RobotVacuum && julia --project=. -e 'using Pkg; Pkg.update()'
    cd src/rust && cargo update

# Docker/Podman helpers
container-build:
    podman build -f docker/Containerfile -t robot-vacuum:latest .

container-run:
    podman run -p 8000:8000 robot-vacuum:latest

container-shell:
    podman run -it robot-vacuum:latest /bin/bash

# Salt states
salt-dev:
    salt-call --local state.apply development

salt-cicd:
    salt-call --local state.apply cicd

salt-monitoring:
    salt-call --local state.apply monitoring

# Generate SBOM
sbom:
    syft dir:. -o cyclonedx-json > sbom.json
    @echo "📋 SBOM generated: sbom.json"

# Sign artifacts (requires GPG)
sign FILE:
    gpg --detach-sign --armor {{FILE}}
    @echo "✍️  Signed: {{FILE}}.asc"

# Verify signatures
verify FILE:
    gpg --verify {{FILE}}.asc {{FILE}}

# Check for TODOs
todos:
    rg "TODO|FIXME|XXX|HACK" --type julia --type rust || echo "No TODOs found!"

# Count lines of code
loc:
    @echo "📊 Lines of Code:"
    @echo "Julia:"
    @find src/julia -name "*.jl" | xargs wc -l | tail -1
    @echo "Rust:"
    @find src/rust/src -name "*.rs" | xargs wc -l | tail -1
    @echo "Total:"
    @find src -name "*.jl" -o -name "*.rs" | xargs wc -l | tail -1

# Show project statistics
stats:
    @just loc
    @echo ""
    @echo "📈 Git Statistics:"
    @git log --oneline | wc -l | xargs echo "Commits:"
    @git ls-files | wc -l | xargs echo "Files:"
    @echo ""
    @echo "🧪 Test Statistics:"
    @find tests/julia -name "test_*.jl" | wc -l | xargs echo "Julia test files:"
    @find src/rust -name "*.rs" -exec grep -l "#\[test\]" {} \; | wc -l | xargs echo "Rust test files:"

# Help - show all available recipes
help:
    @just --list --unsorted

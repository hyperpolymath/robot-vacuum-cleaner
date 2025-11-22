# Salt State: Development Environment Setup
# Configures complete development environment for Robot Vacuum Cleaner project

{% set project_root = pillar.get('project_root', '/opt/robot-vacuum-cleaner') %}
{% set python_version = pillar.get('python_version', '3.11') %}
{% set rust_version = pillar.get('rust_version', 'stable') %}

# Install system dependencies
system_packages:
  pkg.installed:
    - pkgs:
      - git
      - curl
      - wget
      - build-essential
      - pkg-config
      - libssl-dev
      - libffi-dev
      - python{{ python_version }}
      - python{{ python_version }}-dev
      - python3-pip
      - python3-venv
      - postgresql-client
      - redis-tools
      - podman
      - podman-compose
      - vim
      - tmux
      - htop
      - jq
      - ripgrep
      - fd-find

# Install Rust toolchain
rust_install:
  cmd.run:
    - name: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain {{ rust_version }}
    - unless: command -v rustc
    - runas: {{ pillar.get('user', 'developer') }}
    - env:
      - HOME: /home/{{ pillar.get('user', 'developer') }}

rust_components:
  cmd.run:
    - name: rustup component add rustfmt clippy
    - onlyif: command -v rustup
    - runas: {{ pillar.get('user', 'developer') }}
    - require:
      - cmd: rust_install

# Create project directory
project_directory:
  file.directory:
    - name: {{ project_root }}
    - user: {{ pillar.get('user', 'developer') }}
    - group: {{ pillar.get('group', 'developer') }}
    - mode: 755
    - makedirs: True

# Clone or update repository
project_repo:
  git.latest:
    - name: {{ pillar.get('repo_url', 'https://github.com/Hyperpolymath/robot-vacuum-cleaner.git') }}
    - target: {{ project_root }}
    - user: {{ pillar.get('user', 'developer') }}
    - force_reset: False
    - require:
      - file: project_directory

# Create Python virtual environment
python_venv:
  cmd.run:
    - name: python{{ python_version }} -m venv venv
    - cwd: {{ project_root }}
    - unless: test -d {{ project_root }}/venv
    - runas: {{ pillar.get('user', 'developer') }}
    - require:
      - git: project_repo

# Install Python dependencies
python_dependencies:
  cmd.run:
    - name: ./venv/bin/pip install --upgrade pip && ./venv/bin/pip install -r requirements.txt
    - cwd: {{ project_root }}
    - onlyif: test -f {{ project_root }}/requirements.txt
    - runas: {{ pillar.get('user', 'developer') }}
    - require:
      - cmd: python_venv

# Install development dependencies
python_dev_dependencies:
  cmd.run:
    - name: ./venv/bin/pip install pytest pytest-cov pytest-asyncio black isort flake8 mypy pylint bandit
    - cwd: {{ project_root }}
    - runas: {{ pillar.get('user', 'developer') }}
    - require:
      - cmd: python_dependencies

# Build Rust components
rust_build:
  cmd.run:
    - name: cargo build --release
    - cwd: {{ project_root }}/src/rust
    - onlyif: test -f {{ project_root }}/src/rust/Cargo.toml
    - runas: {{ pillar.get('user', 'developer') }}
    - require:
      - cmd: rust_components
      - git: project_repo
    - env:
      - CARGO_HOME: /home/{{ pillar.get('user', 'developer') }}/.cargo

# Install git hooks
git_hooks:
  cmd.run:
    - name: ./scripts/install-hooks.sh
    - cwd: {{ project_root }}
    - onlyif: test -f {{ project_root }}/scripts/install-hooks.sh
    - runas: {{ pillar.get('user', 'developer') }}
    - require:
      - git: project_repo

# Create local configuration
local_config:
  file.managed:
    - name: {{ project_root }}/.env
    - source: {{ project_root }}/.env.example
    - user: {{ pillar.get('user', 'developer') }}
    - group: {{ pillar.get('group', 'developer') }}
    - mode: 600
    - unless: test -f {{ project_root }}/.env
    - require:
      - git: project_repo

# Set up pre-commit framework
pre_commit_install:
  cmd.run:
    - name: ./venv/bin/pip install pre-commit && ./venv/bin/pre-commit install
    - cwd: {{ project_root }}
    - onlyif: test -f {{ project_root }}/.pre-commit-config.yaml
    - runas: {{ pillar.get('user', 'developer') }}
    - require:
      - cmd: python_dev_dependencies

# Create development database
dev_database:
  cmd.run:
    - name: createdb robot_vacuum_dev || true
    - runas: postgres
    - unless: psql -lqt | cut -d \| -f 1 | grep -qw robot_vacuum_dev

# Start development services with Podman Compose
dev_services:
  cmd.run:
    - name: podman-compose -f docker/compose.yaml --profile dev up -d
    - cwd: {{ project_root }}
    - onlyif: test -f {{ project_root }}/docker/compose.yaml
    - runas: {{ pillar.get('user', 'developer') }}
    - require:
      - git: project_repo
      - pkg: system_packages

# Create useful aliases
dev_aliases:
  file.blockreplace:
    - name: /home/{{ pillar.get('user', 'developer') }}/.bashrc
    - marker_start: "# BEGIN ROBOT VACUUM ALIASES"
    - marker_end: "# END ROBOT VACUUM ALIASES"
    - content: |
        alias rv-activate='source {{ project_root }}/venv/bin/activate'
        alias rv-test='cd {{ project_root }} && pytest tests/'
        alias rv-lint='cd {{ project_root }} && black src/ tests/ && isort src/ tests/ && flake8 src/ tests/'
        alias rv-run='cd {{ project_root }} && ./venv/bin/python src/graphql/server.py'
        alias rv-compose='cd {{ project_root }} && podman-compose -f docker/compose.yaml'
        alias rv-logs='cd {{ project_root }} && podman-compose -f docker/compose.yaml logs -f'
        alias rv-shell='cd {{ project_root }} && ./venv/bin/python'
    - append_if_not_found: True
    - backup: '.bak'

# Development completed message
development_complete:
  test.succeed_without_changes:
    - name: development_environment_ready
    - require:
      - pkg: system_packages
      - cmd: python_dependencies
      - cmd: rust_build
      - cmd: git_hooks
      - file: local_config

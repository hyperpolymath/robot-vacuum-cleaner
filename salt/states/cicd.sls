# Salt State: CI/CD Tools Setup
# Installs and configures FOSS CI/CD tools for offline use

{% set project_root = pillar.get('project_root', '/opt/robot-vacuum-cleaner') %}

# Install security scanning tools
security_tools:
  pkg.installed:
    - pkgs:
      - gitleaks
      - trivy

# Install Hadolint for Dockerfile linting
hadolint_install:
  archive.extracted:
    - name: /usr/local/bin/
    - source: https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
    - source_hash: https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64.sha256
    - archive_format: bin
    - enforce_toplevel: False
    - unless: command -v hadolint

hadolint_executable:
  file.managed:
    - name: /usr/local/bin/hadolint
    - mode: 755
    - require:
      - archive: hadolint_install

# Install Grype vulnerability scanner
grype_install:
  cmd.run:
    - name: curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
    - unless: command -v grype

# Install SonarQube Scanner
sonar_scanner_install:
  archive.extracted:
    - name: /opt/
    - source: https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
    - archive_format: zip
    - unless: test -d /opt/sonar-scanner

sonar_scanner_link:
  file.symlink:
    - name: /usr/local/bin/sonar-scanner
    - target: /opt/sonar-scanner-5.0.1.3006-linux/bin/sonar-scanner
    - require:
      - archive: sonar_scanner_install

# Install Act (run GitHub Actions locally)
act_install:
  cmd.run:
    - name: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | bash
    - unless: command -v act

# Install GitLab Runner for local CI/CD
gitlab_runner_repo:
  pkgrepo.managed:
    - humanname: GitLab Runner
    - name: deb https://packages.gitlab.com/runner/gitlab-runner/ubuntu/ focal main
    - key_url: https://packages.gitlab.com/runner/gitlab-runner/gpgkey
    - require_in:
      - pkg: gitlab_runner

gitlab_runner:
  pkg.installed:
    - name: gitlab-runner

# Configure GitLab Runner for local use
gitlab_runner_config:
  file.managed:
    - name: /etc/gitlab-runner/config.toml
    - contents: |
        concurrent = 4
        check_interval = 0

        [session_server]
          session_timeout = 1800

        [[runners]]
          name = "local-runner"
          url = "http://localhost"
          token = "local-development-token"
          executor = "shell"
          shell = "bash"
          [runners.custom_build_dir]
          [runners.cache]
            [runners.cache.s3]
            [runners.cache.gcs]
            [runners.cache.azure]
    - mode: 600
    - require:
      - pkg: gitlab_runner

# Install OWASP Dependency Check
dependency_check_install:
  archive.extracted:
    - name: /opt/
    - source: https://github.com/jeremylong/DependencyCheck/releases/download/v8.4.0/dependency-check-8.4.0-release.zip
    - archive_format: zip
    - unless: test -d /opt/dependency-check

dependency_check_link:
  file.symlink:
    - name: /usr/local/bin/dependency-check
    - target: /opt/dependency-check/bin/dependency-check.sh
    - require:
      - archive: dependency_check_install

# Install Syft (SBOM generator)
syft_install:
  cmd.run:
    - name: curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
    - unless: command -v syft

# Install Cosign (container signing)
cosign_install:
  cmd.run:
    - name: |
        wget "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
        sudo mv cosign-linux-amd64 /usr/local/bin/cosign
        sudo chmod +x /usr/local/bin/cosign
    - unless: command -v cosign

# Set up local registry for container images
local_registry:
  cmd.run:
    - name: podman run -d -p 5000:5000 --name registry cgr.dev/chainguard/registry:latest
    - unless: podman ps -a | grep -q registry

# Create CI/CD workspace
cicd_workspace:
  file.directory:
    - name: {{ project_root }}/.cicd
    - user: {{ pillar.get('user', 'developer') }}
    - group: {{ pillar.get('group', 'developer') }}
    - mode: 755
    - makedirs: True

# Create test reports directory
test_reports:
  file.directory:
    - name: {{ project_root }}/test-reports
    - user: {{ pillar.get('user', 'developer') }}
    - group: {{ pillar.get('group', 'developer') }}
    - mode: 755
    - makedirs: True

# Create coverage reports directory
coverage_reports:
  file.directory:
    - name: {{ project_root }}/coverage
    - user: {{ pillar.get('user', 'developer') }}
    - group: {{ pillar.get('group', 'developer') }}
    - mode: 755
    - makedirs: True

# Install pre-commit hooks framework
pre_commit_tools:
  pip.installed:
    - name: pre-commit
    - bin_env: {{ project_root }}/venv

# Create CI/CD helper scripts
cicd_run_tests:
  file.managed:
    - name: {{ project_root }}/scripts/run-tests.sh
    - contents: |
        #!/bin/bash
        set -e
        cd {{ project_root }}
        source venv/bin/activate
        echo "Running Python tests..."
        pytest tests/python/ -v --cov=src/python --cov-report=html --cov-report=term
        echo "Running Rust tests..."
        cd src/rust && cargo test && cd ../..
        echo "Tests complete!"
    - mode: 755
    - user: {{ pillar.get('user', 'developer') }}
    - require:
      - file: cicd_workspace

cicd_run_security_scan:
  file.managed:
    - name: {{ project_root }}/scripts/security-scan.sh
    - contents: |
        #!/bin/bash
        set -e
        cd {{ project_root }}
        echo "Running security scans..."
        echo "1. GitLeaks..."
        gitleaks detect --source . --verbose
        echo "2. Trivy filesystem..."
        trivy filesystem --severity HIGH,CRITICAL .
        echo "3. Bandit..."
        source venv/bin/activate
        bandit -r src/python/
        echo "4. Dependency Check..."
        dependency-check --scan . --format HTML --out ./test-reports
        echo "Security scans complete!"
    - mode: 755
    - user: {{ pillar.get('user', 'developer') }}
    - require:
      - file: cicd_workspace

cicd_build_containers:
  file.managed:
    - name: {{ project_root }}/scripts/build-containers.sh
    - contents: |
        #!/bin/bash
        set -e
        cd {{ project_root }}
        echo "Building containers..."
        podman build -f docker/Containerfile -t robot-vacuum:latest .
        echo "Scanning container..."
        trivy image robot-vacuum:latest
        echo "Generating SBOM..."
        syft robot-vacuum:latest -o cyclonedx-json > sbom.json
        echo "Container build complete!"
    - mode: 755
    - user: {{ pillar.get('user', 'developer') }}
    - require:
      - file: cicd_workspace

# CI/CD setup complete
cicd_complete:
  test.succeed_without_changes:
    - name: cicd_tools_ready
    - require:
      - cmd: grype_install
      - cmd: syft_install
      - file: cicd_run_tests
      - file: cicd_run_security_scan
      - file: cicd_build_containers

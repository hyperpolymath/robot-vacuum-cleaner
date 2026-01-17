# Contributing to Robot Vacuum Cleaner

Thank you for your interest in contributing! This project follows the **Tri-Perimeter Contribution Framework (TPCF)** to ensure emotional safety and graduated trust.

## 🛡️ Tri-Perimeter Contribution Framework (TPCF)

### Perimeter 3: Community Sandbox (Current Status)

**Access Level**: Open Contribution
**Trust Level**: Minimal verification required
**Scope**: This project operates in Perimeter 3, welcoming all contributions

**What This Means**:
- Anyone can fork, clone, and submit pull requests
- All contributions are reviewed before merge
- Maintainers verify code quality and security
- Contributors build trust through consistent, quality contributions

**Future Perimeters**:
- **Perimeter 2: Trusted Collaborators** - Proven contributors with direct commit access
- **Perimeter 1: Core Maintainers** - Long-term maintainers with full repository access

## 🌟 Ways to Contribute

### 1. Code Contributions

- **Bug Fixes**: Fix issues from the issue tracker
- **New Features**: Implement planned features from roadmap
- **Performance Improvements**: Optimize algorithms or reduce resource usage
- **Test Coverage**: Add tests to improve coverage
- **Documentation**: Improve inline docs, README, or guides

### 2. Non-Code Contributions

- **Bug Reports**: File detailed bug reports with reproduction steps
- **Feature Requests**: Propose new features with use cases
- **Documentation**: Write tutorials, guides, or improve existing docs
- **Design**: Create UI/UX improvements or visualizations
- **Translation**: Translate documentation (future)
- **Community Support**: Help others in discussions and issues

### 3. Infrastructure

- **CI/CD**: Improve build pipelines or add new checks
- **Tooling**: Enhance development tools or scripts
- **Security**: Identify and report security vulnerabilities
- **Performance**: Profile and optimize critical paths

## 🚀 Getting Started

### Prerequisites

```bash
# Required
- Python 3.11+
- Rust (latest stable)
- Git
- Podman or Docker

# Recommended
- Just (command runner)
- Pre-commit
- VS Code with extensions (Python, Rust)
```

### Initial Setup

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/robot-vacuum-cleaner.git
cd robot-vacuum-cleaner

# 3. Add upstream remote
git remote add upstream https://github.com/Hyperpolymath/robot-vacuum-cleaner.git

# 4. Set up Python environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Set up Rust
cd src/rust
cargo build
cargo test
cd ../..

# 6. Install git hooks
./scripts/install-hooks.sh

# 7. Install pre-commit
pre-commit install
```

### Development Workflow

```bash
# 1. Create a feature branch
git checkout -b feature/your-feature-name

# 2. Make your changes
# - Write code
# - Add tests
# - Update documentation

# 3. Run tests locally
pytest tests/python/ -v
cd src/rust && cargo test && cd ../..

# 4. Run code quality checks
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/

# 5. Run security scans
bandit -r src/python/
trivy fs .

# 6. Commit your changes (pre-commit hooks will run)
git add .
git commit -m "feat(component): add your feature"

# 7. Push to your fork
git push origin feature/your-feature-name

# 8. Open a Pull Request
```

## 📋 Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated (README, inline comments)
- [ ] Commit messages follow Conventional Commits format
- [ ] No merge conflicts with main branch
- [ ] Pre-commit hooks pass
- [ ] Security scans pass

### PR Description Template

```markdown
## Description
[Brief description of changes]

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review performed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Security considerations addressed

## Related Issues
Fixes #[issue number]
Relates to #[issue number]

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Additional Notes
[Any additional information]
```

### Review Process

1. **Automated Checks**: CI/CD runs tests, linting, security scans
2. **Code Review**: Maintainers review code quality, design, tests
3. **Feedback**: Address review comments
4. **Approval**: At least one maintainer approval required
5. **Merge**: Maintainer merges after all checks pass

## 🎯 Coding Standards

### Python Style

- **Formatter**: Black (line length 120)
- **Import Sorting**: isort (compatible with Black)
- **Linter**: Flake8, Pylint
- **Type Hints**: Required for public APIs
- **Docstrings**: Google style for all public functions
- **Testing**: pytest with 70%+ coverage

```python
# Good example
def calculate_distance(start: Position, end: Position) -> float:
    """
    Calculate Euclidean distance between two positions.

    Args:
        start: Starting position
        end: Ending position

    Returns:
        Distance in meters

    Raises:
        ValueError: If positions are invalid
    """
    return start.distance_to(end)
```

### Rust Style

- **Formatter**: rustfmt (default settings)
- **Linter**: clippy (all warnings enabled)
- **Documentation**: Doc comments for all public items
- **Testing**: Unit tests for all modules
- **Safety**: No unsafe code without extensive justification

```rust
/// Calculate distance between two positions.
///
/// # Arguments
///
/// * `start` - Starting position
/// * `end` - Ending position
///
/// # Returns
///
/// Distance in meters
///
/// # Examples
///
/// ```
/// let distance = calculate_distance(&start, &end);
/// assert!(distance > 0.0);
/// ```
pub fn calculate_distance(start: &Position, end: &Position) -> f64 {
    start.distance_to(end)
}
```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `build`: Build system changes

**Examples**:
```
feat(pathfinding): add A* algorithm with diagonal movement
fix(robot): correct battery consumption calculation
docs(readme): update installation instructions
test(slam): add particle filter unit tests
```

## 🧪 Testing Guidelines

### Writing Tests

- **Test Coverage**: Aim for 80%+ coverage for new code
- **Test Types**: Unit, integration, and end-to-end tests
- **Test Data**: Use fixtures for reusable test data
- **Assertions**: Clear, specific assertions
- **Edge Cases**: Test boundary conditions and error cases

### Running Tests

```bash
# Python tests
pytest tests/python/ -v --cov=src/python

# Rust tests
cd src/rust && cargo test --verbose

# Integration tests
pytest tests/integration/ -v

# Specific test file
pytest tests/python/test_robot.py -v

# With coverage report
pytest --cov=src/python --cov-report=html
open htmlcov/index.html
```

## 🔒 Security

### Reporting Vulnerabilities

See [SECURITY.md](SECURITY.md) for security disclosure policy.

### Security Best Practices

- Never commit secrets (use environment variables)
- Validate all external inputs
- Use parameterized queries (avoid SQL injection)
- Sanitize output (prevent XSS)
- Keep dependencies updated
- Run security scans before committing

## 📖 Documentation

### Code Documentation

- **Python**: Google-style docstrings
- **Rust**: Doc comments (///)
- **Inline Comments**: Explain "why", not "what"
- **Examples**: Include usage examples in docstrings

### Project Documentation

- **README.md**: Overview, installation, quick start
- **ARCHITECTURE.md**: System design and architecture
- **API Documentation**: Generated from code
- **Guides**: Step-by-step tutorials

## 🌈 Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

### Key Principles

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Inclusive**: Welcome contributors from all backgrounds
- **Be Collaborative**: Work together constructively
- **Be Patient**: Remember everyone is learning
- **Assume Good Intent**: Give others the benefit of the doubt

## 🏆 Recognition

### Contributors

All contributors are recognized in:
- [CONTRIBUTORS.md](CONTRIBUTORS.md) (alphabetical list)
- `.well-known/humans.txt` (machine-readable format)
- GitHub contributors graph
- Release notes for significant contributions

### Becoming a Maintainer

Path to maintainership (TPCF Perimeter 2):

1. **Consistent Contributions**: Regular, quality contributions over 3-6 months
2. **Code Reviews**: Participate in reviewing others' PRs
3. **Community Support**: Help others in issues and discussions
4. **Trust Building**: Demonstrate commitment and understanding
5. **Invitation**: Current maintainers extend invitation

## 💬 Communication

### Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Pull Requests**: Code contributions and reviews
- **Email**: security@robot-vacuum.example.com (security only)

### Response Times

- **Issues**: Within 48-72 hours
- **Pull Requests**: Initial review within 1 week
- **Security Reports**: Within 48 hours
- **General Questions**: Best effort, no SLA

## 📚 Resources

### Learning Resources

- [Python Documentation](https://docs.python.org/3/)
- [Rust Book](https://doc.rust-lang.org/book/)
- [GraphQL Learn](https://graphql.org/learn/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Cargo Book](https://doc.rust-lang.org/cargo/)

### Project-Specific

- [Architecture Documentation](docs/architecture/)
- [API Reference](docs/api/)
- [Development Setup Guide](docs/development-setup.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

## ❓ Questions?

- **Technical Questions**: Open a GitHub Discussion
- **Bug Reports**: File a GitHub Issue
- **Security Concerns**: Email security@robot-vacuum.example.com
- **General Inquiries**: Open a GitHub Discussion

## 📄 License

By contributing, you agree that your contributions will be licensed under the dual MIT + Palimpsest v0.8 license. See [LICENSE.txt](LICENSE.txt) for details.

### Emotional Safety Rights

Under the Palimpsest License, you retain:
- Right to be credited in all derivative works
- Right to withdraw contributions (with notice)
- Protection from malicious modification
- Reversibility guarantees through version control

---

**Thank you for contributing to Robot Vacuum Cleaner!** 🤖🧹

Your contributions make this project better for everyone. We appreciate your time and effort!

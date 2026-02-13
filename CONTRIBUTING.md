# Contributing to SerialScope

Thank you for your interest in contributing to SerialScope! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/serialscope.git
   cd serialscope
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Install Development Tools**
   ```bash
   pip install black ruff mypy pytest pytest-cov
   ```

## 📝 Development Workflow

### Code Style

We use:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **mypy** for type checking (optional, not strict)

**Before committing:**
```bash
make format  # Formats code with Black and fixes Ruff issues
make lint    # Checks code quality
```

### Testing

Write tests for new features:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=serialscope --cov-report=html

# Run specific test file
pytest tests/unit/test_event.py
```

**Test Guidelines:**
- Unit tests should be fast and isolated
- Use mocks for external dependencies (serial ports)
- Aim for >80% code coverage

### Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Example:
```
feat: Add IMU plugin support

- Implement IMU data parser
- Add visualization panel
- Update documentation
```

## 🏗 Architecture Guidelines

### Adding a New Feature

1. **Core Layer** (`serialscope/core/`)
   - Add core functionality
   - Keep it modular and testable
   - Document public APIs

2. **UI Layer** (`serialscope/ui/`)
   - Use Textual for terminal UI
   - Follow existing patterns
   - Keep components reusable

3. **Plugins** (`serialscope/plugins/`)
   - Extend `Plugin` base class
   - Register with `PluginRegistry`
   - Document plugin interface

### Code Organization

- **One class per file** (unless closely related)
- **Clear module boundaries**
- **Type hints** for function signatures
- **Docstrings** for public APIs

### Error Handling

- Use appropriate exception types
- Log errors with context
- Provide user-friendly error messages
- Handle edge cases gracefully

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Minimal steps to reproduce
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:
   - OS and version
   - Python version
   - SerialScope version
   - Hardware (if relevant)

## 💡 Feature Requests

For feature requests:

1. Check if it's already requested
2. Describe the use case
3. Explain the benefit
4. Suggest implementation approach (if possible)

## 🔍 Code Review Process

1. **Create Pull Request**
   - Target `main` branch
   - Fill out PR template
   - Link related issues

2. **Review Checklist**
   - [ ] Code follows style guidelines
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)

3. **Address Feedback**
   - Respond to comments
   - Make requested changes
   - Update PR description if needed

## 📚 Documentation

When adding features:

- Update `README.md` if user-facing
- Add docstrings to new functions/classes
- Update `ARCHITECTURE.md` for architectural changes
- Add examples in `examples/` directory

## 🧪 Testing Guidelines

### Unit Tests

- Test individual components
- Mock external dependencies
- Test edge cases and error conditions

### Integration Tests

- Test component interactions
- Use simulated serial data
- Test end-to-end workflows

### Test Structure

```
tests/
├── unit/           # Unit tests
│   └── test_*.py
└── integration/    # Integration tests
    └── test_*.py
```

## 🚢 Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag
4. Build and publish package

## 📞 Getting Help

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions
- **Email**: Contact maintainers

## 🙏 Thank You!

Your contributions make SerialScope better for everyone. Thank you for taking the time to contribute!

# Contributing to RCD²

Thank you for your interest in contributing to the RCD² (Real-Time Concept Drift Detector & Auto-Retraining ML Pipeline) project! This document provides guidelines for contributions.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## 📜 Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/Raoof128/RTCDDARMP.git
cd RCD2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests to verify setup
pytest tests/ -v
```

## 🔄 Development Process

### Branching Strategy

We use a simplified Git Flow:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical production fixes

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Write Tests First** (TDD approach recommended)
2. **Implement Feature** with clean, documented code
3. **Run Tests** to ensure nothing breaks
4. **Update Documentation** if needed
5. **Commit Changes** with clear, descriptive messages

### Commit Message Format

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring without changing behavior
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(drift-detector): add Jensen-Shannon divergence metric

Implement JS divergence as an additional drift detection method
to provide symmetric KL divergence measurement.

Closes #123
```

```
fix(retrain-engine): resolve model promotion race condition

Add mutex lock to prevent concurrent model promotions that could
cause registry corruption.

Fixes #456
```

## 🔀 Pull Request Process

### Before Submitting

1. **Ensure all tests pass**:
   ```bash
   pytest tests/ -v --cov=backend
   ```

2. **Run linting**:
   ```bash
   black backend/ tests/
   flake8 backend/ tests/
   mypy backend/
   ```

3. **Update documentation** if you've changed APIs or added features

4. **Add tests** for new functionality (aim for >80% coverage)

### Submitting the PR

1. **Push your branch** to your fork
2. **Create a Pull Request** against the `develop` branch
3. **Fill out the PR template** completely
4. **Link related issues** using keywords (Fixes #123, Closes #456)
5. **Request review** from maintainers

### PR Review Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New code has adequate test coverage (>80%)
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages are clear and follow conventions
- [ ] PR description clearly explains changes

## 💻 Coding Standards

### Python Style Guide

We follow **PEP 8** with some specific conventions:

#### General

- Use **4 spaces** for indentation (no tabs)
- Maximum line length: **88 characters** (Black default)
- Use **type hints** for all function parameters and return values
- Write **docstrings** for all public modules, classes, and functions

#### Type Hints

```python
from typing import List, Optional, Dict, Any

def detect_drift(
    features: np.ndarray,
    labels: Optional[np.ndarray] = None,
    threshold: float = 0.2
) -> Dict[str, Any]:
    """
    Detect drift in data stream.
    
    Parameters:
    -----------
    features : np.ndarray
        Feature matrix (n_samples, n_features)
    labels : np.ndarray, optional
        Target labels
    threshold : float
        Drift detection threshold
        
    Returns:
    --------
    Dict[str, Any]
        Drift detection results
    """
    pass
```

#### Docstring Format

Use **NumPy-style** docstrings:

```python
def function_name(param1: int, param2: str) -> bool:
    """
    Brief description of function.
    
    Longer description if needed. Can span multiple
    lines and include implementation details.
    
    Parameters:
    -----------
    param1 : int
        Description of param1
    param2 : str
        Description of param2
        
    Returns:
    --------
    bool
        Description of return value
        
    Raises:
    -------
    ValueError
        When param1 is negative
        
    Examples:
    ---------
    >>> function_name(5, "test")
    True
    """
    pass
```

#### Naming Conventions

- **Classes**: `PascalCase` (e.g., `DriftDetector`)
- **Functions/Methods**: `snake_case` (e.g., `detect_drift`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_WINDOW_SIZE`)
- **Private members**: Prefix with `_` (e.g., `_internal_method`)

#### Error Handling

Always include proper error handling:

```python
def safe_operation(data: List[float]) -> float:
    """Safe operation with error handling."""
    try:
        if not data:
            raise ValueError("Data cannot be empty")
        
        result = sum(data) / len(data)
        return result
        
    except (TypeError, ZeroDivisionError) as e:
        logger.error(f"Operation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise
```

#### Logging

Use structured logging:

```python
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def process_data(data: Any) -> None:
    """Process data with logging."""
    logger.info(f"Processing data with {len(data)} samples")
    
    try:
        # ... processing logic ...
        logger.debug("Processing successful")
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise
```

### Code Organization

- **One class per file** (unless closely related)
- **Group imports**: stdlib, third-party, local
- **Keep functions focused**: Single Responsibility Principle
- **Avoid deep nesting**: Extract to helper functions

## 🧪 Testing Guidelines

### Test Structure

```python
import pytest
import numpy as np
from backend.engines.drift_detector import DriftDetector


class TestDriftDetector:
    """Test suite for DriftDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance for tests."""
        return DriftDetector(n_features=3)
    
    def test_initialization(self, detector):
        """Test detector initialization."""
        assert detector.n_features == 3
        assert detector.reference_features is None
    
    def test_detect_drift_with_valid_data(self, detector):
        """Test drift detection with valid data."""
        # Arrange
        X_ref = np.random.randn(100, 3)
        detector.set_reference(X_ref)
        
        # Act
        for _ in range(50):
            detector.add_sample(np.random.randn(3))
        result = detector.detect_drift()
        
        # Assert
        assert "drift_score" in result
        assert 0 <= result["drift_score"] <= 100
```

### Test Coverage

- **Unit Tests**: Test individual functions/methods
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test full workflows

Aim for **>80% code coverage**:

```bash
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

### Test Naming

- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<what>_<condition>_<expected>`

## 📚 Documentation

### What to Document

1. **All public APIs**: Complete docstrings
2. **Architecture decisions**: In `docs/` or `ARCHITECTURE.md`
3. **Setup instructions**: In `README.md`
4. **Examples**: In `examples/` directory
5. **Configuration**: In code and README

### Documentation Standards

- Use **Markdown** for all documentation files
- Include **code examples** where applicable
- Keep documentation **up-to-date** with code
- Use **diagrams** for complex concepts (Mermaid/ASCII)

## 🌐 Community

### Getting Help

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Pull Requests**: Code reviews, feedback

### Reporting Bugs

Use the GitHub issue tracker with:

1. **Clear title**: Describe the bug concisely
2. **Environment**: Python version, OS, dependencies
3. **Steps to reproduce**: Minimal reproducible example
4. **Expected behavior**: What should happen
5. **Actual behavior**: What actually happens
6. **Logs/Screenshots**: If applicable

### Suggesting Features

1. **Check existing issues** to avoid duplicates
2. **Describe the problem** the feature would solve
3. **Propose a solution** if you have one
4. **Discuss alternatives** you've considered

## 🎯 Areas for Contribution

We especially welcome contributions in:

- **New drift detection algorithms** (e.g., EDDM, HDDM, STEPD)
- **Additional statistical tests** (e.g., Chi-square, Anderson-Darling)
- **Model types** (neural networks, gradient boosting)
- **Visualization improvements** (better charts, real-time updates)
- **Performance optimizations** (streaming, parallel processing)
- **Documentation** (tutorials, examples, guides)
- **Test coverage** (edge cases, integration tests)

## 📦 Release Process

Maintainers will handle releases, but contributors should:

1. Update **CHANGELOG.md** with changes
2. Ensure **version numbers** follow SemVer
3. Update **documentation** for breaking changes

## 🙏 Recognition

All contributors will be:

- Listed in **CONTRIBUTORS.md**
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to RCD²! 🚀

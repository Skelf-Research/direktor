# Contributing

Thank you for your interest in contributing to Direktor!

## Getting Started

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/Skelf-Research/direktor.git
cd direktor
```

2. Install dependencies with uv:
```bash
uv sync --all-extras
```

3. Set up pre-commit hooks (optional):
```bash
uv run pre-commit install
```

4. Create your `.env` file:
```bash
cp sample.env .env
# Edit .env with your API keys
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=direktor

# Run specific test file
uv run pytest tests/test_utils.py
```

### Code Formatting

```bash
# Format code with Black
uv run black direktor/ tests/

# Check formatting
uv run black --check direktor/ tests/
```

### Linting

```bash
# Run flake8
uv run flake8 direktor/ tests/
```

### Building Documentation

```bash
cd documentation
uv run mkdocs serve
# Visit http://localhost:8000
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use Black for formatting (line length: 88)
- Use type hints where practical
- Write docstrings for all public functions

### Docstring Format

```python
def function_name(param1: str, param2: int = 10) -> str:
    """
    Short description of function.

    Longer description if needed, explaining the function's
    behavior in more detail.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
    """
    pass
```

## Submitting Changes

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests and linting
5. Commit with a descriptive message
6. Push to your fork
7. Open a Pull Request

### Commit Messages

Use clear, descriptive commit messages:

```
Add support for custom TTS models

- Add TTS_MODEL environment variable
- Update audio.py to use configurable model
- Add documentation for custom models
```

### PR Description

Include in your PR description:

- What the change does
- Why it's needed
- How to test it
- Any breaking changes

## Project Structure

```
direktor/
├── direktor/           # Main package
│   ├── __init__.py    # Package exports
│   ├── cli.py         # CLI interface
│   ├── assets/        # Static assets
│   └── core/          # Core modules
├── tests/             # Test suite
├── documentation/     # MkDocs documentation
├── examples/          # Example files
└── pyproject.toml     # Project configuration
```

## Adding New Features

### New Module Checklist

- [ ] Create module in `direktor/core/`
- [ ] Add exports to `direktor/core/__init__.py`
- [ ] Write unit tests in `tests/`
- [ ] Add documentation in `documentation/docs/api/`
- [ ] Update relevant guides

### New Configuration Option

- [ ] Add to `config.py`
- [ ] Document in `configuration.md`
- [ ] Add to `sample.env`
- [ ] Update validation if required

## Reporting Issues

### Bug Reports

Include:

- Direktor version
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests

Include:

- Use case description
- Proposed solution
- Alternative approaches considered

## Questions?

- Open a GitHub issue
- Check existing issues first
- Use the discussions tab for general questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

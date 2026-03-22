# Contributing to PCSL

Thank you for your interest in contributing to PCSL (Personal Context Sovereignty Layer)! This document outlines the process for contributing to the project.

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [issue tracker](https://github.com/karan/pcsl/issues) to see if the issue has already been reported. When creating a bug report, include:

- A quick summary and background
- Steps to reproduce
- What you expected vs what actually happened
- Notes (possibly including why you think this might be happening)

### Suggesting Features

Feature requests are welcome! But please first check if there's already a proposal for the feature you'd like to see. When suggesting a feature:

- Explain the problem you're trying to solve
- Describe your proposed solution
- Consider alternatives you've considered

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Write a clear commit message
7. Push your changes to your fork
8. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/CodeForgeNet/pcsl.git
cd pcsl

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env and fill in your API keys (see .env.example for instructions)

# Run tests
pytest

# Run the server
uvicorn pcsl.pcsl_server.main:app --reload
```

## Coding Standards

- Use **Black** for code formatting: `black pcsl/ tests/`
- Use **Ruff** for linting: `ruff check pcsl/ tests/`
- Write type hints where possible
- Include docstrings for public functions
- Keep lines under 100 characters

## Commit Message Guidelines

- Use imperative mood ("Add feature" not "Added feature")
- First line should be under 72 characters
- Reference issues and pull requests where relevant

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Update the CHANGELOG.md if applicable
4. The maintainers will review and merge your PR

## Recognition

Contributors will be listed in the README.md file (with permission).

Podcast Analysis Project

## Setup

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to run linting and formatting checks before each commit.

#### Installation

1. Install dependencies (including pre-commit):
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Install the git hooks:
   ```bash
   pre-commit install
   ```

#### Usage

Pre-commit hooks will automatically run on `git commit`. They check:
- **ruff check**: Lints Python files and auto-fixes issues
- **ruff format**: Auto-formats Python code

To run hooks manually on all files:
```bash
pre-commit run --all-files
```

To run hooks on staged files only:
```bash
pre-commit run
```

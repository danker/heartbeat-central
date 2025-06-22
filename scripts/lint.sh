#!/bin/bash
# Run code quality checks: isort, black, and flake8

set -e  # Exit on first error

echo "Running isort..."
uv run python -m isort .

echo -e "\nRunning Black formatter..."
uv run python -m black .

echo -e "\nRunning Flake8 linter..."
uv run python -m flake8 .

echo -e "\n✅ All linting checks passed!"
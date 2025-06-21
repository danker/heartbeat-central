#!/bin/bash
# Run code quality checks: isort, black, and flake8

set -e  # Exit on first error

echo "Running isort..."
uv run isort .

echo -e "\nRunning Black formatter..."
uv run black .

echo -e "\nRunning Flake8 linter..."
uv run flake8 .

echo -e "\n✅ All linting checks passed!"
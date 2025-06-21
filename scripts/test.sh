#!/bin/bash
# Run all tests for the healthcheck-monitor project

set -e  # Exit on first error

echo "🧪 Running tests..."
uv run pytest -v

echo -e "\n✅ All tests passed!"
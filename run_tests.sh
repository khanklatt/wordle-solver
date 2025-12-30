#!/bin/bash
# Test runner script for Wordle Solver
# Runs both CLI and API tests

set -e

echo "Running Wordle Solver tests..."
echo ""

# Check if Flask is installed (required for API tests)
if python3 -c "import flask" 2>/dev/null; then
    echo "=== Running API Tests ==="
    python3 -m unittest api.test_api -v
    echo ""
else
    echo "Warning: Flask not installed, skipping API tests"
    echo "Install with: pip install -r api/requirements.txt"
    echo ""
fi

echo "=== Running CLI Solver Tests ==="
python3 -m unittest test_wordle_solver -v

echo ""
echo "All tests completed!"


#!/bin/bash

set -euo pipefail

VENV_DIR=".venv"
PYTHON_EXEC="$VENV_DIR/bin/python"

if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed. Please install 'uv' before running this script."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating virtual environment..."
    uv sync
fi

if [ ! -x "$PYTHON_EXEC" ]; then
    echo "Error: Python executable not found in virtual environment."
    exit 1
fi

# Run the main Python program (echo with green color)
echo -e "\033[0;32mFetch API data from TripAdvisor in 3 seconds...\033[0m"
sleep 3
$PYTHON_EXEC tripadvisor/main.py --api
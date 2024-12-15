#!/bin/bash

set -euo pipefail

VENV_DIR=".venv"
PYTHON_EXEC="$VENV_DIR/bin/python"
MAX_LOCATIONS=200

usage() {
    echo "Usage: $0 [-n N]"
    echo "  -n N    Set the maximum locations (default: 200)."
    exit 1
}

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -n)
            if [[ -z "${2:-}" || ! "$2" =~ ^[0-9]+$ ]]; then
                echo "Error: -n requires a numeric argument."
                usage
            fi
            MAX_LOCATIONS=$2
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Error: Unknown argument: $1"
            usage
            ;;
    esac
done

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
echo -e "\033[0;32mScraping up to $MAX_LOCATIONS locations from TripAdvisor in 3 seconds...\033[0m"
sleep 3
$PYTHON_EXEC tripadvisor/main.py --scrape --max_locations "$MAX_LOCATIONS"

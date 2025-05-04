#!/bin/bash

# Default values
CLIENTS=5
STARTING_OPS=100
SCALING_FACTOR=2
STEPS=5

# Parse command line arguments
while getopts ":c:o:f:s:h" opt; do
  case ${opt} in
    c )
      CLIENTS=$OPTARG
      ;;
    o )
      STARTING_OPS=$OPTARG
      ;;
    f )
      SCALING_FACTOR=$OPTARG
      ;;
    s )
      STEPS=$OPTARG
      ;;
    h )
      echo "Usage: $0 [-c clients] [-o starting_ops] [-f scaling_factor] [-s steps]"
      echo "  -c: Number of client connections (default: 5)"
      echo "  -o: Starting number of operations (default: 100)"
      echo "  -f: Scaling factor for each step (default: 2)"
      echo "  -s: Number of scaling steps (default: 5)"
      exit 0
      ;;
    \? )
      echo "Invalid option: $OPTARG" 1>&2
      exit 1
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument" 1>&2
      exit 1
      ;;
  esac
done

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Print the command being executed
echo "Running load test with:"
echo "  Clients: $CLIENTS"
echo "  Starting operations: $STARTING_OPS"
echo "  Scaling factor: $SCALING_FACTOR"
echo "  Steps: $STEPS"

# Run the test
python "$PROJECT_ROOT/tests/load_test.py" \
  --clients $CLIENTS \
  --starting-ops $STARTING_OPS \
  --scaling-factor $SCALING_FACTOR \
  --steps $STEPS

# Check if the test completed successfully
if [ $? -eq 0 ]; then
    echo "Load test completed successfully. Check the logs directory for results."
else
    echo "Load test failed. Check the logs for errors."
    exit 1
fi 
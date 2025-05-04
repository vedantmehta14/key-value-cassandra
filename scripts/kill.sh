#!/bin/bash

# Set base directory to the project root
cd "$(dirname "$0")/.."

echo "Stopping all key-value store servers..."

# METHOD 1: Try to find and kill all server processes by name pattern
echo "Trying to kill servers by process name..."
pkill -f "python3.*src/grpc_server.py" 2>/dev/null

# Check if any processes were killed
if [ $? -eq 0 ]; then
    echo "Servers have been stopped by process name."
else
    echo "No running servers were found by process name."
fi

# METHOD 2: Kill processes by specific ports
echo "Trying to kill servers by port numbers..."

# Use server ports from config file if possible
if [ -f "config/config.json" ]; then
    # Extract the ports from config.json using Python
    PORTS=$(python3 -c "
import json
with open('config/config.json') as f:
    data = json.load(f)
    ports = [str(server['port']) for server in data['servers']]
    print(' '.join(ports))
")
else
    # Use default port range if config file not found
    PORTS="50050 50051 50052 50053 50054 50055 50056 50057 50058 50059"
fi

# Track if we killed any processes by port
KILLED_COUNT=0

# Find and kill processes on each port
for PORT in $PORTS; do
    echo "Checking port $PORT..."
    
    # Get PID for process using this port (works on Linux and macOS)
    if command -v lsof >/dev/null 2>&1; then
        PID=$(lsof -t -i:$PORT 2>/dev/null)
    elif command -v netstat >/dev/null 2>&1; then
        # For Linux systems without lsof
        PID=$(netstat -tulpn 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d/ -f1)
    fi
    
    # Kill the process if found
    if [ -n "$PID" ]; then
        echo "Found process $PID on port $PORT, killing it..."
        kill -9 $PID 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "Successfully killed process $PID on port $PORT"
            KILLED_COUNT=$((KILLED_COUNT+1))
        else
            echo "Failed to kill process $PID on port $PORT"
        fi
    else
        echo "No process found on port $PORT"
    fi
done

if [ $KILLED_COUNT -gt 0 ]; then
    echo "Killed $KILLED_COUNT processes by port."
else
    echo "No processes were killed by port."
fi

echo "Cleanup complete." 
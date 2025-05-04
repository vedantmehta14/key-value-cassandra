#!/bin/bash

# Exit on error
set -e

# Generate Python code from proto file if it doesn't exist yet
if [ ! -f "keyvalue_pb2.py" ]; then
    echo "Generating gRPC code from proto file..."
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. keyvalue.proto
fi

# Function to check if a port is already in use
port_in_use() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        lsof -i:$port >/dev/null 2>&1
        return $?
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tuln | grep -q ":$port "
        return $?
    else
        # Default to assuming port is free if we can't check
        return 1
    fi
}

# Parse server information from config.json
servers=$(python -c "
import json
with open('config.json', 'r') as f:
    config = json.load(f)
for server in config['servers']:
    print(f\"{server['id']} {server['ip']} {server['port']}\")
")

# Kill existing Python processes (if any)
echo "Stopping any existing servers..."
pkill -f "python.*grpc_server.py" || true
sleep 1

# Start each server
echo "Starting servers..."

for server in $servers; do
    read -r id ip port <<< "$server"
    
    # Check if port is already in use
    if port_in_use $port; then
        echo "Port $port is already in use. Cannot start server $id."
        continue
    fi
    
    # Start the server in the background
    echo "Starting server $id on $ip:$port"
    python grpc_server.py --id $id --ip $ip --port $port > "server_$id.log" 2>&1 &
    
    # Sleep briefly to prevent port conflicts
    sleep 0.5
done

echo "All servers started. Use 'tail -f server_*.log' to view logs."
echo "Press Ctrl+C to stop all servers."

# Wait for Ctrl+C
trap "echo 'Stopping all servers...'; pkill -f 'python.*grpc_server.py' || true; exit 0" INT
while true; do
    sleep 1
done 
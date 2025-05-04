#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Generate Python gRPC code from the proto file if it doesn't exist
if [ ! -f "keyvalue_pb2.py" ]; then
    echo "Generating gRPC code from proto file..."
    python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. keyvalue.proto
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
        # Assume port is free if we can't check
        return 1
    fi
}

# Read server information from config.json using Python
servers=$(python3 -c "
import json
with open('config.json') as f:
    data = json.load(f)
    for server in data['servers']:
        print(f\"{server['id']} {server['ip']} {server['port']}\")
")

# Stop any running grpc_server.py processes
echo "Stopping any existing servers..."
pkill -f "python3.*grpc_server.py" || true
sleep 1

# Start each server in the background
echo "Starting servers..."

while read -r id ip port; do
    if port_in_use "$port"; then
        echo "Port $port is already in use. Cannot start server $id."
        continue
    fi

    echo "Starting server $id on $ip:$port"
    python3 grpc_server.py --id "$id" --ip "$ip" --port "$port" > "server_$id.log" 2>&1 &

    sleep 0.5
done <<< "$servers"

echo "All servers started. Use 'tail -f server_*.log' to view logs."
echo "Press Ctrl+C to stop all servers."

# Gracefully handle Ctrl+C
trap "echo 'Stopping all servers...'; pkill -f 'python3.*grpc_server.py' || true; exit 0" INT

# Keep the script running until manually interrupted
while true; do
    sleep 1
done

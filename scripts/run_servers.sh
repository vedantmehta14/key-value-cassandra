# AI generated

#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Set base directory to the project root
cd "$(dirname "$0")/.."

# Generate Python gRPC code from the proto file if it doesn't exist
if [ ! -f "src/proto/keyvalue_pb2.py" ]; then
    echo "Generating gRPC code from proto file..."
    python3 -m grpc_tools.protoc -I./src/proto --python_out=./src/proto --grpc_python_out=./src/proto ./src/proto/keyvalue.proto
    # Move the generated files to the right place
    mv src/proto/src/proto/keyvalue_pb2*.py src/proto/ 2>/dev/null || true
    rmdir src/proto/src/proto src/proto/src 2>/dev/null || true
fi

# Create logs directory if it doesn't exist
mkdir -p logs

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

# Get local IP addresses
echo "Getting local IP addresses..."
local_ips=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')

echo "Local IP addresses: $local_ips"

# Convert the local IPs into a Python-friendly format
local_ips_python=$(echo "$local_ips" | tr ' ' ',')

# Read server information from config.json using Python, filtering by local IPs
servers=$(python3 -c "
import json

# Get local IPs as a list
local_ips = \"$local_ips_python\".split(',')
local_ips = [ip for ip in local_ips if ip]  # Remove empty strings
print(f'Local IPs: {local_ips}')

with open('config/config.json') as f:
    data = json.load(f)
    for server in data['servers']:
        if server['ip'] in local_ips:
            print(f\"{server['id']} {server['ip']} {server['port']}\")
")

if [ -z "$servers" ]; then
    echo "No servers found with local IP addresses. Available IPs: $local_ips"
    exit 1
fi

# Stop any running grpc_server.py processes
echo "Stopping any existing servers..."
pkill -f "python3.*src/grpc_server.py" || true
sleep 1

# Start each server in the background
echo "Starting local servers..."

while read -r id ip port; do
    if port_in_use "$port"; then
        echo "Port $port is already in use. Cannot start server $id."
        continue
    fi

    echo "Starting server $id on $ip:$port"
    python3 src/grpc_server.py --id "$id" --ip "$ip" --port "$port" > "logs/server_$id.log" 2>&1 &

    sleep 0.5
done <<< "$servers"

echo "All local servers started. Use 'tail -f logs/server_*.log' to view logs."
echo "Press Ctrl+C to stop all servers."

# Gracefully handle Ctrl+C
trap "echo 'Stopping all servers...'; pkill -f 'python3.*src/grpc_server.py' || true; exit 0" INT

# Keep the script running until manually interrupted
while true; do
    sleep 1
done

# Distributed Key-Value Store with gRPC

A distributed key-value store implementation using gRPC with consistent hashing, replication, and quorum-based consensus.

## Features

- **Consistent Hashing**: Uses MurmurHash to distribute keys across servers
- **Replication**: Each key is replicated across multiple servers
- **Quorum Consensus**: Read and write operations use quorum for consistency
- **Ranking and Load Awareness**: Servers prioritize operations based on load
- **Eventual Consistency**: Ensures eventual propagation of writes

## Architecture

The key-value store consists of:

1. **Consistent Hashing Ring**: Distributes keys across the server cluster
2. **Server Ranking**: Tracks server load for optimal request distribution
3. **Quorum-based Operations**: Ensures data consistency and availability
4. **gRPC Communication**: Facilitates client-server and server-server communication

## Project Structure

The project is organized in the following directory structure:

- `src/`: Source code directory
  - `utils/`: Utility modules
    - `config.py`: Configuration management
    - `hashing.py`: MurmurHash and consistent hashing implementation
    - `rank.py`: Server rank management
    - `storage.py`: Local key-value storage with timestamp versioning 
    - `quorum.py`: Quorum consensus logic
  - `proto/`: Protocol buffer definitions and generated code
    - `keyvalue.proto`: gRPC service definitions
  - `grpc_server.py`: Server implementation
  - `grpc_client.py`: Client library and CLI
  - `main.py`: Main entry point

- `scripts/`: Utility scripts
  - `run_servers.sh`: Script to run all servers in the cluster
  - `generate_grpc.sh`: Script to generate gRPC code from proto files

- `config/`: Configuration files
  - `config.json`: Main configuration file

- `logs/`: Log files
  - `server_*.log`: Server logs
  - `client.log`: Client logs

- `tests/`: Test files (for future implementation)

## Setup and Installation

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Generate gRPC code:
   ```
   ./scripts/generate_grpc.sh
   ```

3. Configure the system by editing `config/config.json` (adjust cluster size, replication factor, etc.)

## Running the Key-Value Store

1. Start all servers using the provided script:
   ```
   ./scripts/run_servers.sh
   ```

2. Use the client to interact with the store:
   ```
   python src/grpc_client.py
   ```

## Client Usage

The client provides a simple CLI with the following commands:

- `get <key>`: Retrieve a value
- `put <key> <value>`: Store a key-value pair
- `delete <key>`: Delete a key
- `keys`: List all keys (debugging)
- `exit`: Quit the client

You can also specify a server to connect to:
```
python grpc_client.py --server 127.0.0.1:50050
```

## Configuration

Edit `config.json` to configure:

- `cluster_size`: Number of servers in the cluster
- `replication_factor`: Number of servers each key is stored on
- `write_quorum`: Minimum servers for a successful write
- `read_quorum`: Minimum servers for a successful read
- `servers`: Array of server configurations (id, ip, port)
- `heartbeat_interval`: Interval for server heartbeats in seconds 
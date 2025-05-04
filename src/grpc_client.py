import sys
import random
import logging
import os
import grpc
import argparse

# Ensure the proto directory is in the path
proto_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proto")
sys.path.append(proto_dir)

# Import the generated protocol code
import keyvalue_pb2
import keyvalue_pb2_grpc

# Import our own modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.config import get_config

# Setup logging
def setup_logging():
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(logs_dir, "client.log")
    
    # Setup root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

class KeyValueClient:
    """Client for interacting with the distributed key-value store."""
    
    def __init__(self, server_address=None):
        """
        Initialize the client.
        
        Args:
            server_address: Optional server address to connect to. If None, a random server 
                           from the config will be chosen.
        """
        self.config = get_config()
        
        if server_address is None:
            # Pick a random server from config
            server = random.choice(self.config.get_all_servers())
            server_address = f"{server['ip']}:{server['port']}"
        
        self.server_address = server_address
        logger.info(f"Connecting to server at {server_address}")
    
    def get(self, key):
        """
        Get a value for a key.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The value if found, None otherwise
        """
        try:
            with grpc.insecure_channel(self.server_address) as channel:
                stub = keyvalue_pb2_grpc.KeyValueServiceStub(channel)
                response = stub.Get(keyvalue_pb2.GetRequest(key=key))
                
                if response.success:
                    logger.info(f"Retrieved key {key}: {response.value}")
                    return response.value
                else:
                    logger.info(f"Key {key} not found")
                    return None
        except Exception as e:
            logger.error(f"Error in Get for key {key}: {e}")
            return None
    
    def put(self, key, value):
        """
        Store a key-value pair.
        
        Args:
            key: The key to store
            value: The value to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with grpc.insecure_channel(self.server_address) as channel:
                stub = keyvalue_pb2_grpc.KeyValueServiceStub(channel)
                response = stub.Put(
                    keyvalue_pb2.PutRequest(key=key, value=value)
                )
                
                if response.success:
                    logger.info(f"Stored key {key} with timestamp {response.timestamp}")
                    return True
                else:
                    logger.error(f"Failed to store key {key}")
                    return False
        except Exception as e:
            logger.error(f"Error in Put for key {key}: {e}")
            return False
    
    def delete(self, key):
        """
        Delete a key.
        
        Args:
            key: The key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with grpc.insecure_channel(self.server_address) as channel:
                stub = keyvalue_pb2_grpc.KeyValueServiceStub(channel)
                response = stub.Delete(keyvalue_pb2.DeleteRequest(key=key))
                
                if response.success:
                    logger.info(f"Deleted key {key}")
                    return True
                else:
                    logger.error(f"Failed to delete key {key}")
                    return False
        except Exception as e:
            logger.error(f"Error in Delete for key {key}: {e}")
            return False
    
    def get_all_keys(self):
        """
        Get all keys from the server (for debugging).
        
        Returns:
            List of keys
        """
        try:
            with grpc.insecure_channel(self.server_address) as channel:
                stub = keyvalue_pb2_grpc.KeyValueServiceStub(channel)
                response = stub.GetAllKeys(keyvalue_pb2.GetAllKeysRequest())
                return list(response.keys)
        except Exception as e:
            logger.error(f"Error in GetAllKeys: {e}")
            return []


def interactive_cli():
    """Run an interactive command-line interface for the key-value store."""
    parser = argparse.ArgumentParser(description="Key-Value Store Client")
    parser.add_argument("--server", type=str, help="Server address (ip:port)")
    args = parser.parse_args()
    
    client = KeyValueClient(args.server)
    
    print("Key-Value Store Client")
    print("Available commands:")
    print("  get <key>")
    print("  put <key> <value>")
    print("  delete <key>")
    print("  keys")
    print("  exit")
    
    while True:
        try:
            command = input("> ").strip().split()
            if not command:
                continue
            
            cmd = command[0].lower()
            
            if cmd == "exit":
                print("Exiting...")
                break
            elif cmd == "get" and len(command) == 2:
                value = client.get(command[1])
                if value is not None:
                    print(f"Value: {value}")
                else:
                    print("Key not found")
            elif cmd == "put" and len(command) >= 3:
                key = command[1]
                value = " ".join(command[2:])
                success = client.put(key, value)
                if success:
                    print(f"Stored {key}={value}")
                else:
                    print("Failed to store value")
            elif cmd == "delete" and len(command) == 2:
                success = client.delete(command[1])
                if success:
                    print(f"Deleted {command[1]}")
                else:
                    print("Failed to delete key")
            elif cmd == "keys":
                keys = client.get_all_keys()
                if keys:
                    print("Keys on server:")
                    for key in keys:
                        print(f"  {key}")
                else:
                    print("No keys found")
            else:
                print("Invalid command")
                print("Available commands:")
                print("  get <key>")
                print("  put <key> <value>")
                print("  delete <key>")
                print("  keys")
                print("  exit")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    interactive_cli() 
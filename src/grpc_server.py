import sys
import threading
import time
import logging
import os
from concurrent import futures
import argparse
import grpc

# Import the generated protocol code
# Ensure the proto directory is in the path
proto_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proto")
sys.path.append(proto_dir)

import keyvalue_pb2
import keyvalue_pb2_grpc

# Import our own modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.config import get_config
from utils.hashing import get_hash_ring
from utils.rank import get_rank_manager
from utils.storage import get_store
from utils.quorum import get_quorum_manager
from utils.work_stealing import WorkStealingManager

# Setup logging
def setup_logging(server_id):
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(logs_dir, f"server_{server_id}.log")
    
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

# The logger will be initialized when server starts
logger = None

class KeyValueServicer(keyvalue_pb2_grpc.KeyValueServiceServicer):
    """Implementation of the client-facing KeyValueService."""
    
    def __init__(self, server_id, server_address):
        self.server_id = server_id
        self.server_address = server_address
        self.config = get_config()
        self.hash_ring = get_hash_ring()
        self.rank_manager = get_rank_manager(server_id, self.config.heartbeat_interval)
        self.store = get_store(server_id)
        self.quorum_manager = get_quorum_manager()
        self.work_stealing_manager = WorkStealingManager(server_id, self.rank_manager)
        self.work_stealing_manager.start_work_stealing()
    
    def Get(self, request, context):
        """Handle client Get request."""
        logger.info(f"Received Get request for key: {request.key}")
        
        # Add to work stealing queue
        self.work_stealing_manager.add_message(request.key, "", int(time.time() * 1000), "GET")
        
        # Increment active requests
        self.rank_manager.increment_active_requests()
        
        try:
            # Find responsible servers for this key using consistent hashing
            responsible_servers = self._get_servers_for_key(request.key)
            server_ids = [server_id for server_id, _ in responsible_servers]
            
            # Sort servers by rank
            ranked_server_ids = self.rank_manager.get_servers_by_rank(server_ids)
            
            # Query the top read_quorum servers
            top_servers = ranked_server_ids[:self.config.read_quorum]
            
            # Create a function to read from a server
            def read_from_server(server_id, key):
                if server_id == self.server_id:
                    # Read locally
                    return self.store.get(key)
                else:
                    # Forward to the appropriate server
                    return self._forward_read(server_id, key)
            
            # Perform quorum read
            success, value, timestamp = self.quorum_manager.perform_read_quorum(
                top_servers, read_from_server, request.key
            )
            
            return keyvalue_pb2.GetResponse(
                success=success,
                value="" if value is None else value,
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Error in Get: {e}")
            return keyvalue_pb2.GetResponse(success=False, value="", timestamp=0)
        finally:
            # Decrement active requests
            self.rank_manager.decrement_active_requests()
    
    def Put(self, request, context):
        """Handle client Put request."""
        logger.info(f"Received Put request for key: {request.key}, value: {request.value}")
        
        # Add to work stealing queue
        self.work_stealing_manager.add_message(request.key, request.value, int(time.time() * 1000), "PUT")
        
        # Increment active requests
        self.rank_manager.increment_active_requests()
        
        try:
            # Find responsible servers for this key using consistent hashing
            responsible_servers = self._get_servers_for_key(request.key)
            server_ids = [server_id for server_id, _ in responsible_servers]
            
            # Sort servers by rank
            ranked_server_ids = self.rank_manager.get_servers_by_rank(server_ids)
            
            # Generate a timestamp for this write
            timestamp = int(time.time() * 1000)
            
            # Create a function to write to a server
            def write_to_server(server_id, key, value, timestamp):
                if server_id == self.server_id:
                    # Write locally
                    actual_timestamp = self.store.put(key, value, timestamp)
                    return True, actual_timestamp
                else:
                    # Replicate to another server
                    return self._replicate_write(server_id, key, value, timestamp)
            
            # Perform quorum write
            success, actual_timestamp = self.quorum_manager.perform_write_quorum(
                ranked_server_ids, write_to_server, request.key, request.value, timestamp
            )
            
            return keyvalue_pb2.PutResponse(success=success, timestamp=actual_timestamp)
            
        except Exception as e:
            logger.error(f"Error in Put: {e}")
            return keyvalue_pb2.PutResponse(success=False, timestamp=0)
        finally:
            # Decrement active requests
            self.rank_manager.decrement_active_requests()
    
    def Delete(self, request, context):
        """Handle client Delete request."""
        logger.info(f"Received Delete request for key: {request.key}")
        
        # Add to work stealing queue
        self.work_stealing_manager.add_message(request.key, "", int(time.time() * 1000), "DELETE")
        
        # Increment active requests
        self.rank_manager.increment_active_requests()
        
        try:
            # For simplicity, implement delete as a special write with empty value
            empty_put = keyvalue_pb2.PutRequest(key=request.key, value="")
            put_response = self.Put(empty_put, context)
            
            return keyvalue_pb2.DeleteResponse(success=put_response.success)
            
        except Exception as e:
            logger.error(f"Error in Delete: {e}")
            return keyvalue_pb2.DeleteResponse(success=False)
        finally:
            # Decrement active requests
            self.rank_manager.decrement_active_requests()
    
    def GetAllKeys(self, request, context):
        """Handle client GetAllKeys request (for debugging)."""
        logger.info("Received GetAllKeys request")
        
        # This is just from the current server for debugging
        keys = self.store.get_all_keys()
        return keyvalue_pb2.GetAllKeysResponse(keys=keys)
    
    def _get_servers_for_key(self, key):
        """Get the servers responsible for a key based on consistent hashing."""
        return self.hash_ring.get_n_servers_for_key(key, self.config.replication_factor)
    
    def _forward_read(self, server_id, key):
        """Forward a read request to another server."""
        server_address = self.config.get_server_address(server_id)
        try:
            with grpc.insecure_channel(server_address) as channel:
                stub = keyvalue_pb2_grpc.InternalServiceStub(channel)
                response = stub.ForwardRead(keyvalue_pb2.ForwardReadRequest(key=key))
                if response.success:
                    return response.value, response.timestamp
                else:
                    return None, 0
        except Exception as e:
            logger.error(f"Error forwarding read to {server_address}: {e}")
            return None, 0
    
    def _replicate_write(self, server_id, key, value, timestamp):
        """Replicate a write to another server."""
        server_address = self.config.get_server_address(server_id)
        try:
            with grpc.insecure_channel(server_address) as channel:
                stub = keyvalue_pb2_grpc.InternalServiceStub(channel)
                response = stub.ReplicateWrite(
                    keyvalue_pb2.ReplicateWriteRequest(
                        key=key, value=value, timestamp=timestamp
                    )
                )
                return response.success, response.timestamp
        except Exception as e:
            logger.error(f"Error replicating write to {server_address}: {e}")
            return False, 0


class InternalServicer(keyvalue_pb2_grpc.InternalServiceServicer):
    """Implementation of the internal server-to-server service."""
    
    def __init__(self, server_id, server_address):
        self.server_id = server_id
        self.server_address = server_address
        self.config = get_config()
        self.rank_manager = get_rank_manager(server_id, self.config.heartbeat_interval)
        self.store = get_store(server_id)
        self.work_stealing_manager = WorkStealingManager(server_id, self.rank_manager)
    
    def ReplicateWrite(self, request, context):
        """Handle replication of a write from another server."""
        logger.info(f"Received replication write for key: {request.key}, timestamp: {request.timestamp}")
        
        # Store the key-value with the provided timestamp
        actual_timestamp = self.store.put(request.key, request.value, request.timestamp)
        
        return keyvalue_pb2.ReplicateWriteResponse(
            success=True, timestamp=actual_timestamp
        )
    
    def ForwardRead(self, request, context):
        """Handle forwarded read from another server."""
        logger.info(f"Received forwarded read for key: {request.key}")
        
        # Read from local store
        value, timestamp = self.store.get(request.key)
        
        return keyvalue_pb2.ForwardReadResponse(
            success=True,
            value="" if value is None else value,
            timestamp=timestamp
        )
    
    def Heartbeat(self, request, context):
        """Handle heartbeat from another server."""
        logger.debug(f"Received heartbeat from server {request.server_id} with rank {request.rank}")
        
        # Update the stored rank for this server
        self.rank_manager.update_server_rank(request.server_id, request.rank)
        
        return keyvalue_pb2.HeartbeatResponse(success=True)

    def GetServerStatus(self, request, context):
        """Handle server status request for work stealing."""
        logger.info(f"Received server status request from server {request.requesting_server_id}")
        
        return keyvalue_pb2.ServerStatusResponse(
            queue_length=self.work_stealing_manager.get_queue_length(),
            cpu_utilization=self.work_stealing_manager.get_cpu_utilization(),
            active_requests=self.rank_manager.active_requests,
            server_rank=self.rank_manager.get_rank()
        )

    def RequestWorkSteal(self, request, context):
        """Handle work steal request from another server."""
        logger.info(f"Received work steal request from server {request.requesting_server_id}")
        
        # Only give work if the requesting server is less loaded
        if request.requesting_server_rank >= self.rank_manager.get_rank():
            return keyvalue_pb2.WorkStealResponse(success=False, messages=[])
        
        # Get messages to give away
        messages_to_give = []
        for _ in range(request.max_messages_to_steal):
            try:
                message = self.work_stealing_manager.pending_messages.get_nowait()
                messages_to_give.append(keyvalue_pb2.PendingMessage(
                    key=message['key'],
                    value=message['value'],
                    timestamp=message['timestamp'],
                    operation_type=message['operation_type']
                ))
            except:
                break
        
        return keyvalue_pb2.WorkStealResponse(
            success=len(messages_to_give) > 0,
            messages=messages_to_give
        )


def send_heartbeats(server_id, server_addresses):
    """Send heartbeats to all other servers."""
    rank_manager = get_rank_manager(server_id)
    
    def heartbeat_callback(server_id, rank):
        for target_id, target_address in server_addresses.items():
            if target_id != server_id:  # Don't send to self
                try:
                    with grpc.insecure_channel(target_address) as channel:
                        stub = keyvalue_pb2_grpc.InternalServiceStub(channel)
                        stub.Heartbeat(
                            keyvalue_pb2.HeartbeatRequest(server_id=server_id, rank=rank)
                        )
                except Exception as e:
                    logger.debug(f"Failed to send heartbeat to {target_address}: {e}")
    
    # Start sending heartbeats
    rank_manager.start_heartbeat(heartbeat_callback)


def serve(server_id, server_ip, server_port):
    global logger
    
    # Setup logging for this server
    logger = setup_logging(server_id)
    
    # Log server start
    server_address = f"{server_ip}:{server_port}"
    logger.info(f"Server {server_id} started on {server_address}")
    
    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Register servicers
    keyvalue_pb2_grpc.add_KeyValueServiceServicer_to_server(
        KeyValueServicer(server_id, server_address), server
    )
    keyvalue_pb2_grpc.add_InternalServiceServicer_to_server(
        InternalServicer(server_id, server_address), server
    )
    
    # Add secure port with insecure credentials (for simplicity)
    server.add_insecure_port(server_address)
    
    # Start server
    server.start()
    
    # Start background heartbeat thread
    server_addresses = {s["id"]: f"{s['ip']}:{s['port']}" for s in get_config().get_all_servers()}
    heartbeat_thread = threading.Thread(
        target=send_heartbeats,
        args=(server_id, server_addresses),
        daemon=True
    )
    heartbeat_thread.start()
    
    # Keep thread alive
    try:
        while True:
            time.sleep(86400)  # Sleep for a day
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Key-Value Store Server")
    parser.add_argument("--id", type=int, required=True, help="Server ID")
    parser.add_argument("--ip", type=str, required=True, help="Server IP")
    parser.add_argument("--port", type=int, required=True, help="Server Port")
    
    args = parser.parse_args()
    serve(args.id, args.ip, args.port) 
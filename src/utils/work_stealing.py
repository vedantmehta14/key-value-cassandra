import threading
import time
import logging
import grpc
import psutil
from typing import List, Dict, Any, Optional
from queue import Queue
import random

from utils.config import get_config
from utils.rank import RankManager
import keyvalue_pb2
import keyvalue_pb2_grpc

logger = logging.getLogger(__name__)

class WorkStealingManager:
    def __init__(self, server_id: int, rank_manager: RankManager):
        self.server_id = server_id
        self.rank_manager = rank_manager
        self.config = get_config()
        
        # Queue for pending messages
        self.pending_messages = Queue()
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Background thread for work stealing
        self.stealing_thread = None
        self.running = False
        
        # Configuration for work stealing - More aggressive settings
        self.stealing_interval = 2  # seconds (reduced from 5)
        self.min_queue_length_for_stealing = 5  # reduced from 10
        self.max_messages_to_steal = 10  # increased from 5
        self.stealing_threshold = 0.3  # reduced from 0.7 (steal if queue is 30% of others)
        
        # Track stolen messages for logging
        self.stolen_messages = []
    
    def start_work_stealing(self):
        """Start the work stealing background thread."""
        self.running = True
        self.stealing_thread = threading.Thread(target=self._work_stealing_loop, daemon=True)
        self.stealing_thread.start()
        logger.info(f"Server {self.server_id} started work stealing thread")
    
    def stop_work_stealing(self):
        """Stop the work stealing background thread."""
        self.running = False
        if self.stealing_thread:
            self.stealing_thread.join(timeout=self.stealing_interval)
            logger.info(f"Server {self.server_id} stopped work stealing thread")
    
    def add_message(self, key: str, value: str, timestamp: int, operation_type: str):
        """Add a message to the pending queue."""
        with self.lock:
            self.pending_messages.put({
                'key': key,
                'value': value,
                'timestamp': timestamp,
                'operation_type': operation_type
            })
    
    def get_queue_length(self) -> int:
        """Get the current length of the pending messages queue."""
        return self.pending_messages.qsize()
    
    def get_cpu_utilization(self) -> float:
        """Get current CPU utilization."""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception as e:
            logger.warning(f"Failed to get CPU usage: {e}")
            return 50.0
    
    def _work_stealing_loop(self):
        """Background loop that attempts to steal work from other servers."""
        while self.running:
            try:
                # Only attempt to steal if our queue is relatively empty
                if self.get_queue_length() < self.min_queue_length_for_stealing:
                    self._attempt_work_stealing()
            except Exception as e:
                logger.error(f"Error in work stealing loop: {e}")
            
            time.sleep(self.stealing_interval)
    
    def _attempt_work_stealing(self):
        """Attempt to steal work from other servers."""
        # Get all server statuses
        server_statuses = self._get_all_server_statuses()
        
        # Find potential victims (servers with more work)
        victims = []
        our_queue_length = self.get_queue_length()
        
        for server_id, status in server_statuses.items():
            if server_id != self.server_id:
                # More aggressive conditions for work stealing
                if (status['queue_length'] > our_queue_length * (1 + self.stealing_threshold) or  # Queue length condition
                    status['cpu_utilization'] > 50 or  # Reduced CPU threshold from 70
                    status['server_rank'] > self.rank_manager.get_rank()):  # Rank condition
                    victims.append((server_id, status))
        
        # Sort victims by queue length (most loaded first)
        victims.sort(key=lambda x: x[1]['queue_length'], reverse=True)
        
        # Try to steal from each victim
        for victim_id, victim_status in victims:
            if self._steal_from_server(victim_id):
                # Continue stealing from other victims even after a successful steal
                continue
    
    def _get_all_server_statuses(self) -> Dict[int, Dict[str, Any]]:
        """Get status information from all servers."""
        statuses = {}
        
        for server in self.config.get_all_servers():
            if server['id'] != self.server_id:
                try:
                    with grpc.insecure_channel(f"{server['ip']}:{server['port']}") as channel:
                        stub = keyvalue_pb2_grpc.InternalServiceStub(channel)
                        response = stub.GetServerStatus(
                            keyvalue_pb2.ServerStatusRequest(requesting_server_id=self.server_id)
                        )
                        statuses[server['id']] = {
                            'queue_length': response.queue_length,
                            'cpu_utilization': response.cpu_utilization,
                            'active_requests': response.active_requests,
                            'server_rank': response.server_rank
                        }
                except Exception as e:
                    logger.warning(f"Failed to get status from server {server['id']}: {e}")
        
        return statuses
    
    def _steal_from_server(self, victim_id: int) -> bool:
        """Attempt to steal work from a specific server."""
        try:
            server = self.config.get_server_by_id(victim_id)
            with grpc.insecure_channel(f"{server['ip']}:{server['port']}") as channel:
                stub = keyvalue_pb2_grpc.InternalServiceStub(channel)
                response = stub.RequestWorkSteal(
                    keyvalue_pb2.WorkStealRequest(
                        requesting_server_id=self.server_id,
                        requesting_server_rank=self.rank_manager.get_rank(),
                        max_messages_to_steal=self.max_messages_to_steal
                    )
                )
                
                if response.success and response.messages:
                    # Add stolen messages to our queue
                    for msg in response.messages:
                        self.add_message(
                            msg.key,
                            msg.value,
                            msg.timestamp,
                            msg.operation_type
                        )
                    
                    # Log the stolen messages
                    self._log_stolen_messages(victim_id, response.messages)
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to steal from server {victim_id}: {e}")
            return False
    
    def _log_stolen_messages(self, victim_id: int, messages: List[Any]):
        """Log information about stolen messages."""
        for msg in messages:
            log_entry = {
                'timestamp': time.time(),
                'victim_server_id': victim_id,
                'stolen_by_server_id': self.server_id,
                'message_key': msg.key,
                'operation_type': msg.operation_type,
                'original_timestamp': msg.timestamp
            }
            self.stolen_messages.append(log_entry)
            logger.info(f"Stole message from server {victim_id}: {log_entry}")
    
    def get_stolen_messages_log(self) -> List[Dict[str, Any]]:
        """Get the log of stolen messages."""
        return self.stolen_messages 
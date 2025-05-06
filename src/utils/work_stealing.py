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
        

        self.pending_messages = Queue()
        

        self.lock = threading.RLock()
        

        self.stealing_thread = None
        self.running = False
        
       
        self.stealing_interval = 2
        self.min_queue_length_for_stealing = 5  
        self.max_messages_to_steal = 10  
        self.stealing_threshold = 0.3  
        

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
                
                if self.get_queue_length() < self.min_queue_length_for_stealing:
                    self._attempt_work_stealing()
            except Exception as e:
                logger.error(f"Error in work stealing loop: {e}")
            
            time.sleep(self.stealing_interval)
    
    def _attempt_work_stealing(self):
        """Attempt to steal work from other servers."""

        server_statuses = self._get_all_server_statuses()
        
        victims = []
        our_queue_length = self.get_queue_length()
        
        for server_id, status in server_statuses.items():
            if server_id != self.server_id:
            
                if (status['queue_length'] > our_queue_length * (1 + self.stealing_threshold) or  
                    status['cpu_utilization'] > 50 or  # Reduced CPU threshold from 70
                    status['server_rank'] > self.rank_manager.get_rank()): 
                    victims.append((server_id, status))
        
       
        victims.sort(key=lambda x: x[1]['queue_length'], reverse=True)
        
       
        for victim_id, victim_status in victims:
            if self._steal_from_server(victim_id):
                
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
import time
import threading
from typing import Dict, Any, Callable
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RankManager:
    def __init__(self, server_id: int, heartbeat_interval: int = 5):
        self.server_id = server_id
        self.heartbeat_interval = heartbeat_interval
        self.active_requests = 0
        self.lock = threading.RLock()
        
        # Store ranks from other servers: {server_id: (rank, timestamp)}
        self.server_ranks = {}
        
        # Background thread for sending heartbeats
        self.heartbeat_thread = None
        self.running = False
        self.heartbeat_callback = None
    
    def start_heartbeat(self, callback: Callable[[int, int], None]):
        """Start sending heartbeats at regular intervals.
        
        Args:
            callback: Function that takes (server_id, rank) and sends heartbeat
        """
        self.heartbeat_callback = callback
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        logger.info(f"Server {self.server_id} started heartbeat thread")
    
    def stop_heartbeat(self):
        """Stop the heartbeat thread."""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=self.heartbeat_interval)
            logger.info(f"Server {self.server_id} stopped heartbeat thread")
    
    def _heartbeat_loop(self):
        """Background loop that sends heartbeats."""
        while self.running:
            try:
                current_rank = self.get_rank()
                if self.heartbeat_callback:
                    self.heartbeat_callback(self.server_id, current_rank)
            except Exception as e:
                logger.error(f"Error in heartbeat: {e}")
            
            time.sleep(self.heartbeat_interval)
    
    def increment_active_requests(self):
        """Increment the count of active requests."""
        with self.lock:
            self.active_requests += 1
    
    def decrement_active_requests(self):
        """Decrement the count of active requests."""
        with self.lock:
            self.active_requests = max(0, self.active_requests - 1)
    
    def get_rank(self) -> int:
        """Calculate and return the current rank of this server."""
        with self.lock:
            # For now, just use the number of active requests as the rank
            # Lower rank means less loaded (better)
            return self.active_requests
    
    def update_server_rank(self, server_id: int, rank: int):
        """Update the stored rank for another server."""
        with self.lock:
            self.server_ranks[server_id] = (rank, time.time())
    
    def get_server_rank(self, server_id: int) -> int:
        """Get the rank of a specific server."""
        with self.lock:
            if server_id == self.server_id:
                return self.get_rank()
            
            if server_id in self.server_ranks:
                rank, timestamp = self.server_ranks[server_id]
                
                # If rank is too old, consider it stale
                if time.time() - timestamp > self.heartbeat_interval * 3:
                    logger.warning(f"Rank for server {server_id} is stale")
                
                return rank
            
            # Default to a high rank if we don't know about this server
            return float('inf')
    
    def get_servers_by_rank(self, server_ids):
        """Sort the given server IDs by their rank (ascending)."""
        with self.lock:
            servers_with_ranks = [(server_id, self.get_server_rank(server_id)) for server_id in server_ids]
            # Sort by rank (lower rank first)
            return [server_id for server_id, _ in sorted(servers_with_ranks, key=lambda x: x[1])]


# Dictionary to store RankManager instances per server
_rank_instances = {}

def get_rank_manager(server_id: int, heartbeat_interval: int = 5):
    """Get or create a RankManager instance for a specific server."""
    global _rank_instances
    if server_id not in _rank_instances:
        _rank_instances[server_id] = RankManager(server_id, heartbeat_interval)
    return _rank_instances[server_id] 
import threading
from typing import List, Dict, Any, Tuple, Optional, Callable
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuorumManager:
    def __init__(self):
        self.config = get_config()
        self.write_quorum = self.config.write_quorum
        self.read_quorum = self.config.read_quorum
        self.replication_factor = self.config.replication_factor
    
    def perform_write_quorum(
        self, 
        servers: List[int],
        write_func: Callable[[int, str, str, Optional[int]], Tuple[bool, int]],
        key: str,
        value: str,
        timestamp: Optional[int] = None
    ) -> Tuple[bool, int]:
        """
        Perform a write operation with quorum consensus.
        
        Args:
            servers: List of server IDs to write to
            write_func: Function to call for writing (server_id, key, value, timestamp) -> (success, timestamp)
            key: Key to write
            value: Value to write
            timestamp: Optional timestamp
            
        Returns:
            Tuple of (success, highest_timestamp)
        """
        if len(servers) < self.write_quorum:
            logger.error(f"Not enough servers available for write quorum: {len(servers)} < {self.write_quorum}")
            return False, 0
        
        results = []
        max_timestamp = timestamp if timestamp is not None else int(time.time() * 1000)
        successful_writes = 0
        
        # Using ThreadPoolExecutor for parallel writes
        with ThreadPoolExecutor(max_workers=len(servers)) as executor:
            # Submit all write requests
            future_to_server = {
                executor.submit(write_func, server_id, key, value, max_timestamp): server_id
                for server_id in servers
            }
            
            # Process results as they complete
            for future in future_to_server:
                try:
                    success, timestamp_response = future.result()
                    server_id = future_to_server[future]
                    results.append((server_id, success, timestamp_response))
                    
                    if success:
                        successful_writes += 1
                        max_timestamp = max(max_timestamp, timestamp_response)
                    
                    # Early exit if we have enough successful writes
                    if successful_writes >= self.write_quorum:
                        break
                        
                except Exception as e:
                    logger.error(f"Error during write quorum: {e}")
        
        # Check if we achieved quorum
        achieved_quorum = successful_writes >= self.write_quorum
        logger.info(f"Write quorum {'achieved' if achieved_quorum else 'failed'}: {successful_writes}/{self.write_quorum}")
        
        # If we achieved quorum but not all servers were updated, we need to ensure eventual consistency
        if achieved_quorum and successful_writes < len(servers):
            # This should be handled by a background process for eventual consistency
            # Here we'll just log it
            unwritten_servers = [s for s, success, _ in results if not success] + \
                             [s for s in servers if s not in [server_id for server_id, _, _ in results]]
            logger.info(f"Need eventual consistency for servers: {unwritten_servers}")
            
            # In a real implementation, you would start a background task to retry these servers
        
        return achieved_quorum, max_timestamp
    
    def perform_read_quorum(
        self,
        servers: List[int],
        read_func: Callable[[int, str], Tuple[Optional[str], int]],
        key: str
    ) -> Tuple[bool, Optional[str], int]:
        """
        Perform a read operation with quorum consensus.
        
        Args:
            servers: List of server IDs to read from
            read_func: Function to call for reading (server_id, key) -> (value, timestamp)
            key: Key to read
            
        Returns:
            Tuple of (success, latest_value, latest_timestamp)
        """
        if len(servers) < self.read_quorum:
            logger.error(f"Not enough servers available for read quorum: {len(servers)} < {self.read_quorum}")
            return False, None, 0
        
        results = []
        successful_reads = 0
        
        # Using ThreadPoolExecutor for parallel reads
        with ThreadPoolExecutor(max_workers=len(servers)) as executor:
            # Submit all read requests
            future_to_server = {
                executor.submit(read_func, server_id, key): server_id
                for server_id in servers
            }
            
            # Process results as they complete
            for future in future_to_server:
                try:
                    value, timestamp = future.result()
                    server_id = future_to_server[future]
                    
                    # Consider a read successful if we got a timestamp, even if value is None
                    # This handles deleted keys consistently
                    successful_reads += 1
                    results.append((server_id, value, timestamp))
                    
                    # Early exit if we have enough successful reads
                    if successful_reads >= self.read_quorum:
                        break
                        
                except Exception as e:
                    logger.error(f"Error during read quorum: {e}")
        
        # Check if we achieved quorum
        achieved_quorum = successful_reads >= self.read_quorum
        
        if not achieved_quorum:
            logger.info(f"Read quorum failed: {successful_reads}/{self.read_quorum}")
            return False, None, 0
        
        # Find the latest value based on timestamp
        latest_server_id = None
        latest_value = None
        latest_timestamp = 0
        
        for server_id, value, timestamp in results:
            if timestamp > latest_timestamp:
                latest_timestamp = timestamp
                latest_value = value
                latest_server_id = server_id
        
        logger.info(f"Read quorum achieved: {successful_reads}/{self.read_quorum}, " +
                   f"latest value from server {latest_server_id} with timestamp {latest_timestamp}")
        
        return True, latest_value, latest_timestamp


# Singleton instance
_quorum_instance = None

def get_quorum_manager():
    """Get or create a QuorumManager instance."""
    global _quorum_instance
    if _quorum_instance is None:
        _quorum_instance = QuorumManager()
    return _quorum_instance 
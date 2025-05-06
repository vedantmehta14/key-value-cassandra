import threading
import time
from typing import Dict, Tuple, Any, Optional, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KeyValueStore:
    def __init__(self):
        # Dictionary to store (value, timestamp) tuples
        self.store: Dict[str, Tuple[str, int]] = {}
        self.lock = threading.RLock()
    
    def put(self, key: str, value: str, timestamp: Optional[int] = None) -> int:
        """
        Store a key-value pair with a logical timestamp.
    
        """
        with self.lock:
            current_timestamp = timestamp if timestamp is not None else int(time.time() * 1000)
            
            
            if key in self.store:
                stored_value, stored_timestamp = self.store[key]
                if current_timestamp <= stored_timestamp:
                    logger.info(f"Ignored write for key {key} with older timestamp {current_timestamp} < {stored_timestamp}")
                    return stored_timestamp
            
            self.store[key] = (value, current_timestamp)
            logger.info(f"Stored {key}:{value} with timestamp {current_timestamp}")
            return current_timestamp
    
    def get(self, key: str) -> Tuple[Optional[str], int]:
        """
        Retrieve a value and its timestamp for a given key.
        
 
        """
        with self.lock:
            if key in self.store:
                value, timestamp = self.store[key]
                logger.info(f"Retrieved {key}:{value} with timestamp {timestamp}")
                return value, timestamp
            else:
                logger.info(f"Key {key} not found")
                return None, 0
    
    def delete(self, key: str, timestamp: Optional[int] = None) -> bool:
        """
        Delete a key from the store.
        
  
        """
        with self.lock:
            current_timestamp = timestamp if timestamp is not None else int(time.time() * 1000)
            

            if key in self.store:
                _, stored_timestamp = self.store[key]
                if current_timestamp <= stored_timestamp:
                    logger.info(f"Ignored delete for key {key} with older timestamp {current_timestamp} < {stored_timestamp}")
                    return False
                
                del self.store[key]
                logger.info(f"Deleted key {key} with timestamp {current_timestamp}")
                return True
            
            logger.info(f"Key {key} not found for deletion")
            return False
    
    def get_all_keys(self) -> List[str]:
        """Return a list of all keys in the store."""
        with self.lock:
            return list(self.store.keys())


_store_instances = {}

def get_store(server_id: int):
    """Get or create a KeyValueStore instance for a specific server."""
    global _store_instances
    if server_id not in _store_instances:
        _store_instances[server_id] = KeyValueStore()
    return _store_instances[server_id] 
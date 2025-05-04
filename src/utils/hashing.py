import hashlib
import struct
import bisect
import sys
import os
from typing import List, Tuple, Dict, Optional, Any

# Add the parent directory to the path to make utils imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import get_config

# Use murmurhash3 algorithm
def murmurhash(key: str, seed: int = 0) -> int:
    """Implement MurmurHash3 for string keys"""
    key_bytes = key.encode('utf-8')
    
    # MurmurHash3 constants
    c1 = 0xcc9e2d51
    c2 = 0x1b873593
    r1 = 15
    r2 = 13
    m = 5
    n = 0xe6546b64
    
    # Initialize hash with seed
    hash_val = seed
    
    # Process 4 bytes at a time
    nblocks = len(key_bytes) // 4
    for i in range(nblocks):
        k = struct.unpack('<I', key_bytes[i*4:(i+1)*4])[0]
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << r1) | (k >> (32 - r1))) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        
        hash_val ^= k
        hash_val = ((hash_val << r2) | (hash_val >> (32 - r2))) & 0xFFFFFFFF
        hash_val = ((hash_val * m) + n) & 0xFFFFFFFF
    
    # Process remaining bytes
    remaining = len(key_bytes) & 3
    if remaining > 0:
        k = 0
        for i in range(remaining):
            k <<= 8
            k |= key_bytes[nblocks*4 + i]
        
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << r1) | (k >> (32 - r1))) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        
        hash_val ^= k
    
    # Finalization
    hash_val ^= len(key_bytes)
    hash_val ^= hash_val >> 16
    hash_val = (hash_val * 0x85ebca6b) & 0xFFFFFFFF
    hash_val ^= hash_val >> 13
    hash_val = (hash_val * 0xc2b2ae35) & 0xFFFFFFFF
    hash_val ^= hash_val >> 16
    
    return hash_val


class ConsistentHashRing:
    def __init__(self, num_virtual_nodes: int = 10):
        self.num_virtual_nodes = num_virtual_nodes
        self.ring = {}  # Hash -> (server_id, address)
        self.sorted_keys = []  # Sorted list of hash values
        self.server_node_map = {}  # server_id -> list of hash values
        
        # Load initial servers from config
        config = get_config()
        for server in config.get_all_servers():
            self.add_server(server["id"], f"{server['ip']}:{server['port']}")
    
    def add_server(self, server_id: int, address: str) -> None:
        """Add a server to the hash ring with virtual nodes."""
        if server_id not in self.server_node_map:
            self.server_node_map[server_id] = []
        
        # Add the server multiple times (virtual nodes) for better distribution
        for i in range(self.num_virtual_nodes):
            virtual_node_key = f"{address}:{i}"
            hash_val = murmurhash(virtual_node_key)
            
            self.ring[hash_val] = (server_id, address)
            self.server_node_map[server_id].append(hash_val)
            
            # Insert maintaining sorted order
            bisect.insort(self.sorted_keys, hash_val)
    
    def remove_server(self, server_id: int) -> None:
        """Remove a server and its virtual nodes from the hash ring."""
        if server_id not in self.server_node_map:
            return
        
        # Remove all virtual nodes for this server
        for hash_val in self.server_node_map[server_id]:
            if hash_val in self.ring:
                del self.ring[hash_val]
                self.sorted_keys.remove(hash_val)
        
        del self.server_node_map[server_id]
    
    def get_server_for_key(self, key: str) -> Tuple[int, str]:
        """Get the server responsible for the given key."""
        if not self.ring:
            raise ValueError("Hash ring is empty")
        
        key_hash = murmurhash(key)
        
        # Find the first node with hash >= key's hash, or wrap around to the first one
        pos = bisect.bisect_left(self.sorted_keys, key_hash) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[pos]]
    
    def get_n_servers_for_key(self, key: str, n: int) -> List[Tuple[int, str]]:
        """Get n servers for the given key moving clockwise on the ring."""
        if not self.ring:
            raise ValueError("Hash ring is empty")
        
        if n > len(self.ring) // self.num_virtual_nodes:
            raise ValueError(f"Cannot get {n} unique servers, only {len(self.ring) // self.num_virtual_nodes} available")
        
        key_hash = murmurhash(key)
        
        # Find the first node with hash >= key's hash
        pos = bisect.bisect_left(self.sorted_keys, key_hash) % len(self.sorted_keys)
        
        result = []
        seen_servers = set()
        
        # Walk clockwise around the ring
        for i in range(len(self.sorted_keys)):
            curr_pos = (pos + i) % len(self.sorted_keys)
            server_id, address = self.ring[self.sorted_keys[curr_pos]]
            
            if server_id not in seen_servers:
                seen_servers.add(server_id)
                result.append((server_id, address))
                
                if len(result) == n:
                    break
        
        return result


# Singleton instance
_ring_instance = None

def get_hash_ring():
    global _ring_instance
    if _ring_instance is None:
        _ring_instance = ConsistentHashRing()
    return _ring_instance 
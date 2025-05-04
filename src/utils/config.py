import json
import os
from typing import Dict, List, Any

class Config:
    def __init__(self, config_file=None):
        if config_file is None:
            # Default to config/config.json relative to project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            config_file = os.path.join(project_root, "config/config.json")
        
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.cluster_size = self.config.get("cluster_size", 10)
        self.replication_factor = self.config.get("replication_factor", 3)
        self.write_quorum = self.config.get("write_quorum", 2)
        self.read_quorum = self.config.get("read_quorum", 2)
        self.servers = self.config.get("servers", [])
        self.heartbeat_interval = self.config.get("heartbeat_interval", 5)
        
        # Validate configuration
        if self.write_quorum > self.replication_factor:
            raise ValueError("Write quorum cannot be greater than replication factor")
        if self.read_quorum > self.replication_factor:
            raise ValueError("Read quorum cannot be greater than replication factor")
        if self.replication_factor > self.cluster_size:
            raise ValueError("Replication factor cannot be greater than cluster size")
        if len(self.servers) != self.cluster_size:
            raise ValueError(f"Number of servers in config ({len(self.servers)}) does not match cluster_size ({self.cluster_size})")
    
    def get_server_by_id(self, server_id: int) -> Dict[str, Any]:
        for server in self.servers:
            if server["id"] == server_id:
                return server
        raise ValueError(f"Server with ID {server_id} not found")
    
    def get_all_servers(self) -> List[Dict[str, Any]]:
        return self.servers
    
    def get_server_address(self, server_id: int) -> str:
        server = self.get_server_by_id(server_id)
        return f"{server['ip']}:{server['port']}"

# Singleton instance
_config_instance = None

def get_config(config_file=None):
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_file)
    return _config_instance 
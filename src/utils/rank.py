import time
import threading
import os
import psutil
import platform
import subprocess
from typing import Dict, Any, Callable, List, Tuple
import logging
import random  # For simulating jitter when real measurement isn't available

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
        
        # Track historical measurements for smoothing
        self.historical_measurements = {
            'active_requests': []
        }
        self.max_history = 5  # Number of historical values to keep
    
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
    
    def _get_cpu_free_percentage(self) -> float:
        """Get percentage of free CPU."""
        try:
            # Get CPU usage as a percentage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            # Convert to free percentage
            return 100.0 - cpu_percent
        except Exception as e:
            logger.warning(f"Failed to get CPU usage: {e}")
            # Return a sensible default
            return 50.0
    
    def _get_memory_free_percentage(self) -> float:
        """Get percentage of free memory."""
        try:
            memory = psutil.virtual_memory()
            return memory.available * 100 / memory.total
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            # Return a sensible default
            return 50.0
    
    def _get_jitter(self) -> float:
        """Measure network jitter (variability in latency).
        
        Returns:
            Jitter value in ms
        """
        try:
            # Simple ping to measure jitter
            if platform.system().lower() == 'windows':
                ping_param = '-n'
            else:
                ping_param = '-c'
            
            # Ping common DNS server (Google's)
            ping_target = '8.8.8.8'
            cmd = ['ping', ping_param, '3', ping_target]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            output_lines = result.stdout.splitlines()
            
            # Extract times from ping output
            times = []
            for line in output_lines:
                if 'time=' in line:
                    # Extract the time value
                    time_part = line.split('time=')[1].split()[0]
                    # Remove 'ms' if present
                    time_value = float(time_part.replace('ms', ''))
                    times.append(time_value)
            
            # Calculate jitter as the standard deviation of ping times
            if times:
                mean = sum(times) / len(times)
                jitter = (sum((t - mean) ** 2 for t in times) / len(times)) ** 0.5
                
                # Return the average jitter over recent measurements
                return jitter
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"Failed to measure jitter: {e}")
            # Simulate some reasonable jitter
            return random.uniform(0.5, 5.0)
    
    def _update_historical(self, metric_name: str, value: float):
        """Update historical measurements for a metric."""
        with self.lock:
            self.historical_measurements[metric_name].append(value)
            if len(self.historical_measurements[metric_name]) > self.max_history:
                self.historical_measurements[metric_name].pop(0)
    
    def _get_smoothed_value(self, metric_name: str, current_value: float) -> float:
        """Get smoothed value using historical measurements."""
        with self.lock:
            history = self.historical_measurements[metric_name]
            if not history:
                return current_value
            
            # Use exponential smoothing
            alpha = 0.3  # Smoothing factor
            smoothed = alpha * current_value
            
            # Add weighted historical values
            weight = (1 - alpha)
            for i, past_value in enumerate(reversed(history)):
                factor = weight / (i + 1)
                smoothed += factor * past_value
            
            return smoothed
    
    def get_rank(self) -> int:
        """Calculate and return the current rank of this server using multiple metrics.
        
        The rank is calculated using:
        1. CPU utilization (40% weight)
        2. Queue length (30% weight)
        3. Active requests (30% weight)
        
        Lower rank means less loaded (better).
        """
        with self.lock:
            # Get current metrics
            cpu_util = self._get_cpu_free_percentage()  # Convert to free percentage
            queue_length = self.work_stealing_manager.get_queue_length() if hasattr(self, 'work_stealing_manager') else 0
            active_requests = self.active_requests
            
            # Store current values for history
            self._update_historical('cpu_utilization', cpu_util)
            self._update_historical('queue_length', queue_length)
            self._update_historical('active_requests', active_requests)
            
            # Get smoothed values
            smoothed_cpu = self._get_smoothed_value('cpu_utilization', cpu_util)
            smoothed_queue = self._get_smoothed_value('queue_length', queue_length)
            smoothed_requests = self._get_smoothed_value('active_requests', active_requests)
            
            # Calculate weighted rank
            # CPU utilization (40% weight) - higher free CPU is better (lower rank)
            cpu_rank = (100 - smoothed_cpu) * 0.4
            
            # Queue length (30% weight) - normalize to 0-100 scale
            max_queue = 100  # Maximum expected queue length
            queue_rank = min(smoothed_queue / max_queue * 100, 100) * 0.3
            
            # Active requests (30% weight) - normalize to 0-100 scale
            max_requests = 50  # Maximum expected concurrent requests
            request_rank = min(smoothed_requests / max_requests * 100, 100) * 0.3
            
            # Calculate final rank
            rank = cpu_rank + queue_rank + request_rank
            
            # Ensure rank is non-negative
            rank = max(0, rank)
            
            logger.debug(f"Rank components - CPU: {cpu_rank:.2f}, Queue: {queue_rank:.2f}, Requests: {request_rank:.2f}, final_rank={rank:.2f}")
            
            return int(rank * 10)  # Scale for integer representation
    
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
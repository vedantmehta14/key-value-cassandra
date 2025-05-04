import sys
import os
import time
import random
import string
import threading
import concurrent.futures
import logging
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# Import client
from grpc_client import KeyValueClient
from utils.config import get_config

# Setup logging
def setup_logging():
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"load_test_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# Generate random data
def generate_random_string(length=10):
    """Generate a random string of letters and digits."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_random_key():
    """Generate a random key."""
    return f"test_key_{generate_random_string(8)}"

def generate_random_value():
    """Generate a random value."""
    return f"test_value_{generate_random_string(20)}"

class OperationResult:
    """Class to track operation results and timing."""
    def __init__(self, operation_type):
        self.operation_type = operation_type
        self.start_time = None
        self.end_time = None
        self.success = False
        self.error = None
    
    def start(self):
        self.start_time = time.time()
        return self
    
    def end(self, success, error=None):
        self.end_time = time.time()
        self.success = success
        self.error = error
        return self
    
    @property
    def duration(self):
        if self.start_time is None or self.end_time is None:
            return None
        return self.end_time - self.start_time

class LoadTester:
    """Load tester for the distributed key-value store."""
    
    def __init__(self, num_clients=1):
        self.config = get_config()
        self.server_addresses = [f"{server['ip']}:{server['port']}" for server in self.config.get_all_servers()]
        self.clients = []
        
        # Initialize clients
        for _ in range(num_clients):
            server_address = random.choice(self.server_addresses)
            self.clients.append(KeyValueClient(server_address))
        
        self.results = []
        logger.info(f"Initialized LoadTester with {num_clients} clients connected to {len(self.server_addresses)} servers")
    
    def _get_client(self):
        """Get a random client."""
        return random.choice(self.clients)
    
    def perform_put_operation(self, key, value):
        """Perform a put operation and record the result."""
        client = self._get_client()
        result = OperationResult("PUT").start()
        
        try:
            success = client.put(key, value)
            return result.end(success)
        except Exception as e:
            logger.error(f"Error in PUT operation for key {key}: {e}")
            return result.end(False, str(e))
    
    def perform_get_operation(self, key):
        """Perform a get operation and record the result."""
        client = self._get_client()
        result = OperationResult("GET").start()
        
        try:
            value = client.get(key)
            return result.end(value is not None)
        except Exception as e:
            logger.error(f"Error in GET operation for key {key}: {e}")
            return result.end(False, str(e))
    
    def perform_delete_operation(self, key):
        """Perform a delete operation and record the result."""
        client = self._get_client()
        result = OperationResult("DELETE").start()
        
        try:
            success = client.delete(key)
            return result.end(success)
        except Exception as e:
            logger.error(f"Error in DELETE operation for key {key}: {e}")
            return result.end(False, str(e))
    
    def run_mixed_workload(self, operations_count, get_ratio=0.7, put_ratio=0.2, delete_ratio=0.1):
        """
        Run a mixed workload with specified ratios of operations.
        
        Args:
            operations_count: Total number of operations to perform
            get_ratio: Ratio of GET operations
            put_ratio: Ratio of PUT operations
            delete_ratio: Ratio of DELETE operations
            
        Returns:
            List of operation results
        """
        logger.info(f"Running mixed workload with {operations_count} operations (GET: {get_ratio}, PUT: {put_ratio}, DELETE: {delete_ratio})")
        
        # Generate keys first for put operations
        keys_to_put = [generate_random_key() for _ in range(int(operations_count * put_ratio))]
        
        # Track which keys were successfully put
        successful_keys = []
        batch_results = []
        
        # Perform PUT operations
        logger.info(f"Performing {len(keys_to_put)} PUT operations")
        for key in keys_to_put:
            value = generate_random_value()
            result = self.perform_put_operation(key, value)
            batch_results.append(result)
            if result.success:
                successful_keys.append(key)
        
        # Perform GET operations
        get_count = int(operations_count * get_ratio)
        logger.info(f"Performing {get_count} GET operations")
        for _ in range(get_count):
            if successful_keys:
                key = random.choice(successful_keys)
                result = self.perform_get_operation(key)
                batch_results.append(result)
            else:
                logger.warning("No successful keys to get, skipping GET operation")
        
        # Perform DELETE operations
        delete_count = int(operations_count * delete_ratio)
        logger.info(f"Performing {delete_count} DELETE operations")
        for _ in range(delete_count):
            if successful_keys:
                key = random.choice(successful_keys)
                result = self.perform_delete_operation(key)
                batch_results.append(result)
                if result.success:
                    successful_keys.remove(key)
            else:
                logger.warning("No successful keys to delete, skipping DELETE operation")
        
        self.results.extend(batch_results)
        return batch_results
    
    def run_parallel_workload(self, operations_per_thread, num_threads):
        """
        Run operations in parallel using multiple threads.
        
        Args:
            operations_per_thread: Number of operations per thread
            num_threads: Number of threads to use
            
        Returns:
            Combined results from all threads
        """
        logger.info(f"Running parallel workload with {num_threads} threads, {operations_per_thread} operations per thread")
        
        all_results = []
        
        def thread_workload():
            return self.run_mixed_workload(operations_per_thread)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_results = [executor.submit(thread_workload) for _ in range(num_threads)]
            
            for future in concurrent.futures.as_completed(future_results):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Thread error: {e}")
        
        return all_results
    
    def analyze_results(self):
        """Analyze the results of load testing."""
        if not self.results:
            logger.warning("No results to analyze")
            return {}
        
        analysis = {
            "total_operations": len(self.results),
            "successful_operations": sum(1 for r in self.results if r.success),
            "failed_operations": sum(1 for r in self.results if not r.success),
            "operation_types": {}
        }
        
        # Calculate success rates and latencies by operation type
        for op_type in ["PUT", "GET", "DELETE"]:
            op_results = [r for r in self.results if r.operation_type == op_type]
            successful_ops = [r for r in op_results if r.success]
            
            if op_results:
                success_rate = len(successful_ops) / len(op_results)
                avg_latency = sum(r.duration for r in successful_ops) / len(successful_ops) if successful_ops else 0
                max_latency = max(r.duration for r in successful_ops) if successful_ops else 0
                min_latency = min(r.duration for r in successful_ops) if successful_ops else 0
                
                analysis["operation_types"][op_type] = {
                    "total": len(op_results),
                    "successful": len(successful_ops),
                    "failed": len(op_results) - len(successful_ops),
                    "success_rate": success_rate,
                    "avg_latency": avg_latency,
                    "max_latency": max_latency,
                    "min_latency": min_latency
                }
        
        # Log analysis
        logger.info(f"Total operations: {analysis['total_operations']}")
        logger.info(f"Successful operations: {analysis['successful_operations']} ({analysis['successful_operations']/analysis['total_operations']*100:.2f}%)")
        logger.info(f"Failed operations: {analysis['failed_operations']} ({analysis['failed_operations']/analysis['total_operations']*100:.2f}%)")
        
        for op_type, stats in analysis["operation_types"].items():
            logger.info(f"{op_type} operations: {stats['total']}")
            logger.info(f"  Success rate: {stats['success_rate']*100:.2f}%")
            logger.info(f"  Average latency: {stats['avg_latency']*1000:.2f} ms")
            logger.info(f"  Min/Max latency: {stats['min_latency']*1000:.2f}/{stats['max_latency']*1000:.2f} ms")
        
        return analysis
    
    def plot_results(self, output_dir=None):
        """Generate plots for the test results."""
        if not self.results:
            logger.warning("No results to plot")
            return
        
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Group results by operation type
        op_types = ["PUT", "GET", "DELETE"]
        results_by_type = {op: [r for r in self.results if r.operation_type == op and r.success] for op in op_types}
        
        # Plot latency distributions
        plt.figure(figsize=(10, 6))
        
        for op_type, results in results_by_type.items():
            if results:
                latencies = [r.duration * 1000 for r in results]  # Convert to ms
                plt.hist(latencies, bins=30, alpha=0.5, label=op_type)
        
        plt.xlabel('Latency (ms)')
        plt.ylabel('Count')
        plt.title('Operation Latency Distribution')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, f"latency_distribution_{timestamp}.png"))
        logger.info(f"Saved latency distribution plot to {output_dir}/latency_distribution_{timestamp}.png")
        
        # Plot success rates
        success_rates = {}
        for op_type in op_types:
            op_results = [r for r in self.results if r.operation_type == op_type]
            if op_results:
                success_rates[op_type] = sum(1 for r in op_results if r.success) / len(op_results)
        
        if success_rates:
            plt.figure(figsize=(8, 5))
            bars = plt.bar(success_rates.keys(), [rate * 100 for rate in success_rates.values()])
            
            # Add percentage labels
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{height:.1f}%', ha='center', va='bottom')
            
            plt.ylim(0, 105)  # Give some space for the labels
            plt.ylabel('Success Rate (%)')
            plt.title('Operation Success Rates')
            plt.grid(axis='y')
            plt.savefig(os.path.join(output_dir, f"success_rates_{timestamp}.png"))
            logger.info(f"Saved success rates plot to {output_dir}/success_rates_{timestamp}.png")
    
    def run_weak_scaling_test(self, starting_ops=100, scaling_factor=2, num_steps=5):
        """
        Run a weak scaling test that increases the load progressively.
        
        Args:
            starting_ops: Number of operations to start with
            scaling_factor: Factor by which to increase operations in each step
            num_steps: Number of scaling steps to perform
            
        Returns:
            Dictionary with test results
        """
        logger.info(f"Starting weak scaling test with {starting_ops} initial operations, scaling by {scaling_factor}x over {num_steps} steps")
        
        scaling_results = {}
        
        for step in range(num_steps):
            ops_count = starting_ops * (scaling_factor ** step)
            threads = 2 ** step  # Scale threads along with operations
            ops_per_thread = ops_count // threads
            
            logger.info(f"Step {step+1}/{num_steps}: {ops_count} operations with {threads} threads ({ops_per_thread} ops/thread)")
            
            start_time = time.time()
            step_results = self.run_parallel_workload(ops_per_thread, threads)
            end_time = time.time()
            
            total_duration = end_time - start_time
            operations_per_second = ops_count / total_duration if total_duration > 0 else 0
            
            # Calculate stats for this step
            successful_ops = sum(1 for r in step_results if r.success)
            success_rate = successful_ops / len(step_results) if step_results else 0
            avg_latency = sum(r.duration for r in step_results if r.success) / successful_ops if successful_ops else 0
            
            scaling_results[step] = {
                "operations": ops_count,
                "threads": threads,
                "ops_per_thread": ops_per_thread,
                "total_duration": total_duration,
                "operations_per_second": operations_per_second,
                "success_rate": success_rate,
                "avg_latency": avg_latency
            }
            
            logger.info(f"Step {step+1} completed in {total_duration:.2f} seconds")
            logger.info(f"  Throughput: {operations_per_second:.2f} ops/sec")
            logger.info(f"  Success rate: {success_rate*100:.2f}%")
            logger.info(f"  Average latency: {avg_latency*1000:.2f} ms")
            
            # Give the system some time to recover between steps
            time.sleep(2)
        
        # Plot scaling results
        self._plot_scaling_results(scaling_results)
        
        return scaling_results
    
    def _plot_scaling_results(self, scaling_results):
        """Plot the results of the scaling test."""
        if not scaling_results:
            return
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract data
        steps = list(scaling_results.keys())
        operations = [scaling_results[step]["operations"] for step in steps]
        throughput = [scaling_results[step]["operations_per_second"] for step in steps]
        latency = [scaling_results[step]["avg_latency"] * 1000 for step in steps]  # Convert to ms
        
        # Plot throughput and latency as operations increase
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        color = 'tab:blue'
        ax1.set_xlabel('Operations')
        ax1.set_ylabel('Throughput (ops/sec)', color=color)
        ax1.plot(operations, throughput, 'o-', color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('Average Latency (ms)', color=color)
        ax2.plot(operations, latency, 's-', color=color)
        ax2.tick_params(axis='y', labelcolor=color)
        
        fig.tight_layout()
        plt.title('Weak Scaling: Throughput and Latency vs. Operations')
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, f"weak_scaling_{timestamp}.png"))
        logger.info(f"Saved weak scaling plot to {output_dir}/weak_scaling_{timestamp}.png")

def main():
    parser = argparse.ArgumentParser(description="Load Testing for Distributed Key-Value Store")
    parser.add_argument("--clients", type=int, default=5, help="Number of client connections to use")
    parser.add_argument("--starting-ops", type=int, default=100, help="Starting number of operations")
    parser.add_argument("--scaling-factor", type=int, default=2, help="Factor to scale operations by at each step")
    parser.add_argument("--steps", type=int, default=5, help="Number of scaling steps")
    args = parser.parse_args()
    
    logger.info("Starting load test with configuration:")
    logger.info(f"  Clients: {args.clients}")
    logger.info(f"  Starting operations: {args.starting_ops}")
    logger.info(f"  Scaling factor: {args.scaling_factor}")
    logger.info(f"  Steps: {args.steps}")
    
    tester = LoadTester(num_clients=args.clients)
    
    try:
        scaling_results = tester.run_weak_scaling_test(
            starting_ops=args.starting_ops,
            scaling_factor=args.scaling_factor,
            num_steps=args.steps
        )
        
        tester.analyze_results()
        tester.plot_results()
        
        logger.info("Load test completed successfully")
    except KeyboardInterrupt:
        logger.info("Load test interrupted by user")
    except Exception as e:
        logger.error(f"Load test failed: {e}", exc_info=True)

if __name__ == "__main__":
    main() 
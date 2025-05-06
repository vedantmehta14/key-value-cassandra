import sys
import os
import time
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from load_test import LoadTester, setup_logging
from utils.config import get_config

logger = setup_logging()

def run_work_stealing_test():
    """Run a test to verify work stealing functionality."""
    logger.info("Starting work stealing load test")
    
    # Create load tester with multiple clients
    load_tester = LoadTester(num_clients=10)
    
    # Base values for scaling
    base_operations = 1000
    base_threads = 5
    scaling_factor = 1.4
    
    # Generate 8 test scenarios with increasing load
    scenarios = []
    for step in range(8):
        scale = scaling_factor ** step
        scenarios.append({
            "name": f"Load Step {step + 1}",
            "operations_per_thread": int(base_operations * scale),
            "num_threads": int(base_threads * scale),
            "target_server": step % 3,  # Rotate between servers 0, 1, and 2
            "delay": max(0.01, 0.05 / scale)  # Decrease delay as load increases
        })
    
    all_results = []
    
    for scenario in scenarios:
        logger.info(f"\nRunning scenario: {scenario['name']}")
        logger.info(f"Operations per thread: {scenario['operations_per_thread']}")
        logger.info(f"Number of threads: {scenario['num_threads']}")
        logger.info(f"Target server: {scenario['target_server']}")
        logger.info(f"Delay: {scenario['delay']}")
        
        # If targeting a specific server, modify client connections
        if scenario['target_server'] is not None:
            server = get_config().get_server_by_id(scenario['target_server'])
            server_address = f"{server['ip']}:{server['port']}"
            # Create new clients all pointing to the target server
            load_tester.clients = [load_tester._get_client().__class__(server_address) for _ in range(10)]
        
        # Run the workload with the specified delay
        results = load_tester.run_parallel_workload(
            scenario['operations_per_thread'],
            scenario['num_threads']
        )
        
        # Analyze results
        analysis = load_tester.analyze_results()
        all_results.append({
            'scenario': scenario['name'],
            'analysis': analysis,
            'load_factor': scaling_factor ** (int(scenario['name'].split()[-1]) - 1)
        })
        
        # Plot results for this scenario
        load_tester.plot_results()
        
        # Wait between scenarios to let the system stabilize
        time.sleep(10)
    
    # Print summary of all scenarios
    logger.info("\nTest Summary:")
    for result in all_results:
        logger.info(f"\nScenario: {result['scenario']}")
        logger.info(f"Load Factor: {result['load_factor']:.2f}x")
        logger.info(f"Total Operations: {result['analysis']['total_operations']}")
        logger.info(f"Success Rate: {result['analysis']['successful_operations'] / result['analysis']['total_operations'] * 100:.2f}%")
        
        for op_type, stats in result['analysis']['operation_types'].items():
            logger.info(f"\n{op_type} Operations:")
            logger.info(f"  Total: {stats['total']}")
            logger.info(f"  Success Rate: {stats['successful'] / stats['total'] * 100:.2f}%")
            logger.info(f"  Average Latency: {stats['avg_latency'] * 1000:.2f}ms")
    
    # Check server logs for work stealing
    logger.info("\nChecking server logs for work stealing activity...")
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    
    for server_id in range(get_config().cluster_size):
        log_file = os.path.join(logs_dir, f"server_{server_id}.log")
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_content = f.read()
                steal_count = log_content.count("Stole message from server")
                logger.info(f"Server {server_id} stole work {steal_count} times")
                
                # Look for specific patterns
                if "queue_length" in log_content:
                    logger.info(f"Server {server_id} participated in work stealing")
                if "cpu_utilization" in log_content:
                    logger.info(f"Server {server_id} reported CPU utilization")

if __name__ == "__main__":
    run_work_stealing_test() 
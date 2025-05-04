# Load Testing for Distributed Key-Value Store

This directory contains tools for load testing the distributed key-value store, with a focus on analyzing weak scaling capabilities.

## Prerequisites

Ensure you have installed all required dependencies:

```bash
pip install -r ../requirements.txt
```

Also, make sure that your server nodes are up and running before executing the tests. The load tester will use the configuration in the `config` directory to connect to the servers.

## Running Load Tests

### Using the Command Line

You can run the load tests directly using Python:

```bash
python load_test.py --clients 5 --starting-ops 100 --scaling-factor 2 --steps 5
```

Available parameters:

- `--clients`: Number of client connections to use (default: 5)
- `--starting-ops`: Initial number of operations for the first step (default: 100)
- `--scaling-factor`: Factor by which to increase operations at each step (default: 2)
- `--steps`: Number of scaling steps to perform (default: 5)

### Using the Shell Script

For convenience, we've also provided a shell script that can be used to run the tests:

```bash
../scripts/run_load_test.sh -c 5 -o 100 -f 2 -s 5
```

Where:
- `-c`: Number of client connections (default: 5)
- `-o`: Starting number of operations (default: 100)
- `-f`: Scaling factor for each step (default: 2)
- `-s`: Number of scaling steps (default: 5)

Use `-h` for help:

```bash
../scripts/run_load_test.sh -h
```

## Test Methodology

The weak scaling test increases the load on the system progressively, measuring how well the system scales under increasing demand. At each step:

1. The number of operations increases by the scaling factor
2. The number of threads increases along with the operations
3. Operations per thread remain roughly constant

This helps determine if the system maintains consistent performance as load increases.

The test performs a mixture of operations:
- 20% PUT operations
- 70% GET operations
- 10% DELETE operations

## Results and Analysis

All test results are logged to the `logs` directory:

- Detailed logs in `load_test_TIMESTAMP.log` 
- Performance plots:
  - `latency_distribution_TIMESTAMP.png`: Distribution of latencies by operation type
  - `success_rates_TIMESTAMP.png`: Success rates by operation type
  - `weak_scaling_TIMESTAMP.png`: Throughput and latency as operations increase

### Analyzing Weak Scaling

In the weak scaling plot, look for:

1. **Throughput scalability**: The blue line should ideally increase linearly with the number of operations, indicating that the system can handle more operations per second as load increases.

2. **Latency stability**: The red line should ideally remain flat or increase only slightly as operations increase, indicating that the system maintains responsive performance even under high load.

3. **Where the system breaks**: If the throughput line flattens or starts to decrease while latency sharply increases, this is the point where the system is reaching its capacity limits.

## Customizing Tests

Feel free to modify the `load_test.py` script to customize the test parameters or to implement additional test scenarios. The core `LoadTester` class can be extended to support different test methodologies. 
#!/bin/bash

# Generate Python code from proto file
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. keyvalue.proto

echo "Generated gRPC code from keyvalue.proto" 
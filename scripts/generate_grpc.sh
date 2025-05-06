# AI generated
#!/bin/bash

# Set base directory to the project root
cd "$(dirname "$0")/.."

# Generate Python code from proto file
python3 -m grpc_tools.protoc -I./src/proto --python_out=./src/proto --grpc_python_out=./src/proto ./src/proto/keyvalue.proto

# Move the generated files to the right place (protoc can create nested directories)
mv src/proto/src/proto/keyvalue_pb2*.py src/proto/ 2>/dev/null || true
rmdir src/proto/src/proto src/proto/src 2>/dev/null || true

echo "Generated gRPC code from keyvalue.proto" 
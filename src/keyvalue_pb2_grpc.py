# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import keyvalue_pb2 as keyvalue__pb2

GRPC_GENERATED_VERSION = '1.71.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in keyvalue_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class KeyValueServiceStub(object):
    """Service for client-server communication
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Get = channel.unary_unary(
                '/keyvaluestore.KeyValueService/Get',
                request_serializer=keyvalue__pb2.GetRequest.SerializeToString,
                response_deserializer=keyvalue__pb2.GetResponse.FromString,
                _registered_method=True)
        self.Put = channel.unary_unary(
                '/keyvaluestore.KeyValueService/Put',
                request_serializer=keyvalue__pb2.PutRequest.SerializeToString,
                response_deserializer=keyvalue__pb2.PutResponse.FromString,
                _registered_method=True)
        self.Delete = channel.unary_unary(
                '/keyvaluestore.KeyValueService/Delete',
                request_serializer=keyvalue__pb2.DeleteRequest.SerializeToString,
                response_deserializer=keyvalue__pb2.DeleteResponse.FromString,
                _registered_method=True)
        self.GetAllKeys = channel.unary_unary(
                '/keyvaluestore.KeyValueService/GetAllKeys',
                request_serializer=keyvalue__pb2.GetAllKeysRequest.SerializeToString,
                response_deserializer=keyvalue__pb2.GetAllKeysResponse.FromString,
                _registered_method=True)


class KeyValueServiceServicer(object):
    """Service for client-server communication
    """

    def Get(self, request, context):
        """Read a value by key
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Put(self, request, context):
        """Write a key-value pair
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Delete(self, request, context):
        """Delete a key
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAllKeys(self, request, context):
        """Get all keys (for debugging)
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_KeyValueServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Get': grpc.unary_unary_rpc_method_handler(
                    servicer.Get,
                    request_deserializer=keyvalue__pb2.GetRequest.FromString,
                    response_serializer=keyvalue__pb2.GetResponse.SerializeToString,
            ),
            'Put': grpc.unary_unary_rpc_method_handler(
                    servicer.Put,
                    request_deserializer=keyvalue__pb2.PutRequest.FromString,
                    response_serializer=keyvalue__pb2.PutResponse.SerializeToString,
            ),
            'Delete': grpc.unary_unary_rpc_method_handler(
                    servicer.Delete,
                    request_deserializer=keyvalue__pb2.DeleteRequest.FromString,
                    response_serializer=keyvalue__pb2.DeleteResponse.SerializeToString,
            ),
            'GetAllKeys': grpc.unary_unary_rpc_method_handler(
                    servicer.GetAllKeys,
                    request_deserializer=keyvalue__pb2.GetAllKeysRequest.FromString,
                    response_serializer=keyvalue__pb2.GetAllKeysResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'keyvaluestore.KeyValueService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('keyvaluestore.KeyValueService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class KeyValueService(object):
    """Service for client-server communication
    """

    @staticmethod
    def Get(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/keyvaluestore.KeyValueService/Get',
            keyvalue__pb2.GetRequest.SerializeToString,
            keyvalue__pb2.GetResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Put(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/keyvaluestore.KeyValueService/Put',
            keyvalue__pb2.PutRequest.SerializeToString,
            keyvalue__pb2.PutResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Delete(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/keyvaluestore.KeyValueService/Delete',
            keyvalue__pb2.DeleteRequest.SerializeToString,
            keyvalue__pb2.DeleteResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetAllKeys(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/keyvaluestore.KeyValueService/GetAllKeys',
            keyvalue__pb2.GetAllKeysRequest.SerializeToString,
            keyvalue__pb2.GetAllKeysResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)


class InternalServiceStub(object):
    """Service for internal server-to-server communication
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ReplicateWrite = channel.unary_unary(
                '/keyvaluestore.InternalService/ReplicateWrite',
                request_serializer=keyvalue__pb2.ReplicateWriteRequest.SerializeToString,
                response_deserializer=keyvalue__pb2.ReplicateWriteResponse.FromString,
                _registered_method=True)
        self.ForwardRead = channel.unary_unary(
                '/keyvaluestore.InternalService/ForwardRead',
                request_serializer=keyvalue__pb2.ForwardReadRequest.SerializeToString,
                response_deserializer=keyvalue__pb2.ForwardReadResponse.FromString,
                _registered_method=True)
        self.Heartbeat = channel.unary_unary(
                '/keyvaluestore.InternalService/Heartbeat',
                request_serializer=keyvalue__pb2.HeartbeatRequest.SerializeToString,
                response_deserializer=keyvalue__pb2.HeartbeatResponse.FromString,
                _registered_method=True)
        self.RequestWorkSteal = channel.unary_unary(
                '/keyvaluestore.InternalService/RequestWorkSteal',
                request_serializer=keyvalue__pb2.WorkStealRequest.SerializeToString,
                response_deserializer=keyvalue__pb2.WorkStealResponse.FromString,
                _registered_method=True)
        self.GetServerStatus = channel.unary_unary(
                '/keyvaluestore.InternalService/GetServerStatus',
                request_serializer=keyvalue__pb2.ServerStatusRequest.SerializeToString,
                response_deserializer=keyvalue__pb2.ServerStatusResponse.FromString,
                _registered_method=True)


class InternalServiceServicer(object):
    """Service for internal server-to-server communication
    """

    def ReplicateWrite(self, request, context):
        """Replicate a write to another server
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ForwardRead(self, request, context):
        """Forward a read to another server
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Heartbeat(self, request, context):
        """Send heartbeat with rank information
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RequestWorkSteal(self, request, context):
        """Request work stealing from another server
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetServerStatus(self, request, context):
        """Get server status for work stealing
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_InternalServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ReplicateWrite': grpc.unary_unary_rpc_method_handler(
                    servicer.ReplicateWrite,
                    request_deserializer=keyvalue__pb2.ReplicateWriteRequest.FromString,
                    response_serializer=keyvalue__pb2.ReplicateWriteResponse.SerializeToString,
            ),
            'ForwardRead': grpc.unary_unary_rpc_method_handler(
                    servicer.ForwardRead,
                    request_deserializer=keyvalue__pb2.ForwardReadRequest.FromString,
                    response_serializer=keyvalue__pb2.ForwardReadResponse.SerializeToString,
            ),
            'Heartbeat': grpc.unary_unary_rpc_method_handler(
                    servicer.Heartbeat,
                    request_deserializer=keyvalue__pb2.HeartbeatRequest.FromString,
                    response_serializer=keyvalue__pb2.HeartbeatResponse.SerializeToString,
            ),
            'RequestWorkSteal': grpc.unary_unary_rpc_method_handler(
                    servicer.RequestWorkSteal,
                    request_deserializer=keyvalue__pb2.WorkStealRequest.FromString,
                    response_serializer=keyvalue__pb2.WorkStealResponse.SerializeToString,
            ),
            'GetServerStatus': grpc.unary_unary_rpc_method_handler(
                    servicer.GetServerStatus,
                    request_deserializer=keyvalue__pb2.ServerStatusRequest.FromString,
                    response_serializer=keyvalue__pb2.ServerStatusResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'keyvaluestore.InternalService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('keyvaluestore.InternalService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class InternalService(object):
    """Service for internal server-to-server communication
    """

    @staticmethod
    def ReplicateWrite(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/keyvaluestore.InternalService/ReplicateWrite',
            keyvalue__pb2.ReplicateWriteRequest.SerializeToString,
            keyvalue__pb2.ReplicateWriteResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def ForwardRead(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/keyvaluestore.InternalService/ForwardRead',
            keyvalue__pb2.ForwardReadRequest.SerializeToString,
            keyvalue__pb2.ForwardReadResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Heartbeat(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/keyvaluestore.InternalService/Heartbeat',
            keyvalue__pb2.HeartbeatRequest.SerializeToString,
            keyvalue__pb2.HeartbeatResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def RequestWorkSteal(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/keyvaluestore.InternalService/RequestWorkSteal',
            keyvalue__pb2.WorkStealRequest.SerializeToString,
            keyvalue__pb2.WorkStealResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetServerStatus(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/keyvaluestore.InternalService/GetServerStatus',
            keyvalue__pb2.ServerStatusRequest.SerializeToString,
            keyvalue__pb2.ServerStatusResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

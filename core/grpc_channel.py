"""
Encapsulates classes and handlers needed for setting up and disposing gRPC channels cleanly.
"""

import atexit
import logging
import os
from weakreflist import WeakList

from grpc import insecure_channel
from tensorflow_serving.apis.prediction_service_pb2 import PredictionServiceStub

from tf_serving_flask_app import settings


logger = logging.getLogger('core')

# Global list of weak references to managed channels that are disposed off cleanly on exit.
# We intentionally use weak references to ensure ManagedChannel objects can be naturally
# garbage collected.
_managed_channel_refs = WeakList()


class ManagedChannel:
    """Wraps and provides proper disposal of a (gRPC channel, prediction service stub) pair."""
    def __init__(self):
        self.channel = None
        self.stub = None
        self.connect()

    def connect(self):
        """Creates an insecure channel to a TensorFlow gRPC model server and then binds
        a prediction service stub on that channel.

        The hostname and port of the remote gRPC server are provided as environment
        variables.

        We add a weak reference to the managed pair to a global pool for proper cleanup.
        """
        server_name = os.getenv(
            'TF_SERVER_NAME',
            settings.DEFAULT_TF_SERVER_NAME)
        server_port = os.getenv(
            'TF_SERVER_PORT',
            settings.DEFAULT_TF_SERVER_PORT)

        if server_name and server_port:
            self.channel = insecure_channel('%s:%s' % (server_name, server_port))
            self.stub = PredictionServiceStub(self.channel)
            _managed_channel_refs.append(self)

    def shutdown(self):
        """Deletes the (gRPC channel, prediction service stub) pair."""
        del self.channel
        del self.stub


def exit_handler():
    """atexit handler that guarantees that the global managed channel is properly disposed off."""
    global _managed_channel_refs
    num_disposed_channels = 0
    for managed_channel in _managed_channel_refs:
        if managed_channel:
            managed_channel.shutdown()
            del managed_channel
            num_disposed_channels += 1
    if num_disposed_channels > 0:
        logger.info('Successfully disposed %d gRPC channels' % num_disposed_channels)

atexit.register(exit_handler)

"""Defines the lifecycle of a prediction."""

import logging
import os
from typing import Any, Dict

from grpc import RpcError
import tensorflow as tf
from tensorflow_serving.apis.predict_pb2 import PredictRequest, PredictResponse

from tf_serving_flask_app import settings
from tf_serving_flask_app.base.exceptions import PredictionRpcError, PreprocessorError, PostprocessorError
from tf_serving_flask_app.base.metaclasses import Singleton
from tf_serving_flask_app.core.grpc_channel import ManagedChannel
from tf_serving_flask_app.core import metrics
from tf_serving_flask_app.core.spec_borg import SpecBorg

logger = logging.getLogger('core')

PredictionInput = Dict[str, Any]


class PredictionFlow(metaclass=Singleton):
    """A prediction flow is a callable class composed of three instrumented stages:

    - Pre-processing request inputs into tensor protocol buffers.
    - Making the gRPC network call with tensors marshaled into gRPC requests.
    - Running the post-processor on output tensors and marshaling the output
      response.
    """
    def __init__(self, prediction_rpc_timeout_secs):
        self.spec_borg = None
        self.prediction_rpc_timeout_secs = prediction_rpc_timeout_secs

    def _initialize_spec(self):
        self.spec_borg = SpecBorg()

    def _populate_model_attributes(self, request: PredictRequest):
        """Populates the prediction request with model specific attributes
        like the name, version and signature.
        """
        assert self.spec_borg

        model_spec = self.spec_borg.model_spec
        request.model_spec.name = model_spec.name
        if model_spec.version > 0:
            request.model_spec.version.value = model_spec.version
        if model_spec.signature_name:
            request.model_spec.signature_name = model_spec.signature_name
        logger.debug(
            'Populated request with model attributes - name: `%s`, version: `%d`, signature_name: `%s`',
            model_spec.name, model_spec.version, model_spec.signature_name)

    @metrics.histogram(
        'preprocessor_request_duration_seconds',
        'Pre-processor request duration in seconds',
    )
    def _preprocess_input(self,
                          prediction_input: PredictionInput,
                          prediction_rpc_request: PredictRequest):
        """Populates the prediction request with pre-processed input.

        :param prediction_input: Maps input keys to extracted flask request data.
        :param prediction_rpc_request: Prediction RPC request that is populated
        with the tensor derived from `prediction_input`.

        :raises PreprocessorError if there was a failure running the spec
        specified pre-processor or for a TypeError or ValueError thrown while
        converting the pre-processed numpy array into a tensor proto.
        """
        assert self.spec_borg

        for (input_key, input_data) in prediction_input.items():
            # The REST API request endpoint will die early with a bad request
            # error if specified input keys in the spec are not present. We
            # asssume this as a precondition.
            assert input_key in self.spec_borg.input_preprocessors

            preprocessor = self.spec_borg.input_preprocessors[input_key]
            # Raises PreprocessorError for any failure.
            ndarray = preprocessor.preprocess(input_data)
            logger.debug('Pre-processed input into a numpy array of shape `%s`',
                         ndarray.shape)

            try:
                features_tensor_proto = tf.contrib.util.make_tensor_proto(ndarray)
            except (TypeError, ValueError) as e:
                raise PreprocessorError(e)

            prediction_rpc_request.inputs[input_key].CopyFrom(features_tensor_proto)
            logger.debug(
                'Populated the prediction RPC request input keyed by `%s` '
                'with a feature tensor of shape `%s` and dtype `%s`',
                input_key,
                features_tensor_proto.tensor_shape,
                features_tensor_proto.dtype)

    @metrics.histogram(
        'model_prediction_duration_seconds',
        'Model prediction duration in seconds',
    )
    def _make_prediction_rpc(self, request: PredictRequest):
        """ Makes the actual gRPC for predictions.

        :param request: a populated prediction request protocol buffer
        :return: the gRPC response protocol buffer
        """
        managed_channel = ManagedChannel()
        logger.debug('Making a synchronous gRPC call for the prediction')
        try:
            response = managed_channel.stub.Predict(
                request,
                timeout=self.prediction_rpc_timeout_secs)
        except RpcError as e:
            status_code = e.code()
            logger.error('Received a gRPC error with status code `%s`, status value `%s` and '
                         'details `%s`', status_code.name, status_code.value, e.details())
            raise PredictionRpcError(e)
        logger.debug('Successfully made the gRPC call')
        return response

    @metrics.histogram(
        'postprocessor_request_duration_seconds',
        'Post-processor request duration in seconds',
    )
    def _postprocess_response(self, response: PredictResponse):
        """Post-processes the response into output meant to be serialized by REST.

        :param response: a prediction response protocol buffer
        :return: a python dict from the output key specified in the spec
        to the post-processed result for that output key.

        :raises PostprocessorError for a failure in any of:
        - looking up the output signature key in the response
        - converting the output tensor to a numpy array
        - running the post-processor function over the numpy array
        """
        assert self.spec_borg
        final_response = {}
        for (output_key, output_postprocessor) in self.spec_borg.output_postprocessors.items():
            try:
                output_tensor = response.outputs[output_key]
            except KeyError as e:
                raise PostprocessorError(e)

            logger.debug('Received output tensor keyed by `%s`of shape `%s` and dtype `%s`',
                         output_key,
                         output_tensor.tensor_shape,
                         output_tensor.dtype)

            try:
                output_ndarray = tf.contrib.util.make_ndarray(output_tensor)
            except TypeError as e:
                raise PostprocessorError(e)

            logger.debug('Converted the output tensor into a numpy array of shape `%s`',
                         output_ndarray.shape)

            # Raises a PostprocessorError.
            final_response[output_key] = output_postprocessor.postprocess(output_ndarray)
            logger.debug('Successfully ran the post-processor over the output numpy array for key `%s`', output_key)

        return final_response

    def _model_postprocess(self, output_dict):
        """
        Post-processes the response into output meant to be serialized by REST.

        :param output_dict: a python dict from the output key specified in the spec
        to the post-processed result for that output key.

        :raises PostprocessorError for a failure in any of:
        - running the post-processor function over the dictionary of output signature key and its numpy array outputs
        """
        final_response = self.spec_borg.postprocessor.postprocess(output_dict)
        return final_response

    def __call__(self, prediction_input: PredictionInput):
        """Makes a prediction on extracted flask request input and
        returns an output dict to be serialized through REST.

        :raises:
        - a PreprocessorError for a failure converting `prediction_input` into
        tensors for transport.
        - a PredictionRpcError for a failure with the RPC.
        - a PostprocessorError for a failure post-processing the RPC response into
        a dict that is then serialized.
        """
        self._initialize_spec()
        prediction_rpc_request = PredictRequest()
        self._populate_model_attributes(prediction_rpc_request)
        self._preprocess_input(prediction_input, prediction_rpc_request)
        response = self._make_prediction_rpc(prediction_rpc_request)
        response = self._postprocess_response(response)
        return self._model_postprocess(response)


def create_prediction_flow():
    """Factory method that returns a singleton instance of the prediction flow."""
    prediction_rpc_timeout_secs = int(os.getenv(
        'PREDICTION_RPC_TIMEOUT_SECS',
        settings.DEFAULT_PREDICTION_RPC_TIMEOUT_SECS))
    return PredictionFlow(prediction_rpc_timeout_secs)

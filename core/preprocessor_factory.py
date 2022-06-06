"""
Defines a factory method for instantiating pre-processor functions and
callable classes.
"""

import logging

from spec.proto.input_pb2 import Input
from tf_serving_flask_app.core import file_preprocessor, \
    image_preprocessor, \
    text_preprocessor
from tf_serving_flask_app.base.dynamic_imports import identity, \
    import_function_or_identity, \
    import_callable_class_or_identity, \
    name, safe_eval_lambda

logger = logging.getLogger('core')

valid_inputs = [
    Input.FILE,
    Input.IMAGE,
    Input.TEXT
]
valid_inputs = dict((i, 0) for i in valid_inputs)


def get_preprocessor(input_specification, data_format):
    """Factory method that returns a pre-processor specific to the type
    mentioned in the input specification.

    :param input_specification: A input_pb2.Input that describes how input
    should be pre-processed.

    :param data_format: A DataFormat enumeration that describes the axis used
    for channels.

    For 2D data (e.g. image), CHANNELS_LAST assumes (height, width, channels) while
    CHANNELS_FIRST assumes  (channels, height, width).

    For 3D data, CHANNELS_LAST assumes (conv_dim1, conv_dim2, conv_dim3, channels)
    while CHANNELS_FIRST assumes (channels, conv_dim1, conv_dim2, conv_dim3).

    https://github.com/faif/python-patterns/blob/master/creational/factory_method.py
    """
    if input_specification.type not in valid_inputs:
        raise NotImplementedError

    if input_specification.HasField('preprocessor_function'):
        logger.debug('Attempting to import pre-processor function "%s"' %
                     input_specification.preprocessor_function)
        preprocessor_function = import_function_or_identity(
            input_specification.preprocessor_function)
    elif input_specification.HasField('preprocessor_class'):
        logger.debug('Attempting to import pre-processor callable class "%s"' %
                     input_specification.preprocessor_class)
        preprocessor_function = import_callable_class_or_identity(
            input_specification.preprocessor_class)
    elif input_specification.HasField('preprocessor_lambda'):
        logger.debug('Attempting to import pre-processor lambda function "%s"' %
                     input_specification.preprocessor_lambda)
        preprocessor_function = safe_eval_lambda(input_specification.preprocessor_lambda)
    else:
        logger.debug('Explicit pre-processor not specified and using the identity function')
        preprocessor_function = identity

    preprocessor_name = name(preprocessor_function)

    if input_specification.type == Input.IMAGE:
        logger.debug('Instantiating an image pre-processor wrapping "%s"' %
                     preprocessor_name)
        return image_preprocessor.ImagePreprocessor(
            input_specification.dtype,
            input_specification.shape,
            input_specification.image,
            preprocessor_function,
            data_format)

    if input_specification.type == Input.FILE:
        logger.debug('Instantiating a file pre-processor wrapping "%s"' %
                     preprocessor_name)
        return file_preprocessor.FilePreprocessor(preprocessor_function)

    if input_specification.type == Input.TEXT:
        logger.debug('Instantiating a text pre-processor wrapping "%s"' %
                     preprocessor_name)
        return text_preprocessor.TextPreprocessor(preprocessor_function)

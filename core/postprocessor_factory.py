"""
Defines a factory method for instantiating post-processor functions and callable classes.
"""

import logging

from tf_serving_flask_app.core import postprocessor
from tf_serving_flask_app.base.dynamic_imports import identity, \
    import_function_or_identity, \
    import_callable_class_or_identity, \
    name

logger = logging.getLogger('core')


def get_postprocessor(output_specification):
    """Factory method that returns a post-processor specific to the type
    mentioned in the output specification.

    :param output_specification: An output_pb2.Output that describes how
    the prediction response should be post-processed.

    https://github.com/faif/python-patterns/blob/master/creational/factory_method.py
    """
    if output_specification.HasField('postprocessor_function'):
        logger.debug('Attempting to import post-processor function "%s"' %
                     output_specification.postprocessor_function)
        postprocessor_function = import_function_or_identity(
            output_specification.postprocessor_function)
    elif output_specification.HasField('postprocessor_class'):
        logger.debug('Attempting to import post-processor callable class "%s"' %
                     output_specification.postprocessor_class)
        postprocessor_function = import_callable_class_or_identity(
            output_specification.postprocessor_class)
    elif output_specification.HasField('postprocessor_lambda'):
        logger.debug('Attempting to import postprocessor lambda function "%s"' %
                     output_specification.postprocessor_lambda)
        postprocessor_function = safe_eval_lambda(output_specification.postprocessor_lambda)
    else:
        logger.debug('Explicit post-processor not specified and using the identity function')
        postprocessor_function = identity

    postprocessor_name = name(postprocessor_function)

    logger.debug('Instantiating a post-processor wrapping "%s"' %
                 postprocessor_name)
    return postprocessor.PassthroughPostprocessor(postprocessor_function)

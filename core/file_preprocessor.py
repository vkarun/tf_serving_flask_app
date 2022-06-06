"""
Defines a wrapper class for a pre-processor that takes a file pointer
as input.
"""

from typing import BinaryIO, Callable, TextIO, Union

from tf_serving_flask_app.core.preprocessor import AbstractPreprocessor


class FilePreprocessor(AbstractPreprocessor):
    """Wraps a dynamically imported pre-processing function
    that expects a file pointer as input and returns a numpy
    array.
    """

    def __init__(self, preprocessor_function: Callable):
        """
        :param preprocessor_function: A validated pre-processor function that
        is expected to return a numpy array.
        """
        self.preprocessor_function = preprocessor_function

    def preprocess_impl(self, fp: Union[BinaryIO, TextIO]):
        return self.preprocessor_function(fp)

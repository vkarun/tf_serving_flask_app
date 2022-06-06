"""
Defines a wrapper class for a pre-processor that takes text input.
"""

from typing import Callable

from tf_serving_flask_app.core.preprocessor import AbstractPreprocessor


class TextPreprocessor(AbstractPreprocessor):
    """Wraps a dynamically imported pre-processing function
    that expects text input and returns a numpy array.
    """

    def __init__(self, preprocessor_function: Callable):
        """
        :param preprocessor_function: A validated pre-processor function that
        is expected to return a numpy array.
        """
        self.preprocessor_function = preprocessor_function

    def preprocess_impl(self, text: str):
        return self.preprocessor_function(text)

"""
Defines the abstract base class for pre-processors.
"""

from abc import ABCMeta, abstractmethod
from typing import Any

from tf_serving_flask_app.base.exceptions import PreprocessorError


class AbstractPreprocessor(metaclass=ABCMeta):
    def preprocess(self, input_data: Any):
        """Safely wraps an abstract pre-processor implementation.

        :raises PreprocessorError for any exception thrown during
        pre-processing by concrete subclasses.
        """
        try:
            return self.preprocess_impl(input_data)
        except Exception as e:
            raise PreprocessorError(e)

    @abstractmethod
    def preprocess_impl(self, input_data: Any):
        pass


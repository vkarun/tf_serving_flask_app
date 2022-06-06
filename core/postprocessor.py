from abc import ABCMeta, abstractmethod

from tf_serving_flask_app.base.exceptions import PostprocessorError


class AbstractPostprocessor(metaclass=ABCMeta):
    def postprocess(self, response):
        try:
            return self.postprocess_impl(response)
        except Exception as e:
            raise PostprocessorError(e)

    @abstractmethod
    def postprocess_impl(self, response):
        pass


class PassthroughPostprocessor(AbstractPostprocessor):
    """Trivial wrapper over a dynamically imported post-processing function."""

    def __init__(self, postprocessor_function):
        """
        :param postprocessor_function: A validated post-processor function that
        we run the prediction response through before dispatching to the
        client.
        """
        self.postprocessor_function = postprocessor_function

    def postprocess_impl(self, response):
        return self.postprocessor_function(response)

import logging

from spec.reader import load_pipeline_spec_from_json
from tf_serving_flask_app.core import preprocessor_factory
from tf_serving_flask_app.core import postprocessor_factory


logger = logging.getLogger('core')


class SpecBorg(object):
    """Monostate that provides access to protocol buffers that define
    the specification and objects that derive from these protocol
    buffers.

    https://github.com/faif/python-patterns/blob/master/creational/borg.py
    """
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def initialize_from_json(self, pipeline_spec_path):
        """Initializes the shared state.

        :param pipeline_spec_path: Path to the pipeline specification.
        We expect the specification to be valid as a pre-requisite.
        """
        pipeline_spec = load_pipeline_spec_from_json(pipeline_spec_path)

        # Currently scoped only to a single model with multiple inputs and
        # outputs.
        self.model_spec = pipeline_spec.model[0]

        # assuming there will be at max one post processor at model level
        self.postprocessor = postprocessor_factory.get_postprocessor(
                self.model_spec)

        # A dict from input signature to associated specification.
        self.input_specs = {}
        # A dict from input signature to associated pre-processor functions or
        # callable classes.
        self.input_preprocessors = {}
        for input_spec in self.model_spec.input:
            input_key = input_spec.signature_def_key
            assert input_key
            self.input_specs[input_key] = input_spec
            self.input_preprocessors[input_key] = preprocessor_factory.get_preprocessor(
                input_spec, self.model_spec.data_format)

        # A dict from output signature to associated specification.
        self.output_specs = {}
        # A dict from output signature to associated post-processor functions or
        # callable classes.
        self.output_postprocessors = {}
        for output_spec in self.model_spec.output:
            output_key = output_spec.signature_def_key
            assert output_key
            self.output_specs[output_key] = output_spec
            self.output_postprocessors[output_key] = postprocessor_factory.get_postprocessor(
                output_spec)


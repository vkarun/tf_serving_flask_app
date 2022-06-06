"""
Defines a pre-processor for optimally converting an image file to a numpy array.
"""

from typing import BinaryIO, Callable, List

import numpy as np
from PIL import Image

from spec.proto.dtypes_pb2 import DataType
from spec.proto.input_pb2 import Image as ImageSpec
from spec.proto.model_pb2 import Model
from tf_serving_flask_app.core import dtypes
from tf_serving_flask_app.core.preprocessor import AbstractPreprocessor


class ImagePreprocessor(AbstractPreprocessor):
    """The image pre-processor converts an image to a numpy array."""

    def __init__(self,
                 dtype: DataType,
                 shape: List[int],
                 image_spec: ImageSpec,
                 preprocessor_function: Callable,
                 image_data_format: int):
        """
        :param dtype: The data type for the numpy array derived from the image.

        :param image_spec: Defines how the image should be re-sized and in
        what color space.

        :param shape: A repeated array which defines the expected shape of the numpy
        array before it is passed to the pre-processor function.

        :param preprocessor_function: A validated pre-processor function that we run the
        numpy array derived from the image through.

        :param image_data_format: Image data format convention to follow.
        The enum value CHANNELS_LAST assumes (height, width, channels)
        while the enum value CHANNELS_FIRST assumes  (channels, height, width).
        """
        self.image_spec = image_spec

        self.preprocessor_function = preprocessor_function

        self.numpy_dtype = dtypes.to_numpy(dtype)

        self.shape = shape

        self.image_data_format = image_data_format

    def preprocess_image(self, imagefp: BinaryIO):
        """Converts an image file to a 3D numpy array.

        - If the spec explicitly lists RGB or GRAYSCALE for the colorspace
          and the colorspace of the loaded image is not compliant,
          we convert to the right colorspace.

        - If the spec explicitly specifies a target width and target height,
          we resize the loaded image to the target dimensions.

        - The data format dictates what axis channels are stored in.

        :param imagefp: An image file object. The file object must implement
        read(), seek(), and tell() methods, and be opened in binary mode.

        :return: If the data format is CHANNELS_LAST, we return a numpy array
        with shape (height, width, channels). If the data format is
        CHANNELS_FIRST, we return a numpy array with shape
        (channels, height, width).
        """
        # Opens an image in channels last format.
        img = Image.open(imagefp)

        if self.image_spec.colorspace == ImageSpec.GRAYSCALE and img.mode != 'L':
            img = img.convert('L')

        if self.image_spec.colorspace == ImageSpec.RGB and img.mode != 'RGB':
            img = img.convert('RGB')

        if self.image_spec.target_width > 0 \
                and self.image_spec.target_height > 0:
            img = img.resize((self.image_spec.target_width,
                              self.image_spec.target_height))

        x = np.asarray(img, dtype=self.numpy_dtype)

        # We add an axis explicitly for GRAYSCALE images to
        # stay shape conformant.
        if self.image_spec.colorspace == ImageSpec.GRAYSCALE:
            x = x[:, :, np.newaxis]

        # Swap the axis representing channels if the data format
        # is channels first. Assumes all prior steps yield
        # channels last.
        if self.image_data_format == Model.CHANNELS_FIRST:
            x = np.moveaxis(x, -1, 0)

        return x

    def preprocess_impl(self, imagefp: BinaryIO):
        """Converts an image file a numpy array.

        :param imagefp: An image file object. The file object must implement
        read(), seek(), and tell() methods, and be opened in binary mode.

        :return the numpy array passed to the neural network. The number of dimensions
        of the numpy array is controlled by the shape specified in the spec:

        Pre-processor function expects a 3D array
        =========================================
        If the spec defines a 3D shape, the 3D numpy array
        obtained from resizing the image is directly passed to
        the pre-processor function.

        The shape is (height, width, channels) when the data format
        is CHANNELS_LAST.

        The shape is (channels, height, width) when the data format is
        CHANNELS_FIRST.

        Pre-processor function expects a 4D array
        =========================================
        If the spec defines a 4D shape, we expand the shape of the
        3D image array by inserting a new axis at the first
        position.

        The shape is (batch size, height, width, channels) with a
        batch of 1 when the data format is CHANNELS_LAST.

        The shape is (batch size, channels, height, width) with a
        batch of 1 when the data format is CHANNELS_FIRST.
        """
        imgarray = self.preprocess_image(imagefp)

        # Expand dimensions if the spec specifies 4D.
        if len(self.shape) > imgarray.ndim:
            imgarray = imgarray[np.newaxis, :]

        return self.preprocessor_function(imgarray)


import numpy as np

from spec.proto import dtypes_pb2


numpy_dtypes = {
    dtypes_pb2.DT_FLOAT16: np.float16,
    dtypes_pb2.DT_FLOAT32: np.float32,
    dtypes_pb2.DT_FLOAT64: np.float64,
    dtypes_pb2.DT_INT8: np.int8,
    dtypes_pb2.DT_UINT8: np.uint8,
    dtypes_pb2.DT_INT16: np.int16,
    dtypes_pb2.DT_UINT16: np.uint16,
    dtypes_pb2.DT_INT32: np.int32,
    dtypes_pb2.DT_UINT32: np.uint32,
    dtypes_pb2.DT_INT64: np.int64,
    dtypes_pb2.DT_UINT64: np.uint64,
    dtypes_pb2.DT_BOOL: np.bool,
    dtypes_pb2.DT_STRING: np.str,
    dtypes_pb2.DT_COMPLEX64: np.complex64,
    dtypes_pb2.DT_COMPLEX128: np.complex128
}


def to_numpy(dt):
    return numpy_dtypes[dt]

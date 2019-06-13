# -*- coding: utf-8 -*-

import numpy as np


def read_image(file_obj, shape, offset, dtype='uint8'):
    """Reads an image from memmap

    :param file_obj: filename or fid
    :param shape: image shape (size)
    :param offset: reading offset
    :param dtype: image dtype. uint8 by default
    :return: numpy.memmap array-like object
    """
    return np.memmap(
        file_obj,
        dtype=dtype,
        mode='r',
        shape=tuple(shape),
        offset=offset,
        order='F'
    )

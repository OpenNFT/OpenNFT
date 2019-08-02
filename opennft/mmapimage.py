# -*- coding: utf-8 -*-

import collections
import typing as t

import numpy as np

from opennft.projview import ProjectionType


def get_image_shape(image_name: str, eng, nargout: int) -> np.ndarray:
    return np.array(eng.evalin('base', 'size({})'.format(image_name), nargout=nargout), dtype=np.int32)


def read_memmap_image(file_obj, shape, offset: int, dtype: str = 'uint8'):
    return np.memmap(
        file_obj,
        dtype=dtype,
        mode='r',
        shape=tuple(shape),
        offset=offset,
        order='F'
    )


def read_mosaic_image(memmap_filename: str, image_name, eng) -> np.ndarray:
    """Reads mosaic image from memmap file

    :param memmap_filename: memmap file name
    :param image_name: name of image in matlab
    :param eng: matlab engine unstance
    :return: numpy array-like image object
    """
    shape = get_image_shape(image_name, eng, nargout=2)
    return read_memmap_image(memmap_filename, shape=shape, offset=0)


class MosaicImageReader:
    """The class for reading mosaic images from memmap file
    """

    def __init__(self, image_name: str):
        self._image = None  # type: t.Optional[np.ndarray]
        self._image_name = image_name
        self.clear()

    @property
    def image(self):
        return self._image

    def read(self, memmap_filename: str, matlab_engine):
        self._image = read_mosaic_image(memmap_filename, self._image_name, matlab_engine)

    def clear(self):
        self._image = None


class ProjectionImagesReader:
    """The class for reading projection images from memmap file
    """

    _projection_images_mapping = collections.OrderedDict([
        (ProjectionType.transversal, 'imgt'),
        (ProjectionType.coronal, 'imgc'),
        (ProjectionType.sagittal, 'imgs'),
    ])

    def __init__(self):
        self._projection_images = {}
        self.clear()

    @property
    def transversal(self) -> np.ndarray:
        """Returns transversal image projection
        """
        return self._projection_images[ProjectionType.transversal]

    @property
    def sagittal(self) -> np.ndarray:
        """Returns sagittal image projection
        """
        return self._projection_images[ProjectionType.sagittal]

    @property
    def coronal(self) -> np.ndarray:
        """Returns coronal image projection
        """
        return self._projection_images[ProjectionType.coronal]

    def proj_image(self, proj: ProjectionType):
        """Returns image projection for given type
        """
        return self._projection_images[proj]

    def read(self, memmap_filename: str, matlab_engine):
        """Reads projection images from memmap file
        """
        with open(memmap_filename, 'r') as fp:
            offset = 0

            for proj_type, image_name in self._projection_images_mapping.items():
                shape = get_image_shape(image_name, matlab_engine, nargout=2)
                self._projection_images[proj_type] = read_memmap_image(fp, shape, offset)
                offset += shape.prod()

    def clear(self):
        """Clean up all data
        """
        self._projection_images = {proj: None for proj in self._projection_images_mapping}

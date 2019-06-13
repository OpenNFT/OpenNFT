# -*- coding: utf-8 -*-

import collections
import numpy as np


class ProjectionImagesReader:
    """The class for reading projection images from memmap file
    """

    _projection_images_mapping = collections.OrderedDict([
        ('transversal', 'imgt'),
        ('sagittal', 'imgs'),
        ('coronal', 'imgc'),
    ])

    def __init__(self):
        self._projection_images = {}
        self.clear()

    @property
    def transversal(self) -> np.ndarray:
        """Returns transversal image projection
        """
        return self._projection_images['transversal']

    @property
    def sagittal(self) -> np.ndarray:
        """Returns sagittal image projection
        """
        return self._projection_images['sagittal']

    @property
    def coronal(self) -> np.ndarray:
        """Returns coronal image projection
        """
        return self._projection_images['coronal']

    def read(self, memmap_filename: str, matlab_engine):
        """Reads projection images from memmap file
        """
        with open(memmap_filename, 'r') as fp:
            offset = 0

            for proj_name, image_name in self._projection_images_mapping.items():
                shape = self._get_image_shape(image_name, matlab_engine)
                self._projection_images[proj_name] = self._read_memmap_image(fp, shape, offset)
                offset += shape.prod()

    def clear(self):
        """Clean up all data
        """
        self._projection_images = {proj: None for proj in self._projection_images_mapping}

    @staticmethod
    def _get_image_shape(image_name, matlab_engine):
        return np.array(matlab_engine.evalin('base', 'size({})'.format(image_name), nargout=3), dtype=np.int32)

    @staticmethod
    def _read_memmap_image(fp, shape, offset):
        return np.memmap(
            fp,
            dtype='uint8',
            mode='r',
            shape=tuple(shape),
            offset=offset,
            order='F'
        )

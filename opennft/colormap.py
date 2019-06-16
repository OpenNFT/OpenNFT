# -*- coding: utf-8 -*-

import typing as t

import numpy as np
from matplotlib import cm
from matplotlib import colors


_CmapType = t.Union[str, colors.Colormap]


def map_to_rgba(data: np.ndarray, cmap: _CmapType):
    """Mapping data to RGBA using given colormap

    Parameters
    ----------

    data: np.ndarray, np.ma.MaskedArray
        The 2D-data array (an image of projection for example)
    cmap: Colormap, str
        Colormap representation instance or name string
    Returns
    -------
    data: np.ndarray
        RGBA data array

    """
    if isinstance(cmap, str):
        cmap = cm.get_cmap(cmap)

    cmap.set_bad(alpha=0.0)

    normalizer = colors.Normalize(vmin=data.min(), vmax=data.max())
    mapper = cm.ScalarMappable(norm=normalizer, cmap=cmap)

    return mapper.to_rgba(data)

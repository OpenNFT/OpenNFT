# -*- coding: utf-8 -*-

import typing as t

import numpy as np
from matplotlib import cm
from matplotlib import colors


_DataType = t.Union[np.ndarray, np.ma.MaskedArray]
_CmapType = t.Union[str, colors.Colormap]
_NormType = t.Optional[float]


def map_to_rgba(data: _DataType, cmap: _CmapType, norm_min: _NormType = None, norm_max: _NormType = None):
    """Mapping data to RGBA using given colormap

    Parameters
    ----------

    data : np.ndarray, np.ma.MaskedArray
        The 2D-data array (an image of projection for example)
    cmap : Colormap, str
        Colormap representation instance or name string
    norm_min : float, None
        Minimum value for colormap normalization
    norm_max : float, None
        Maximum value for colormap normalization

    Returns
    -------
    data: np.ndarray
        RGBA data array

    """
    if isinstance(cmap, str):
        cmap = cm.get_cmap(cmap)

    if norm_min is None:
        norm_min = data.min()
    if norm_max is None:
        norm_max = data.max()

    cmap.set_bad(alpha=0.0)

    normalizer = colors.Normalize(vmin=norm_min, vmax=norm_max)
    mapper = cm.ScalarMappable(norm=normalizer, cmap=cmap)

    return mapper.to_rgba(data)

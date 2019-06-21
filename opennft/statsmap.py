# -*- coding: utf-8 -*-

import numpy as np

from matplotlib import cm
from matplotlib import colors


class RgbaStatsMap:
    """Represents the mapper stats to RGBA
    """

    _no_value = 0.0
    _quantile_interval = [0.05, 0.95]
    _cmap = None

    def __init__(self):
        self.colormap = 'hot'
        self._minimum_threshold = None
        self._maximum_threshold = None

    @property
    def colormap(self) -> colors.Colormap:
        return self._cmap

    @colormap.setter
    def colormap(self, cmap: colors.Colormap):
        if isinstance(cmap, str):
            cmap = cm.get_cmap(cmap)
        self._cmap = cmap
        self._cmap.set_bad(alpha=0.0)

    def __call__(self, stats_map: np.ndarray, auto_thresholds: bool = True) -> np.ndarray:
        # Zero value represents "no value"
        stats_map_ma = np.ma.masked_equal(stats_map, self._no_value)

        if auto_thresholds:
            self._compute_thresholds(stats_map_ma)

        stats_map_ma = np.ma.masked_outside(
            stats_map_ma, self._minimum_threshold, self._maximum_threshold)

        return self._map_to_rgba(stats_map_ma)

    @property
    def minimum_threshold(self) -> float:
        return self._minimum_threshold

    @property
    def maximum_threshold(self) -> float:
        return self._maximum_threshold

    def set_minimum_threshold(self, value: float):
        self._minimum_threshold = value

    def set_maximum_threshold(self, value: float):
        self._maximum_threshold = value

    def _compute_thresholds(self, stats_map):
        q = np.quantile(stats_map.compressed(), self._quantile_interval)
        self._minimum_threshold = q[0]
        self._maximum_threshold = q[1]

    def _map_to_rgba(self, stats_map_ma) -> np.ndarray:
        vmin = stats_map_ma.min()
        vmax = stats_map_ma.max()

        normalizer = colors.Normalize(vmin=vmin, vmax=vmax)
        mapper = cm.ScalarMappable(norm=normalizer, cmap=self._cmap)

        return mapper.to_rgba(stats_map_ma)

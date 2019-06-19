# -*- coding: utf-8 -*-

import typing as t
from PyQt5 import QtWidgets

import pyqtgraph as pg
import numpy as np

from opennft import pgext
from opennft import colormap


class MosaicImageViewWidget(QtWidgets.QWidget):
    """Mosaic image view class
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._background_imitem = pg.ImageItem(autoDownsample=True)
        self._stats_map_imitem = pg.ImageItem(autoDownsample=True)

        self._stats_map_image = None
        self._thr_min = None
        self._thr_max = None
        self._cmap = 'hot'
        self._thr_percentiles = [5., 95.]

        viewbox = pgext.ViewBoxWithoutPadding(
            lockAspect=True,
            enableMouse=False,
            enableMenu=False,
            invertY=True,
        )

        viewbox.addItem(self._background_imitem)
        viewbox.addItem(self._stats_map_imitem)

        glayout = pg.GraphicsLayoutWidget(self)
        glayout.ci.layout.setContentsMargins(0, 0, 0, 0)
        glayout.addItem(viewbox)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(glayout)

        self.setLayout(self._layout)

    def set_background_image(self, image: np.ndarray):
        self._background_imitem.setImage(image.T)

    def set_stats_map_image(self, image: t.Optional[np.ndarray], compute_thresholds: bool = True):
        if image is None:
            self._stats_map_imitem.clear()
            self._stats_map_image = None
            self._thr_min = self._thr_max = None
            return

        self._stats_map_image: np.ma.MaskedArray = np.ma.masked_equal(image, 0.0)

        if compute_thresholds or self._thr_min is None:
            self._compute_stats_map_thresholds()

        self._update_stats_map()

    def clear(self):
        self._background_imitem.clear()
        self._stats_map_imitem.clear()

    def clear_stats_map(self):
        self._stats_map_imitem.clear()

    @property
    def stats_map_min_threshold(self) -> float:
        return self._thr_min

    @property
    def stats_map_max_threshold(self) -> float:
        return self._thr_max

    def set_stats_map_min_threshold(self, thr):
        self._thr_min = thr
        self._update_stats_map()

    def set_stats_map_max_threshold(self, thr):
        self._thr_max = thr
        self._update_stats_map()

    def _compute_stats_map_thresholds(self):
        percentiles = np.percentile(self._stats_map_image.compressed(), self._thr_percentiles)
        self._thr_min = percentiles[0]
        self._thr_max = percentiles[1]

    def _update_stats_map(self):
        if self._stats_map_image is None:
            return

        map_ma = np.ma.masked_outside(self._stats_map_image, self._thr_min, self._thr_max)
        map_rgba = colormap.map_to_rgba(map_ma, cmap=self._cmap)

        self._stats_map_imitem.setImage(map_rgba.transpose((1, 0, 2)))

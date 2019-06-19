# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets

import pyqtgraph as pg
import numpy as np

from opennft import pgext


class MosaicImageViewWidget(QtWidgets.QWidget):
    """Mosaic image view class
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._background_imitem = pg.ImageItem(autoDownsample=True)
        self._stats_map_imitem = pg.ImageItem(autoDownsample=True)

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

    def set_stats_map_image(self, image: np.ndarray):
        self._stats_map_imitem.setImage(image.transpose((1, 0, 2)))

    def clear(self):
        self._background_imitem.clear()
        self._stats_map_imitem.clear()

    def clear_stats_map(self):
        self._stats_map_imitem.clear()

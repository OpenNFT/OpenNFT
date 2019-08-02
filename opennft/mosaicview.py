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
        self._map_imitem = pg.ImageItem(autoDownsample=True)

        self._viewbox = pgext.ViewBoxWithoutPadding(
            lockAspect=True,
            enableMouse=True,
            enableMenu=False,
            invertY=True,
        )

        self._viewbox.addItem(self._background_imitem)
        self._viewbox.addItem(self._map_imitem)

        glayout = pg.GraphicsLayoutWidget(self)
        glayout.ci.layout.setContentsMargins(0, 0, 0, 0)
        glayout.addItem(self._viewbox)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(glayout)

        self.setLayout(self._layout)

    def mouseDoubleClickEvent(self, ev):
        self._viewbox.autoRange()

    def set_background_image(self, image: np.ndarray):
        self._background_imitem.setImage(image.T)

    def set_map_image(self, image: np.ndarray):
        self._map_imitem.setImage(image.transpose((1, 0, 2)))

    def clear(self):
        self._background_imitem.clear()
        self._map_imitem.clear()

    def clear_map(self):
        self._map_imitem.clear()

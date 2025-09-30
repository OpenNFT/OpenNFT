# -*- coding: utf-8 -*-

from PyQt6 import QtWidgets

import pyqtgraph as pg
import numpy as np

from opennft import pgext


class MosaicImageViewWidget(QtWidgets.QWidget):
    """Mosaic image view class
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._background_imitem = pg.ImageItem(autoDownsample=True)
        self._pos_map_imitem = pg.ImageItem(autoDownsample=True)
        self._neg_map_imitem = pg.ImageItem(autoDownsample=True)

        self._viewbox = pgext.ViewBoxWithoutPadding(
            lockAspect=True,
            enableMouse=True,
            enableMenu=False,
            invertY=True,
        )

        self._viewbox.addItem(self._background_imitem)
        self._viewbox.addItem(self._pos_map_imitem)
        self._viewbox.addItem(self._neg_map_imitem)

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

    def set_pos_map_image(self, image: np.ndarray):
        self._pos_map_imitem.setImage(image.transpose((1, 0, 2)))

    def set_neg_map_image(self, image: np.ndarray):
        self._neg_map_imitem.setImage(image.transpose((1, 0, 2)))

    def clear(self):
        self._background_imitem.clear()
        self._pos_map_imitem.clear()
        self._neg_map_imitem.clear()

    def clear_pos_map(self):
        self._pos_map_imitem.clear()

    def clear_neg_map(self):
        self._neg_map_imitem.clear()

    def set_pos_map_visible(self, flag):
        self._pos_map_imitem.setVisible(flag)

    def set_neg_map_visible(self, flag):
        self._neg_map_imitem.setVisible(flag)

    def set_pos_map_opacity(self, value):
        self._pos_map_imitem.setOpacity(value)

    def set_neg_map_opacity(self, value):
        self._neg_map_imitem.setOpacity(value)

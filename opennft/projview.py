# -*- coding: utf-8 -*-

"""
Class for displaing triplanar EPI projections

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Evgeny Prilepin

"""

import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui


class ProjectionImageView(pg.ViewBox):

    cursorPositionChanged = QtCore.Signal(tuple)

    def __init__(self, parent=None, border=None, enableMouse=True, name=None):

        super().__init__(
            parent=parent,
            border=border,
            enableMouse=enableMouse,
            name=name,
            lockAspect=True,
            enableMenu=False,
            invertY=True,
        )

        self._background_imitem = pg.ImageItem(autoDownsample=True)
        self._stats_map_imitem = pg.ImageItem(autoDownsample=True)

        self.addItem(self._background_imitem)
        self.addItem(self._stats_map_imitem)

        self._image_shape = [0, 0]
        self._coords = (0, 0)

    def suggestPadding(self, axis):
        return 0.01

    def set_background_image(self, image):
        self._image_shape = image.shape
        self._background_imitem.setImage(image.T)

    def set_stats_map_image(self, image):
        self._stats_map_imitem.setImage(np.transpose(image, axes=(1, 0, 2)))

    def clear(self):
        self._image_shape = [0, 0]
        self._coords = (0, 0)
        self._background_imitem.clear()
        self._stats_map_imitem.clear()

    def mouseClickEvent(self, ev):
        self._changePositionCursor(ev)
        ev.accept()

    def mouseDragEvent(self, ev, axis=None):
        #self._changePositionCursor(ev)
        ev.accept()

    def wheelEvent(self, ev, axis=None):
        ev.ignore()

    def getCoords(self):
        return self._coords

    def _changePositionCursor(self, ev):
        w = self._image_shape[1]
        h = self._image_shape[0]

        if h == 0 or w == 0:
            return

        viewPos = self.mapSceneToView(ev.scenePos())
        imagePos = self._background_imitem.mapFromView(viewPos)

        x = int(imagePos.x())
        y = int(imagePos.y())

        xx = 0
        yy = 0

        if 0 <= y < h:
            yy = y
        elif y < 0:
            yy = 0
        elif y >= h:
            yy = h - 1

        if 0 <= x < w:
            xx = x
        elif x < 0:
            xx = 0
        elif x >= w:
            xx = w - 1

        self._coords = (xx, yy)
        self.cursorPositionChanged.emit(self._coords)


class ProjectionsWidget(QtGui.QWidget):

    cursorPositionChanged = QtCore.Signal(tuple, tuple)

    # --------------------------------------------------------------------------
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._layout = QtGui.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self._layout)

        self._view = pg.GraphicsView(self)
        self._layout.addWidget(self._view)

        self._glayout = pg.GraphicsLayout(border=(150, 150, 150))
        self._view.setCentralItem(self._glayout)

        self._sagittalViewBox = ProjectionImageView(
            parent=self._glayout, name='Sagittal')

        self._coronalViewBox = ProjectionImageView(
            parent=self._glayout, name='Coronal')

        self._transversalViewBox = ProjectionImageView(
            parent=self._glayout, name='Axial')

        self._transversalLayout = self._setupViewBoxLayout(self._transversalViewBox, 1, 0)
        self._sagittalLayout = self._setupViewBoxLayout(self._sagittalViewBox, 0, 0)
        self._coronalLayout = self._setupViewBoxLayout(self._coronalViewBox, 0, 1)

        self._transversalViewBox.cursorPositionChanged.connect(self._onCursorPositionChanged)
        self._sagittalViewBox.cursorPositionChanged.connect(self._onCursorPositionChanged)
        self._coronalViewBox.cursorPositionChanged.connect(self._onCursorPositionChanged)

        self._coords = {
            self._transversalViewBox: (0, 0),
            self._sagittalViewBox: (0, 0),
            self._coronalViewBox: (0, 0),
        }

        self._projTypes = {
            self._transversalViewBox: (1, 0, 0),
            self._sagittalViewBox: (0, 1, 0),
            self._coronalViewBox: (0, 0, 1),
        }

    def set_transversal_background_image(self, image):
        self._transversalViewBox.set_background_image(image)

    def set_sagittal_background_image(self, image):
        self._sagittalViewBox.set_background_image(image)

    def set_coronal_background_image(self, image):
        self._coronalViewBox.set_background_image(image)

    def set_transversal_stats_map_image(self, image):
        self._transversalViewBox.set_stats_map_image(image)

    def set_sagittal_stats_map_image(self, image):
        self._sagittalViewBox.set_stats_map_image(image)

    def set_coronal_stats_map_image(self, image):
        self._coronalViewBox.set_stats_map_image(image)

    def clear(self):
        self._transversalViewBox.clear()
        self._sagittalViewBox.clear()
        self._coronalViewBox.clear()

    def _setupViewBoxLayout(self, viewbox, row, col):
        layout = self._glayout.addLayout(row=row, col=col)

        layout.setContentsMargins(1, 1, 1, 1)
        layout.addItem(viewbox)

        return layout

    def _onCursorPositionChanged(self, pos):
        proj = self.sender()

        self._coords[proj] = pos
        projtype = self._projTypes[proj]

        self.cursorPositionChanged.emit(pos, projtype)

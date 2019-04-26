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

from opennft import excepthook

excepthook.set_hook()


# ==============================================================================
class ProjectionImageView(pg.ViewBox):

    cursorPositionChanged = QtCore.Signal(tuple)

    # --------------------------------------------------------------------------
    def __init__(self, parent=None, border=None, enableMouse=True, name=None):

        super().__init__(
            parent=parent,
            border=border,
            enableMouse=enableMouse,
            name=name,
            lockAspect=True,
            enableMenu=False,
            invertX=False,
            invertY=True,
        )

        self._imageItem = pg.ImageItem(autoDownsample=True)
        self.addItem(self._imageItem)

        self._imageShape = [0, 0]
        self._coords = (0, 0)

    # --------------------------------------------------------------------------
    def suggestPadding(self, axis):
        return 0.01

    # --------------------------------------------------------------------------
    def setImage(self, image):
        self._imageShape = image.shape
        self._imageItem.setImage(np.transpose(image, axes=(1, 0, 2)))

    # --------------------------------------------------------------------------
    def clear(self):
        self._imageShape = [0, 0]
        self._coords = (0, 0)
        self._imageItem.clear()

    # --------------------------------------------------------------------------
    def mouseClickEvent(self, ev):
        self._changePositionCursor(ev)
        ev.accept()

    # --------------------------------------------------------------------------
    def mouseDragEvent(self, ev, axis=None):
        #self._changePositionCursor(ev)
        ev.accept()

    # --------------------------------------------------------------------------
    def wheelEvent(self, ev, axis=None):
        ev.ignore()

    # --------------------------------------------------------------------------
    def getCoords(self):
        return self._coords

    # --------------------------------------------------------------------------
    def _changePositionCursor(self, ev):
        w = self._imageShape[1]
        h = self._imageShape[0]

        if h == 0 or w == 0:
            return

        viewPos = self.mapSceneToView(ev.scenePos())
        imagePos = self._imageItem.mapFromView(viewPos)

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


# ==============================================================================
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

    # --------------------------------------------------------------------------
    def setTransversalImage(self, image):
        self._transversalViewBox.setImage(image)

    # --------------------------------------------------------------------------
    def setSagittalImage(self, image):
        self._sagittalViewBox.setImage(image)

    # --------------------------------------------------------------------------
    def setCoronalImage(self, image):
        self._coronalViewBox.setImage(image)

    # --------------------------------------------------------------------------
    def clear(self):
        self._transversalViewBox.clear()
        self._sagittalViewBox.clear()
        self._coronalViewBox.clear()

    # --------------------------------------------------------------------------
    def _setupViewBoxLayout(self, viewbox, row, col):
        layout = self._glayout.addLayout(row=row, col=col)

        layout.setContentsMargins(1, 1, 1, 1)
        layout.addItem(viewbox)

        return layout

    # --------------------------------------------------------------------------
    def _onCursorPositionChanged(self, pos):
        proj = self.sender()

        self._coords[proj] = pos
        projtype = self._projTypes[proj]

        self.cursorPositionChanged.emit(pos, projtype)

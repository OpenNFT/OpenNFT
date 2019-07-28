# -*- coding: utf-8 -*-

"""
Class for displaing triplanar EPI projections

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Evgeny Prilepin

"""

import enum

import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui


class ProjectionType(enum.Enum):
    sagittal = (0, 1, 0)
    coronal = (0, 0, 1)
    transversal = (1, 0, 0)


class ProjectionImageView(pg.ViewBox):

    cursorPositionChanged = QtCore.Signal(tuple, ProjectionType)
    resetView = QtCore.Signal(ProjectionType)
    viewChanged = QtCore.Signal(tuple, ProjectionType)

    def __init__(self, parent, proj_type, border=None):

        name = proj_type.name.capitalize()

        super().__init__(
            parent=parent,
            border=border,
            enableMouse=True,
            name=name,
            lockAspect=True,
            enableMenu=False,
            invertY=True,
        )

        self._proj_type = proj_type

        self._background_imitem = pg.ImageItem(autoDownsample=True)
        self._stats_map_imitem = pg.ImageItem(autoDownsample=True)

        self.addItem(self._background_imitem)
        self.addItem(self._stats_map_imitem)

        # self._background_imitem.setBorder({'color': pg.mkColor('g'), 'width': 1})

        self._name_textitem = pg.TextItem(
            text=name, color=pg.mkColor('g'), anchor=(1, 0))
        self._name_textitem.setParentItem(self)

        self._image_shape = [0, 0]

        self._click_event = None
        self._cursor_pos_change_timer = QtCore.QTimer(self)
        self._cursor_pos_change_timer.setInterval(150)
        self._cursor_pos_change_timer.timeout.connect(self._change_cursor_position)

        self.sigResized.connect(self._viewbox_resized)

    def set_background_image(self, image):
        self._image_shape = image.shape
        self._background_imitem.setImage(image.T)

    def set_stats_map_image(self, image):
        self._stats_map_imitem.setImage(np.transpose(image, axes=(1, 0, 2)))

    def clear(self):
        self._image_shape = [0, 0]
        self._background_imitem.clear()
        self._stats_map_imitem.clear()

    def suggestPadding(self, axis=None):
        return 0.01

    def mouseClickEvent(self, ev):
        ev.accept()
        self._click_event = ev
        self._cursor_pos_change_timer.start()

    def mouseDoubleClickEvent(self, ev):
        self._cursor_pos_change_timer.stop()
        self.autoRange()
        self.resetView.emit(self._proj_type)

    def wheelEvent(self, ev, axis=None):
        super().wheelEvent(ev, axis)
        self.viewChanged.emit(tuple(self.viewRange()), self._proj_type)

    def mouseDragEvent(self, ev, axis=None):
        super().mouseDragEvent(ev, axis)
        self.viewChanged.emit(tuple(self.viewRange()), self._proj_type)

    def _viewbox_resized(self):
        r = self.boundingRect()
        self._name_textitem.setPos(r.width(), 0)

    def _change_cursor_position(self):
        self._cursor_pos_change_timer.stop()

        w = self._image_shape[1]
        h = self._image_shape[0]

        if h == 0 or w == 0:
            return

        view_pos = self.mapSceneToView(self._click_event.scenePos())
        image_pos = self._background_imitem.mapFromView(view_pos)

        x = int(image_pos.x())
        y = int(image_pos.y())

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

        coords = (xx, yy)
        self.cursorPositionChanged.emit(coords, self._proj_type)


class ProjectionsWidget(QtGui.QWidget):

    cursorPositionChanged = QtCore.Signal(tuple, ProjectionType)

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._layout = QtGui.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self._layout)

        self._view = pg.GraphicsView(self)
        self._layout.addWidget(self._view)

        self._glayout = pg.GraphicsLayout(border=(150, 150, 150))
        self._view.setCentralItem(self._glayout)

        self._sagittal_viewbox = ProjectionImageView(
            parent=self._glayout,
            proj_type=ProjectionType.sagittal,
        )

        self._coronal_viewbox = ProjectionImageView(
            parent=self._glayout,
            proj_type=ProjectionType.coronal,
        )

        self._transversal_viewbox = ProjectionImageView(
            parent=self._glayout,
            proj_type=ProjectionType.transversal,
        )

        self._proj_views = {
            ProjectionType.sagittal: self._sagittal_viewbox,
            ProjectionType.coronal: self._coronal_viewbox,
            ProjectionType.transversal: self._transversal_viewbox,
        }

        self._sagittal_layout = self._setup_viewbox_layout(self._sagittal_viewbox, 0, 0)
        self._coronal_layout = self._setup_viewbox_layout(self._coronal_viewbox, 0, 1)
        self._transversal_layout = self._setup_viewbox_layout(self._transversal_viewbox, 1, 0)

        self._sagittal_viewbox.cursorPositionChanged.connect(self._on_cursor_position_changed)
        self._coronal_viewbox.cursorPositionChanged.connect(self._on_cursor_position_changed)
        self._transversal_viewbox.cursorPositionChanged.connect(self._on_cursor_position_changed)

        self._sagittal_viewbox.sigResized.connect(lambda _: self.sync_proj_view())

        self._sagittal_viewbox.viewChanged.connect(self._sync_proj_view)
        self._coronal_viewbox.viewChanged.connect(self._sync_proj_view)
        self._transversal_viewbox.viewChanged.connect(self._sync_proj_view)

        self._sagittal_viewbox.resetView.connect(self._reset_view)
        self._coronal_viewbox.resetView.connect(self._reset_view)
        self._transversal_viewbox.resetView.connect(self._reset_view)

    def set_transversal_background_image(self, image):
        self._transversal_viewbox.set_background_image(image)

    def set_sagittal_background_image(self, image):
        self._sagittal_viewbox.set_background_image(image)

    def set_coronal_background_image(self, image):
        self._coronal_viewbox.set_background_image(image)

    def set_transversal_stats_map_image(self, image):
        self._transversal_viewbox.set_stats_map_image(image)

    def set_sagittal_stats_map_image(self, image):
        self._sagittal_viewbox.set_stats_map_image(image)

    def set_coronal_stats_map_image(self, image):
        self._coronal_viewbox.set_stats_map_image(image)

    def clear(self):
        self._transversal_viewbox.clear()
        self._sagittal_viewbox.clear()
        self._coronal_viewbox.clear()

    def sync_proj_view(self, proj=ProjectionType.sagittal, auto_range=False):
        view_range = self._proj_views[proj].viewRange()
        self._sync_proj_view(view_range, proj, auto_range)

    def _setup_viewbox_layout(self, viewbox, row, col):
        layout = self._glayout.addLayout(row=row, col=col)

        layout.setContentsMargins(1, 1, 1, 1)
        layout.addItem(viewbox)

        return layout

    def _on_cursor_position_changed(self, pos, proj_type):
        self.cursorPositionChanged.emit(pos, proj_type)

    @staticmethod
    def _set_view_range(view, xrange=None, yrange=None, auto_range=False):
        if auto_range:
            view.autoRange()

        view.setRange(xRange=xrange, yRange=yrange, padding=0.0, disableAutoRange=True)
        view.state['targetRange'] = view.viewRange()

    def _sync_proj_view(self, view_range, proj, auto_range=False):
        xrange, yrange = view_range

        if proj == ProjectionType.sagittal:
            self._set_view_range(self._coronal_viewbox, yrange=yrange, auto_range=auto_range)
            self._set_view_range(self._transversal_viewbox, xrange=xrange, auto_range=auto_range)

        if proj == ProjectionType.coronal:
            self._set_view_range(self._sagittal_viewbox, yrange=yrange, auto_range=auto_range)
            xrange, _ = self._sagittal_viewbox.viewRange()
            self._set_view_range(self._transversal_viewbox, xrange=xrange, auto_range=auto_range)

        if proj == ProjectionType.transversal:
            self._set_view_range(self._sagittal_viewbox, xrange=xrange, auto_range=auto_range)
            _, yrange = self._sagittal_viewbox.viewRange()
            self._set_view_range(self._coronal_viewbox, yrange=yrange, auto_range=auto_range)

    def _reset_view(self):
        self._sagittal_viewbox.autoRange()
        self.sync_proj_view(auto_range=True)

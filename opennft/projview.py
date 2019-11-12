# -*- coding: utf-8 -*-

"""
Class for displaing triplanar EPI projections

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Evgeny Prilepin

"""

import enum

import numpy as np
from cycler import cycler

import pyqtgraph as pg
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from opennft import config


class ProjectionType(enum.Enum):
    transversal = (1, 0, 0)
    coronal = (0, 1, 0)
    sagittal = (0, 0, 1)


class ProjectionImageView(pg.ViewBox):

    cursorPositionChanged = QtCore.pyqtSignal(tuple, ProjectionType)
    resetView = QtCore.pyqtSignal(ProjectionType)
    viewChanged = QtCore.pyqtSignal(tuple, ProjectionType)

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
        self._pos_map_imitem = pg.ImageItem(autoDownsample=True)
        self._neg_map_imitem = pg.ImageItem(autoDownsample=True)

        self._roi_plotdataitems = []
        self._roi_pens = cycler(color=config.PROJ_ROI_COLORS)

        self.addItem(self._background_imitem)
        self.addItem(self._pos_map_imitem)
        self.addItem(self._neg_map_imitem)

        # self._background_imitem.setBorder({'color': pg.mkColor('g'), 'width': 1})

        # self._name_textitem = pg.TextItem(
        #     text=name, color=pg.mkColor('g'), anchor=(1, 0))
        # self._name_textitem.setParentItem(self)

        self._image_shape = [0, 0]

        self._click_event = None
        self._cursor_pos_change_timer = QtCore.QTimer(self)
        self._cursor_pos_change_timer.setInterval(150)
        self._cursor_pos_change_timer.timeout.connect(self._change_cursor_position)

        # self.sigResized.connect(self._viewbox_resized)

    def set_background_image(self, image):
        self._image_shape = image.shape
        self._background_imitem.setImage(image.T)

    def set_pos_map_image(self, image):
        self._pos_map_imitem.setImage(np.transpose(image, axes=(1, 0, 2)))

    def set_neg_map_image(self, image):
        self._neg_map_imitem.setImage(np.transpose(image, axes=(1, 0, 2)))

    def set_pos_map_visible(self, flag):
        self._pos_map_imitem.setVisible(flag)

    def set_neg_map_visible(self, flag):
        self._neg_map_imitem.setVisible(flag)

    def set_pos_map_opacity(self, value):
        self._pos_map_imitem.setOpacity(value)

    def set_neg_map_opacity(self, value):
        self._neg_map_imitem.setOpacity(value)

    def set_roi(self, roi_bounds):
        self._clear_roi()
        pens = self._roi_pens()

        for region_bounds, pen in zip(roi_bounds, pens):
            for piece_coords in region_bounds:
                coords = np.array(piece_coords)
                if coords.size == 0:
                    continue

                y = coords[:, 0]
                x = coords[:, 1]

                pen['width'] = 2
                item = pg.PlotCurveItem(x=x, y=y, pen=pen)

                self._roi_plotdataitems.append(item)
                self.addItem(item)

    def clear(self):
        self._image_shape = [0, 0]
        self._background_imitem.clear()
        self._pos_map_imitem.clear()
        self._neg_map_imitem.clear()
        self._clear_roi()

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

    # def _viewbox_resized(self):
    #     r = self.boundingRect()
    #     self._name_textitem.setPos(r.width(), 0)

    def _clear_roi(self):
        for item in self._roi_plotdataitems:
            item.clear()
            self.removeItem(item)
        self._roi_plotdataitems.clear()

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


class ProjectionsWidget(QtWidgets.QWidget):

    cursorPositionChanged = QtCore.pyqtSignal(tuple, ProjectionType)

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self._layout)

        self._view = pg.GraphicsView(self)
        self._layout.addWidget(self._view)

        self._view_layout = pg.GraphicsLayout(border=pg.mkColor('#969696'))
        self._view.setCentralItem(self._view_layout)

        self._transversal_viewbox = ProjectionImageView(
            parent=self._view_layout,
            proj_type=ProjectionType.transversal,
        )

        self._coronal_viewbox = ProjectionImageView(
            parent=self._view_layout,
            proj_type=ProjectionType.coronal,
        )

        self._sagittal_viewbox = ProjectionImageView(
            parent=self._view_layout,
            proj_type=ProjectionType.sagittal,
        )

        self._proj_views = {
            ProjectionType.transversal: self._transversal_viewbox,
            ProjectionType.coronal: self._coronal_viewbox,
            ProjectionType.sagittal: self._sagittal_viewbox,
        }

        self._transversal_layout = self._setup_viewbox_layout(self._transversal_viewbox, 1, 0)
        self._coronal_layout = self._setup_viewbox_layout(self._coronal_viewbox, 0, 0)
        self._sagittal_layout = self._setup_viewbox_layout(self._sagittal_viewbox, 0, 1)

        for view in self._proj_views.values():
            view.cursorPositionChanged.connect(self._on_cursor_position_changed)
            view.viewChanged.connect(self._sync_proj_view)
            view.resetView.connect(self.reset_view)

        self._coronal_viewbox.sigResized.connect(self._sync_when_resize)

    def set_background_image(self, proj: ProjectionType, image):
        self._proj_views[proj].set_background_image(image)

    def set_pos_map_image(self, proj: ProjectionType, image):
        self._proj_views[proj].set_pos_map_image(image)

    def set_neg_map_image(self, proj: ProjectionType, image):
        self._proj_views[proj].set_neg_map_image(image)

    def set_pos_map_visible(self, flag):
        for view in self._proj_views.values():
            view.set_pos_map_visible(flag)

    def set_neg_map_visible(self, flag):
        for view in self._proj_views.values():
            view.set_neg_map_visible(flag)

    def set_pos_map_opacity(self, value):
        for view in self._proj_views.values():
            view.set_pos_map_opacity(value)

    def set_neg_map_opacity(self, value):
        for view in self._proj_views.values():
            view.set_neg_map_opacity(value)

    def set_roi(self, proj: ProjectionType, roi_bounds):
        self._proj_views[proj].set_roi(roi_bounds)

    def clear(self):
        for view in self._proj_views.values():
            view.clear()

    def reset_view(self):
        for view in self._proj_views.values():
            view.autoRange()

        view_range = self._coronal_viewbox.viewRange()
        self._sync_proj_view(view_range, ProjectionType.coronal)

    def _setup_viewbox_layout(self, viewbox, row, col):
        layout = self._view_layout.addLayout(row=row, col=col)

        layout.setContentsMargins(1, 1, 1, 1)
        layout.addItem(viewbox)

        return layout

    def _on_cursor_position_changed(self, pos, proj_type):
        self.cursorPositionChanged.emit(pos, proj_type)

    @staticmethod
    def _set_view_range(view, xrange=None, yrange=None):
        view.setRange(xRange=xrange, yRange=yrange, padding=0.0, disableAutoRange=True)
        view.state['targetRange'] = view.viewRange()

    def _sync_proj_view(self, view_range, proj):
        xrange, yrange = view_range

        if proj == ProjectionType.transversal:
            self._set_view_range(self._coronal_viewbox, xrange=xrange)
            _, yrange = self._coronal_viewbox.viewRange()
            self._set_view_range(self._sagittal_viewbox, yrange=yrange)

        if proj == ProjectionType.coronal:
            self._set_view_range(self._sagittal_viewbox, yrange=yrange)
            self._set_view_range(self._transversal_viewbox, xrange=xrange)

        if proj == ProjectionType.sagittal:
            self._set_view_range(self._coronal_viewbox, yrange=yrange)
            xrange, _ = self._coronal_viewbox.viewRange()
            self._set_view_range(self._transversal_viewbox, xrange=xrange)

    def _sync_when_resize(self):
        view_range = self._coronal_viewbox.viewRange()
        self._sync_proj_view(view_range, ProjectionType.coronal)

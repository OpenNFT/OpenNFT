# -*- coding: utf-8 -*-

import collections
import typing as t

from loguru import logger
import numpy as np

from matplotlib import cm
from matplotlib import colors

import pyqtgraph as pg

from PyQt6 import QtWidgets
from PyQt6 import QtCore

from opennft import pgext

from copy import copy

ColormapType = t.Union[str, colors.Colormap]
Thresholds = collections.namedtuple('Thresholds', ('lower', 'upper'))


HOT_COLORMAP = 'hot'
COLD_COLORMAP = 'Blues_r'


class MapImageThresholdsCalculator:
    """Statistics/CNR map thresholds calculator class

    The class computes the optimal thresholds for display a map.
    """

    def __init__(self, thr_coeff: float = 0.0005, no_value: float = 0.0):
        self._thr_coeff = thr_coeff
        self._no_value = no_value

    def __call__(self, map_image: np.ndarray) -> t.Optional[Thresholds]:
        map_image_ma = np.ma.masked_equal(map_image, self._no_value)

        if map_image_ma.mask.all():
            logger.warning('There are no any values on the map')
            return None

        data = np.sort(map_image_ma.compressed().ravel())

        lower_data = data[:int(self._thr_coeff * data.size)]
        upper_data = data[int(data.size - self._thr_coeff * data.size):]

        if lower_data.size > 0:
            lower_thr = np.median(lower_data)
        else:
            lower_thr = data.min()

        if upper_data.size > 0:
            upper_thr = np.median(upper_data)
        else:
            upper_thr = data.min()

        return Thresholds(lower_thr, upper_thr)


class RgbaMapImage:
    """Represents the mapper map image to RGBA
    """

    def __init__(self, colormap: ColormapType = HOT_COLORMAP, no_value: float = 0.0):
        self._no_value = no_value

        if isinstance(colormap, str):
            colormap = copy(cm.get_cmap(colormap))

        self._colormap = colormap
        self._colormap.set_bad(alpha=0.0)

    def __call__(self, map_image: np.ndarray, thresholds: t.Optional[Thresholds] = None,
                 alpha: float = 1.0) -> t.Optional[np.ndarray]:

        map_image_ma = np.ma.masked_equal(map_image, self._no_value)

        if map_image_ma.mask.all():
            return

        if thresholds is not None:
            map_image_ma = np.ma.masked_outside(
                map_image_ma, thresholds.lower, thresholds.upper)

        return self._map_to_rgba(map_image_ma, alpha)

    def _map_to_rgba(self, stats_map_ma, alpha) -> np.ndarray:
        vmin = stats_map_ma.min()
        vmax = stats_map_ma.max()

        normalizer = colors.Normalize(vmin=vmin, vmax=vmax)
        mapper = cm.ScalarMappable(norm=normalizer, cmap=self._colormap)

        return mapper.to_rgba(stats_map_ma, alpha=alpha)


class MapImageThresholdsWidget(QtWidgets.QWidget):
    """The widget for manipulating stats/cnr map thresholds
    """

    thresholds_manually_changed = QtCore.pyqtSignal(Thresholds)

    MIN_THRESHOLD = 0
    MAX_THRESHOLD = 255
    STEP = 5

    def __init__(self, parent: QtCore.QObject = None, colormap: ColormapType = HOT_COLORMAP):
        super().__init__(parent)

        self._colormap = colormap

        self._lower_threshold_spinbox = QtWidgets.QDoubleSpinBox(self)
        self._upper_threshold_spinbox = QtWidgets.QDoubleSpinBox(self)

        self._colorbar_imageitem = pg.ImageItem()

        self._colorbar_viewbox = pgext.ViewBoxWithoutPadding(
            lockAspect=False,
            enableMouse=False,
            enableMenu=False,
        )

        self._colorbar_viewbox.addItem(self._colorbar_imageitem)

        self._colorbar_layout = pg.GraphicsLayoutWidget(self)

        size_policy = self._colorbar_layout.sizePolicy()
        size_policy.setVerticalPolicy(QtWidgets.QSizePolicy.Policy.Fixed)
        size_policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Policy.Ignored)
        self._colorbar_layout.setSizePolicy(size_policy)

        self._colorbar_layout.ci.layout.setContentsMargins(0, 0, 0, 0)
        self._colorbar_layout.addItem(self._colorbar_viewbox)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._lower_threshold_spinbox)
        layout.addWidget(self._colorbar_layout)
        layout.addWidget(self._upper_threshold_spinbox)
        layout.setStretch(1, 1)

        self.setLayout(layout)
        self.setMaximumWidth(400)

        self._lower_threshold_spinbox.setMinimum(self.MIN_THRESHOLD)
        self._lower_threshold_spinbox.setMaximum(self.MAX_THRESHOLD)
        self._lower_threshold_spinbox.setSingleStep(self.STEP)
        self._lower_threshold_spinbox.setValue(self.MIN_THRESHOLD)

        self._upper_threshold_spinbox.setMinimum(self.MIN_THRESHOLD)
        self._upper_threshold_spinbox.setMaximum(self.MAX_THRESHOLD)
        self._upper_threshold_spinbox.setSingleStep(self.STEP)
        self._upper_threshold_spinbox.setValue(self.MAX_THRESHOLD)

        self._map_no_value = 0.0
        self._auto_thresholds = True
        self._thr_calculator = MapImageThresholdsCalculator(no_value=self._map_no_value)

        self._make_colorbar()

        self._lower_threshold_spinbox.valueChanged.connect(self._thresholds_changed)
        self._upper_threshold_spinbox.valueChanged.connect(self._thresholds_changed)

    @property
    def auto_thresholds(self) -> bool:
        return self._auto_thresholds

    @auto_thresholds.setter
    def auto_thresholds(self, value: bool):
        self._auto_thresholds = value

    def reset(self):
        self._auto_thresholds = True
        self._set_thresholds(Thresholds(self.MIN_THRESHOLD, self.MAX_THRESHOLD))

    def compute_thresholds(self, map_values: np.ndarray):
        if not self.auto_thresholds:
            return

        thresholds = self._thr_calculator(map_values)

        if thresholds:
            self._set_thresholds(thresholds)
        else:
            logger.warning('Cannot compute thresholds')

    def compute_rgba(self, map_image, alpha: float = 1.0):
        thresholds = self._get_thresholds()
        rgba_stats_map = RgbaMapImage(colormap=self._colormap, no_value=self._map_no_value)
        return rgba_stats_map(map_image, thresholds, alpha)

    def resizeEvent(self, ev):
        self._colorbar_layout.setFixedHeight(self._lower_threshold_spinbox.height())
        self._colorbar_viewbox.autoRange()

    def _make_colorbar(self):
        w = self._colorbar_layout.width()
        h = self._colorbar_layout.height()

        colorbar_values = np.linspace(0., 1., w)
        colorbar_image = np.array(colorbar_values, ndmin=2).repeat(h, axis=0)
        colorbar_rgba = RgbaMapImage(colormap=self._colormap, no_value=-1)(colorbar_image)

        self._colorbar_imageitem.setImage(colorbar_rgba.transpose((1, 0, 2)))
        self._colorbar_viewbox.autoRange()

    def set_thresholds(self, thresholds):
        if not self.auto_thresholds:
            return

        if thresholds:
            self._set_thresholds(thresholds)
        else:
            logger.warning('Cannot compute thresholds')

    def _set_thresholds(self, thresholds):
        self._lower_threshold_spinbox.blockSignals(True)
        self._upper_threshold_spinbox.blockSignals(True)

        self._lower_threshold_spinbox.setValue(thresholds.lower)
        self._upper_threshold_spinbox.setValue(thresholds.upper)

        self._lower_threshold_spinbox.blockSignals(False)
        self._upper_threshold_spinbox.blockSignals(False)

    def get_thresholds(self):
        lower = self._lower_threshold_spinbox.value()
        upper = self._upper_threshold_spinbox.value()
        return Thresholds(lower, upper)

    def _get_thresholds(self):
        lower = self._lower_threshold_spinbox.value()
        upper = self._upper_threshold_spinbox.value()
        return Thresholds(lower, upper)

    def _thresholds_changed(self):
        self.thresholds_manually_changed.emit(self._get_thresholds())

# -*- coding: utf-8 -*-

import pyqtgraph as pg


class ViewBoxWithoutPadding(pg.ViewBox):
    def suggestPadding(self, axis):
        return 0.0

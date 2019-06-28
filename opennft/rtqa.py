# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import uic

import numpy as np
import pyqtgraph as pg
import matlab

from opennft import utils
from opennft import config
from opennft.rtqa_fdm import FD


class RTQAWindow(QtWidgets.QWidget):

    def __init__(self, xrange, parent=None):
        super().__init__(parent=parent, flags=QtCore.Qt.Window)

        uic.loadUi(utils.get_ui_file('rtqa.ui'), self)

        self._fd = FD(xrange)
        self.names = ['X', 'Y', 'Z', 'Pitch', 'Roll', 'Yaw', 'FD']

        self.comboBox.currentTextChanged.connect(self.onComboboxChanged)

        self.snrplot = pg.PlotWidget(self)
        self.snrplot.setBackground((255, 255, 255))
        self.snrPlot.addWidget(self.snrplot)

        p = self.snrplot.getPlotItem()
        p.setTitle('Signal-Noise Ratio', size='')
        p.setLabel('left', "Amplitude [a.u.]")
        p.setMenuEnabled(enableMenu=False)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)

        self._plot_translat = pg.PlotWidget(self)
        self._plot_translat.setBackground((255, 255, 255))
        self.tdPlot.addWidget(self._plot_translat)

        p = self._plot_translat.getPlotItem()
        p.setTitle('Translational Displacement', size='')
        p.setLabel('left', "Amplitude [mm]")
        p.setMenuEnabled(enableMenu=True)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)

        self.makeRoiPlotLegend(self.tdLabel, self.names[0:3], config.PLOT_PEN_COLORS[0:3])

        self._plot_rotat = pg.PlotWidget(self)
        self._plot_rotat.setBackground((255, 255, 255))
        self.rdPlot.addWidget(self._plot_rotat)

        p = self._plot_rotat.getPlotItem()
        p.setTitle('Rotational Displacement', size='')
        p.setLabel('left', "Angle [rad]")
        p.setMenuEnabled(enableMenu=True)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)

        self.makeRoiPlotLegend(self.rdLabel, self.names[3:6], config.PLOT_PEN_COLORS[3:6])

        self._plot_fd = pg.PlotWidget(self)
        self._plot_fd.setBackground((255, 255, 255))
        self.fdPlot.addWidget(self._plot_fd)

        p = self._plot_fd.getPlotItem()
        p.setTitle('Framewise Displacement', size='')
        p.setLabel('left', "FD [mm]")
        p.setMenuEnabled(enableMenu=True)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)
        names = ['FD']
        pens = [config.PLOT_PEN_COLORS[0]]
        for i in range(len(config.DEFAULT_FD_THRESHOLDS)):
            names.append('Threshold ' + str(i))
            pens.append(config.PLOT_PEN_COLORS[i + 1])

        self.makeRoiPlotLegend(self.fdLabel, names, pens)

        self._plot_mc = pg.PlotWidget(self)
        self._plot_mc.setBackground((255, 255, 255))
        self.mcPlot.addWidget(self._plot_mc)
        p = self._plot_mc.getPlotItem()
        p.setTitle('Head Displacement', size='')
        p.setLabel('left', "Amplitude [a.u.]")
        p.setMenuEnabled(enableMenu=True)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)

        self.makeRoiPlotLegend(self.mcLabel, self.names[0:6], config.PLOT_PEN_COLORS[0:6])

        self.tsCheckBox.setChecked(True)

        self.means = dict.fromkeys(['meanRaw'])
        self.m2 = dict.fromkeys(['m2Raw'])
        self.variances = dict.fromkeys(['varRaw'])
        self.rSNR = dict.fromkeys(['snrRaw'])
        self.outputSamples = dict.fromkeys(['motCorrParam'])
        self.outputSamples['motCorrParam'] = list(matlab.double([[1e-05, 1e-05, 1e-05, 1e-05, 1e-05, 1e-05]]))

    def onComboboxChanged(self):

        state = self.comboBox.currentIndex()

        if state == 0:
            self.tsCheckBox.show()
            self.volumeCheckBox.show()
            self.smoothedCheckBox.show()

            return
        if state == 1:
            self.tsCheckBox.hide()
            self.volumeCheckBox.hide()
            self.smoothedCheckBox.hide()

            return
        if state == 2:
            return
        if state == 3:
            return
        if state == 4:
            return

    def makeRoiPlotLegend(self, label, names, pens):
        label.setText('')
        legendText = '<html><head/><body><p>Plot legend: '

        for n, c in zip(names, pens):
            cname = c.color().name()
            legendText += (
                    '<span style="font-weight:600;color:{};">'.format(cname) + '{}</span> '.format(n))

        legendText += '</p></body></html>'

        label.setText(legendText)

    def closeEvent(self, event):
        self.hide()
        event.accept()

    def dictInit(self, sz):
        self.means['meanRaw'] = np.zeros((sz, 0))
        self.m2['m2Raw'] = np.zeros((sz, 0))
        self.variances['varRaw'] = np.zeros((sz, 0))
        self.rSNR['snrRaw'] = np.zeros((sz, 0))

    def plot_snr(self, init):
        plotitem = self.snrplot.getPlotItem()
        data = np.array(self.rSNR["snrRaw"], ndmin=2)
        sz, l = data.shape
        x = np.arange(0, l, dtype=np.float64)

        if init:
            plotitem.clear()
            plots = []

            for i, c in zip(range(sz), config.ROI_PLOT_COLORS):
                pen = pg.mkPen(color=c, width=config.ROI_PLOT_WIDTH)
                p = plotitem.plot(pen=pen)
                plots.append(p)

            self.plot_snr.__dict__[plotitem] = plots

        for p, y in zip(self.plot_snr.__dict__[plotitem], data):
            p.setData(x=x, y=np.array(y))

    def calculate_snr(self, init, data, iteration):
        sz = data.size
        snr = np.zeros((sz, 1))

        if init:
            self.dictInit(sz)
            mean = np.zeros((sz, 1))
            m2 = np.zeros((sz, 1))
            variance = np.zeros((sz, 1))
        else:
            mean = self.means["meanRaw"]
            m2 = self.m2["m2Raw"]
            variance = self.variances["varRaw"]

        n = iteration
        meanPrev = mean

        for i in range(sz):
            mean[i] = mean[i] + (data[i] - mean[i]) / n
            if n == 1:
                variance[i] = 0
            else:
                m2[i] = m2[i] + (data[i] - meanPrev[i]) * (data[i] - mean[i])
                variance[i] = m2[i] / (n - 1)
            if variance[i] == 0:
                snr[i] = 0
            else:
                snr[i] = mean[i] / variance[i] ** (.5)

        self.means["meanRaw"] = mean
        self.m2["m2Raw"] = m2
        self.variances["varRaw"] = variance
        if iteration < 8:
            snr = np.zeros((sz, 1))
        self.rSNR['snrRaw'] = np.append(self.rSNR['snrRaw'], snr, axis=1)

    def plot_fd(self, data):
        self.outputSamples['motCorrParam'].append(data)
        self._fd.draw_mc_plots(True, self.outputSamples, self._plot_translat, "tr")
        self._fd.draw_mc_plots(True, self.outputSamples, self._plot_rotat, "rot")
        self._fd.draw_mc_plots(True, self.outputSamples, self._plot_fd, "fd")
        self._fd.draw_mc_plots(True, self.outputSamples, self._plot_mc, "mc")
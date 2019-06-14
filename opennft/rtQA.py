# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rtQA.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

import numpy as np
import pyqtgraph as pg
import opennft.config as config
from opennft.rtQAUI import Ui_rtQA
from PyQt5 import QtGui, QtCore
from opennft.fdm_base import FD
import matlab
import opennft.fdm_settings as s

class rtQAWindow(QtGui.QMainWindow, Ui_rtQA):

    def __init__(self, xrange, parent=None, ):
        super(rtQAWindow, self).__init__(parent)
        self.setupUi(self)
        self._fd = FD()
        self.names = ['X','Y','Z','Pitch','Roll','Yaw', 'FD']

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
        self.makeRoiPlotLegend(self.tdLabel, self.names[0:3], s.PLOT_PEN_COLORS[0:3])

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
        self.makeRoiPlotLegend(self.rdLabel,  self.names[3:6], s.PLOT_PEN_COLORS[3:6])

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
        pens = [s.PLOT_PEN_COLORS[0]]
        for i in range(len(s.DEFAULT_FD_THRESHOLDS)):
            names.append('Threshold ' + str(i))
            pens.append(s.PLOT_PEN_COLORS[i+1])
        self.makeRoiPlotLegend(self.fdLabel, names, pens)

        self._plot_mc = pg.PlotWidget(self)
        self._plot_mc.setBackground((255, 255, 255))
        self.mcPlot.addWidget(self._plot_mc)
        p = self._plot_mc.getPlotItem()
        p.setTitle('MC', size='')
        p.setLabel('left', "Amplitude [a.u.]")
        p.setMenuEnabled(enableMenu=True)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)
        self.makeRoiPlotLegend(self.mcLabel, self.names[0:6], s.PLOT_PEN_COLORS[0:6])

        self._plot_mc.hide()
        self._plot_fd.hide()
        self._plot_translat.hide()
        self._plot_rotat.hide()
        self.mcLabel.hide()
        self.fdLabel.hide()
        self.tdLabel.hide()
        self.rdLabel.hide()

        self.tsCheckBox.setChecked(True)

        self.setFixedSize(1450, 400)

        self.means = dict.fromkeys(['meanRaw'])
        self.m2 = dict.fromkeys(['m2Raw'])
        self.variances = dict.fromkeys(['varRaw'])
        self.rSNR = dict.fromkeys(['snrRaw'])
        self.outputSamples = dict.fromkeys(['motCorrParam'])
        self.outputSamples['motCorrParam'] = list(matlab.double([[1e-05,1e-05,1e-05,1e-05,1e-05,1e-05]]))

    def onComboboxChanged(self):

        state = self.comboBox.currentIndex()

        if state == 0:
            self._plot_mc.hide()
            self._plot_fd.hide()
            self._plot_translat.hide()
            self._plot_rotat.hide()

            self.mcLabel.hide()
            self.fdLabel.hide()
            self.tdLabel.hide()
            self.rdLabel.hide()

            self.snrplot.show()

            self.tsCheckBox.show()
            self.tsCheckBox.setChecked(True)
            self.volumeCheckBox.show()
            self.volumeCheckBox.setChecked(False)
            self.smoothedCheckBox.show()
            self.smoothedCheckBox.setChecked(False)

            self.setFixedSize(1450, 400)

            return
        if state == 1:
            self._plot_mc.show()
            self._plot_fd.show()
            self._plot_translat.show()
            self._plot_rotat.show()

            self.mcLabel.show()
            self.fdLabel.show()
            self.tdLabel.show()
            self.rdLabel.show()

            self.snrplot.hide()

            self.tsCheckBox.hide()
            self.tsCheckBox.setChecked(False)
            self.volumeCheckBox.hide()
            self.volumeCheckBox.setChecked(False)
            self.smoothedCheckBox.hide()
            self.smoothedCheckBox.setChecked(False)

            self.mcLabel.move(140, 10)
            self.fdLabel.move(140, 270)
            self.tdLabel.move(790, 10)
            self.rdLabel.move(790, 270)

            self.layoutWidget_4.setGeometry(QtCore.QRect(140, 32, 641, 231))
            self.layoutWidget_5.setGeometry(QtCore.QRect(140, 292, 641, 231))
            self.layoutWidget_2.setGeometry(QtCore.QRect(790, 32, 641, 231))
            self.layoutWidget_3.setGeometry(QtCore.QRect(790, 292, 641, 231))

            self.setFixedSize(1450, 530)

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
                '<span style="font-weight:600;color:{};">'.format(cname)+ '{}</span> '.format(n))

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

    def plotSNR(self, init):

        plotitem = self.snrplot.getPlotItem()
        data = np.array(self.rSNR["snrRaw"], ndmin=2)
        sz, l = data.shape
        x = np.arange(0, l , dtype=np.float64)

        if init:
            plotitem.clear()
            plots = []

            for i, c in zip(range(sz), config.ROI_PLOT_COLORS):
                pen = pg.mkPen(color=c, width=config.ROI_PLOT_WIDTH)
                p = plotitem.plot(pen=pen)
                plots.append(p)

            self.plotSNR.__dict__[plotitem] = plots

        for p, y in zip(self.plotSNR.__dict__[plotitem], data):
            p.setData(x=x, y=np.array(y))


    def calcSNR(self, init, data, iteration):

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
        meanPrev = mean;
        for i in range(sz):
            mean[i] = mean[i] + (data[i] - mean[i]) / n
            if n == 1:
                variance[i] = 0
            else:
                m2[i] = m2[i] + (data[i] - meanPrev[i])*(data[i] - mean[i])
                variance[i] = m2[i] / (n-1)
            if variance[i] == 0:
                snr[i] = 0
            else:
                snr[i] = mean[i] / variance[i] ** (.5)

        self.means["meanRaw"] = mean
        self.m2["m2Raw"] = m2
        self.variances["varRaw"] = variance
        if iteration<8:
            snr = np.zeros((sz, 1))
        self.rSNR['snrRaw'] = np.append(self.rSNR['snrRaw'], snr, axis=1)

    def fdPlots(self, data):
        self.outputSamples['motCorrParam'].append(data)
        self._fd.draw_mc_plots(True, self.outputSamples, self._plot_translat, "tr")
        self._fd.draw_mc_plots(True, self.outputSamples, self._plot_rotat, "rot")
        self._fd.draw_mc_plots(True, self.outputSamples, self._plot_fd, "fd")
        self._fd.draw_mc_plots(True, self.outputSamples, self._plot_mc, "mc")



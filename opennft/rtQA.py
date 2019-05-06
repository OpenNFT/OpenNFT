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
from PyQt5 import QtGui


class rtQAWindow(QtGui.QMainWindow, Ui_rtQA):

    def __init__(self, parent=None):
        super(rtQAWindow, self).__init__(parent)
        self.setupUi(self)

        self.snrplot = pg.PlotWidget(self)
        self.snrplot.setBackground((255, 255, 255))
        self.layoutPlot1.addWidget(self.snrplot)
        p = self.snrplot.getPlotItem()
        p.setTitle('Signal-Noise Ratio', size='')
        p.setLabel('left', "Amplitude [a.u.]")
        p.setMenuEnabled(enableMenu=False)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)

        self.means = dict.fromkeys(['meanRaw', 'meanProcessed']);
        self.m2 = dict.fromkeys(['m2Raw'])
        self.variances = dict.fromkeys(['varRaw', 'varProcessed']);
        self.rSNR = dict.fromkeys(['snrRaw', 'snrProcessed'])

    def closeEvent(self, event):
        self.hide()
        event.accept()

    def dictInit(self, sz, key):
        self.means['mean'+key] = np.zeros((sz, 0))
        self.m2['m2'+key] = np.zeros((sz, 0))
        self.variances['var'+key] = np.zeros((sz, 0))
        self.rSNR['snr'+key] = np.zeros((sz, 0))

    def plotSNR(self, init):

        plotitem = self.snrplot.getPlotItem()
        key = str(self.comboBox.currentText())
        data = np.array(self.rSNR["snr" + key], ndmin=2)
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

        items = plotitem.listDataItems()

        plotitem.autoRange(items=items)

    def calcSNR(self, init, data, key, iteration):

        sz = data.size
        snr = np.zeros((sz, 1))

        if init:
            self.dictInit(sz, key)
            mean = np.zeros((sz, 1))
            m2 = np.zeros((sz, 1))
            variance = np.zeros((sz, 1))
        else:
            mean = self.means["mean" + key]
            m2 = self.m2["m2" + key]
            variance = self.variances["var" + key]

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

        self.means["mean" + key] = mean
        self.m2["m2" + key] = m2
        self.variances["var" + key] = variance
        if iteration<8:
            snr = np.zeros((sz, 1))
        self.rSNR['snr'+key] = np.append(self.rSNR['snr'+key], snr, axis=1)



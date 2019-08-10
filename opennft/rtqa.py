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

    def __init__(self, xrange, indBas, indCond, parent=None):
        super().__init__(parent=parent, flags=QtCore.Qt.Window)

        uic.loadUi(utils.get_ui_file('rtqa.ui'), self)

        self._fd = FD(xrange)
        self.names = ['X', 'Y', 'Z', 'Pitch', 'Roll', 'Yaw', 'FD']
        self.indBas = indBas
        self.indCond = indCond
        self.iterBas = 1
        self.iterCond = 1

        self.comboBox.currentTextChanged.connect(self.onComboboxChanged)
        self.mcrRadioButton.toggled.connect(self.onRadioButtonStateChanged)

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

        self.cnrplot = pg.PlotWidget(self)
        self.cnrplot.setBackground((255, 255, 255))
        self.cnrPlot.addWidget(self.cnrplot)

        p = self.cnrplot.getPlotItem()
        p.setTitle('Contrast-Noise Ratio', size='')
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
        p.setLabel('left', "Amplitude [mm]")
        p.setMenuEnabled(enableMenu=True)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)
        names = ['Translationals: ']
        pens = [config.PLOT_PEN_COLORS[6]]
        for i in range(3):
            names.append(self.names[i])
            pens.append(config.PLOT_PEN_COLORS[i])

        self.makeRoiPlotLegend(self.tdLabel, names, pens)

        self._plot_rotat = pg.PlotWidget(self)
        self._plot_rotat.setBackground((255, 255, 255))
        self.rdPlot.addWidget(self._plot_rotat)

        p = self._plot_rotat.getPlotItem()
        p.setLabel('left', "Angle [rad]")
        p.setMenuEnabled(enableMenu=True)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)
        names = ['Rotations: ']
        pens = [config.PLOT_PEN_COLORS[6]]
        for i in range(3):
            names.append(self.names[i+3])
            pens.append(config.PLOT_PEN_COLORS[i + 3])

        self.makeRoiPlotLegend(self.rdLabel, names, pens)

        self._plot_fd = pg.PlotWidget(self)
        self._plot_fd.setBackground((255, 255, 255))
        self.fdPlot.addWidget(self._plot_fd)

        p = self._plot_fd.getPlotItem()
        p.setLabel('left', "FD [mm]")
        p.setMenuEnabled(enableMenu=True)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)
        names = ['Framewise Displacement']
        pens = [config.PLOT_PEN_COLORS[0]]
        for i in range(len(config.DEFAULT_FD_THRESHOLDS)-1):
            names.append('Threshold ' + str(i+1))
            pens.append(config.PLOT_PEN_COLORS[i + 1])

        self.makeRoiPlotLegend(self.fdLabel, names, pens)

        self.tsCheckBox.setChecked(True)

        self.means = dict.fromkeys(['meanRaw'])
        self.m2 = dict.fromkeys(['m2Raw'])
        self.variances = dict.fromkeys(['varRaw'])
        self.rSNR = dict.fromkeys(['snrRaw'])
        self.meanBas = np.array(0)
        self.m2Bas = np.array(0)
        self.meanCond = np.array(0)
        self.m2Cond = np.array(0)
        self.rCNR = np.array(0)

    def onComboboxChanged(self):

        state = self.comboBox.currentIndex()

        if state == 0:
            return
        if state == 1:
            return
        if state == 2:
            self.stackedWidgetOptions.setCurrentIndex(0);
            return
        if state == 3:
            return
        if state == 4:
            return

    def onRadioButtonStateChanged(self):

        if self.mcrRadioButton.isChecked():
            names = ['Micro Displacement']
            pens = [config.PLOT_PEN_COLORS[0]]
            names.append('Threshold')
            pens.append(config.PLOT_PEN_COLORS[2])

            self.makeRoiPlotLegend(self.fdLabel, names, pens)
        else:
            names = ['Framewise Displacement']
            pens = [config.PLOT_PEN_COLORS[0]]
            for i in range(len(config.DEFAULT_FD_THRESHOLDS)-1):
                names.append('Threshold ' + str(i+1))
                pens.append(config.PLOT_PEN_COLORS[i + 1])

            self.makeRoiPlotLegend(self.fdLabel, names, pens)

    def makeRoiPlotLegend(self, label, names, pens):
        label.setText('')
        legendText = '<html><head/><body><p>'

        for n, c in zip(names, pens):
            cname = c.color().name()
            legendText += (
                    '<span style="font-weight:600;color:{};">'.format(cname) + '{}</span> '.format(n))

        legendText += '</p></body></html>'

        label.setText(legendText)

    def makeTextValueLabel(self, label, names, pens):

        label.setText('')
        text = '<html><head/><body><p>'
        for n, c in zip(names, pens):
            cname = c.color().name()
            text += (
                    '<span style="font-weight:600;color:{};">'.format(cname) + '{}</span><br>'.format(n))

        text += '</p></body></html>'

        label.setText(text)

    def closeEvent(self, event):
        self.hide()
        event.accept()

    def dictInit(self, sz):
        self.means['meanRaw'] = np.zeros((sz, 0))
        self.m2['m2Raw'] = np.zeros((sz, 0))
        self.variances['varRaw'] = np.zeros((sz, 0))
        self.rSNR['snrRaw'] = np.zeros((sz, 0))
        self.rCNR = np.zeros((sz, self._fd.xmax+1))

    def plot_ts(self, plotitem, data):

        if self.tsCheckBox.isChecked():

            sz, l = data.shape
            x = np.arange(0, l, dtype=np.float64)

            plotitem.clear()
            plots = []

            for i, c in zip(range(sz), config.ROI_PLOT_COLORS):
                pen = pg.mkPen(color=c, width=config.ROI_PLOT_WIDTH)
                p = plotitem.plot(pen=pen)
                plots.append(p)

            self.plot_ts.__dict__[plotitem] = plots

            for p, y in zip(self.plot_ts.__dict__[plotitem], data):
                p.setData(x=x, y=np.array(y))

    def plot_rtQA(self):

        plotitem = self.snrplot.getPlotItem()
        data = np.array(self.rSNR["snrRaw"], ndmin=2)
        self.plot_ts(plotitem,data)

        plotitem = self.cnrplot.getPlotItem()
        data = np.array(self.rCNR[:, 0:len(self.rSNR["snrRaw"][0])], ndmin=2)
        self.plot_ts(plotitem,data)

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
                snr[i] = mean[i] / (variance[i] ** (.5))

        self.means["meanRaw"] = mean
        self.m2["m2Raw"] = m2
        self.variances["varRaw"] = variance
        if iteration < 8:
            snr = np.zeros((sz, 1))
        self.rSNR['snrRaw'] = np.append(self.rSNR['snrRaw'], snr, axis=1)

        if not self.comboBox.currentIndex():

            names = ['SNR ']
            pens = [config.PLOT_PEN_COLORS[6]]
            for i in range(sz):
                names.append('ROI_' + str(i + 1) + ' ' + '{0:.3f}'.format(float(snr[i])))
                pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))

            self.makeTextValueLabel(self.valuesLabel, names, pens)

    def calculate_cnr(self, data, indexVolume):

        sz = data.size

        if indexVolume in self.indBas:
            if not self.meanBas.any():
                self.meanBas = data
                self.m2Bas = np.zeros((sz, 1))
                return

            meanPrev = self.meanBas
            self.iterBas+=1

            for i in range(sz):
                self.meanBas[i] = self.meanBas[i] + (data[i] - self.meanBas[i]) / self.iterBas
                self.m2Bas[i] = self.m2Bas[i] + (data[i] - meanPrev[i]) * (data[i] - self.meanBas[i])

        if indexVolume in self.indCond:
            if not self.meanCond.any():
                self.meanCond = data
                self.m2Cond = np.zeros((sz, 1))
                return

            meanPrev = self.meanCond
            self.iterCond+=1

            for i in range(sz):
                self.meanCond[i] = self.meanCond[i] + (data[i] - self.meanCond[i]) / self.iterCond
                self.m2Cond[i] = self.m2Cond[i] + (data[i] - meanPrev[i]) * (data[i] - self.meanCond[i])

        if self.meanCond.any():

            for i in range(sz):
                varBas = self.m2Bas[i] / (self.iterBas - 1)
                varCond = self.m2Cond[i] / (self.iterCond - 1)
                self.rCNR[i][indexVolume] = (self.meanCond[i] - self.meanBas[i]) / ((varCond + varBas) ** (.5))

            if self.comboBox.currentIndex()==2:
                names = ['СNR ']
                pens = [config.PLOT_PEN_COLORS[6]]
                for i in range(sz):
                    names.append('ROI_' + str(i + 1) + ' ' + '{0:.3f}'.format(float(self.rCNR[i][indexVolume])))
                    pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))

                self.makeTextValueLabel(self.valuesLabel, names, pens)

    def plot_mcmd(self, data):
        self._fd.draw_mc_plots(data, self.mcrRadioButton.isChecked(), self._plot_translat, self._plot_rotat, self._plot_fd)
        names = ['Framewise displacement ']
        pens = [config.PLOT_PEN_COLORS[6]]
        names.append('Exceed threshold 1: ' + str(int(self._fd.excFD[0])))
        pens.append(config.PLOT_PEN_COLORS[1])
        names.append('Exceed threshold 2: ' + str(int(self._fd.excFD[1])))
        pens.append(config.PLOT_PEN_COLORS[2])
        names.append('Micro displacement ')
        pens.append(config.PLOT_PEN_COLORS[6])
        names.append('Exceed threshold: ' + str(int(self._fd.excVD)))
        pens.append(config.PLOT_PEN_COLORS[2])
        names.append('Mean framewise displacement ')
        pens.append(config.PLOT_PEN_COLORS[6])
        names.append('{0:.3f}'.format(self._fd.meanFD))
        pens.append(config.PLOT_PEN_COLORS[6])
        self.makeTextValueLabel(self.mcmdValuesLabel, names, pens)

    def data_packing(self):

        tsRTQA = dict.fromkeys(['meanSNR', 'm2SNR', 'rSNR',
                                'meanBas', 'm2Bas', 'meanCond', 'm2Cond', 'rCNR',
                                'excFDIndexes', 'excVDIndexes'])

        tsRTQA['meanSNR'] = matlab.double(self.means['meanRaw'].tolist())
        tsRTQA['m2SNR'] = matlab.double(self.m2['m2Raw'].tolist())
        tsRTQA['rSNR'] = matlab.double(self.rSNR['snrRaw'].tolist())
        tsRTQA['meanBas'] = matlab.double(self.meanBas.tolist())
        tsRTQA['m2Bas'] = matlab.double(self.m2Bas.tolist())
        tsRTQA['meanCond'] = matlab.double(self.meanCond.tolist())
        tsRTQA['m2Cond'] = matlab.double(self.m2Cond.tolist())
        tsRTQA['rCNR'] = matlab.double(self.rCNR.tolist())
        tsRTQA['excFDIndexes'] = matlab.double(self._fd.excFDIndexes.tolist())
        tsRTQA['excVDIndexes'] = matlab.double(self._fd.excVDIndexes.tolist())

        return tsRTQA
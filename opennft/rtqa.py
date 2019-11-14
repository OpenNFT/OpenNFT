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

    def __init__(self, sz, xrange, indBas, indCond, musterInfo, parent=None):
        super().__init__(parent=parent, flags=QtCore.Qt.Window)

        uic.loadUi(utils.get_ui_file('rtqa.ui'), self)

        self._fd = FD(xrange)
        self.names = ['X', 'Y', 'Z', 'Pitch', 'Roll', 'Yaw', 'FD']
        self.indBas = indBas
        self.indCond = indCond
        self.iterBas = 0
        self.iterCond = 0

        self.musterInfo = musterInfo

        self.comboBox.currentTextChanged.connect(self.onComboboxChanged)
        self.mcrRadioButton.toggled.connect(self.onRadioButtonStateChanged)

        self.snrplot = pg.PlotWidget(self)
        self.snrplot.setBackground((255, 255, 255))
        self.snrPlot.addWidget(self.snrplot)

        p = self.snrplot.getPlotItem()
        p.setLabel('left', "SNR [a.u.]")
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
        p.setLabel('left', "CNR [a.u.]")
        p.setMenuEnabled(enableMenu=False)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)

        self.meanplot = pg.PlotWidget(self)
        self.meanplot.setBackground((255, 255, 255))
        self.meanPlot.addWidget(self.meanplot)

        p = self.meanplot.getPlotItem()
        p.setLabel('left', "Mean [a.u.]")
        p.setMenuEnabled(enableMenu=False)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)

        names = ['ROI_1 rMean', 'ROI_1 basMean', 'ROI_1 condMean']
        color = [config.STAT_PLOT_COLORS[0], config.ROI_BAS_COLORS[0], config.ROI_COND_COLORS[0]]
        for i in range(sz-1):
            names.append('ROI_' + str(i + 2) + ' rMean')
            names.append('ROI_' + str(i + 2) + ' basMean')
            names.append('ROI_' + str(i + 2) + ' condMean')
            color = color + [config.STAT_PLOT_COLORS[i + 1]] + [config.ROI_BAS_COLORS[i + 1]] + [config.ROI_COND_COLORS[i + 1]]
        pens = []
        for i in range(sz*3):
            pens = pens + [pg.mkPen(color[i], width=1.2)]
        self.makeRoiPlotLegend(self.labelMean, names, pens)

        self.varplot = pg.PlotWidget(self)
        self.varplot.setBackground((255, 255, 255))
        self.varPlot.addWidget(self.varplot)

        p = self.varplot.getPlotItem()
        p.setLabel('left', "Variance [a.u.]")
        p.setMenuEnabled(enableMenu=False)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)

        names = ['ROI_1 rVariance', 'ROI_1 basVariance', 'ROI_1 condVariance']
        for i in range(sz - 1):
            names.append('ROI_' + str(i + 2) + ' rVariance')
            names.append('ROI_' + str(i + 2) + ' basVariance')
            names.append('ROI_' + str(i + 2) + ' condVariance')
        self.makeRoiPlotLegend(self.labelVar, names, pens)

        self.spikes_plot = pg.PlotWidget(self)
        self.spikes_plot.setBackground((255, 255, 255))
        self.spikesPlot.addWidget(self.spikes_plot)

        p = self.spikes_plot.getPlotItem()
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

        self.iteration = 1;
        self.rMean = np.zeros((sz, xrange))
        self.m2 = np.zeros((sz, 1))
        self.rVar = np.zeros((sz, xrange))
        self.rSNR = np.zeros((sz, xrange))
        self.meanBas = np.zeros((sz, xrange))
        self.varBas = np.zeros((sz, xrange))
        self.m2Bas = np.zeros((sz, 1))
        self.meanCond = np.zeros((sz, xrange))
        self.varCond = np.zeros((sz, xrange))
        self.m2Cond = np.zeros((sz, 1))
        self.rCNR = np.zeros((sz, xrange))
        self.glmProcTimeSeries = np.zeros((sz, 1))
        self.posSpikes = dict.fromkeys(['{:d}'.format(x) for x in range(sz)], np.array(0))
        self.negSpikes = dict.fromkeys(['{:d}'.format(x) for x in range(sz)], np.array(0))

    def onComboboxChanged(self):

        state = self.comboBox.currentIndex()

        if state == 0:

            names = ['SNR ']
            pens = [config.PLOT_PEN_COLORS[6]]
            sz = len(self.rSNR)
            for i in range(sz):
                names.append('ROI_' + str(i + 1) + ':  ' + '{0:.3f}'.format(float(self.rSNR[i][self.iteration])))
                pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))

            self.makeTextValueLabel(self.valuesLabel, names, pens)

            return
        if state == 1:
            return
        if state == 2:
            self.stackedWidgetOptions.setCurrentIndex(0);

            names = ['СNR ']
            pens = [config.PLOT_PEN_COLORS[6]]
            sz = len(self.rCNR)
            for i in range(sz):
                names.append('ROI_' + str(i + 1) + ':  ' + '{0:.3f}'.format(float(self.rCNR[i][self.iteration])))
                pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))

            self.makeTextValueLabel(self.valuesLabel, names, pens)

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

        self._fd.draw_mc_plots(self.mcrRadioButton.isChecked(), self._plot_translat, self._plot_rotat, self._plot_fd)

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

    def plot_ts(self, init, plotitem, data):

        if self.tsCheckBox.isChecked():

            sz, l = data.shape

            if init:

                plotitem.clear()
                plots = []

                muster = self.drawMusterPlot(plotitem)

                for i, c in zip(range(sz), config.ROI_PLOT_COLORS):
                    pen = pg.mkPen(color=c, width=config.ROI_PLOT_WIDTH)
                    p = plotitem.plot(pen=pen)
                    plots.append(p)

                self.plot_ts.__dict__[plotitem] = plots, muster

            x = np.arange(1, l+1, dtype=np.float64)

            for p, y in zip(self.plot_ts.__dict__[plotitem][0], data):
                p.setData(x=x, y=np.array(y))

            items = plotitem.listDataItems()

            for m in self.plot_ts.__dict__[plotitem][1]:
                items.remove(m)

            if data.any():
                plotitem.setYRange(np.min(data), np.max(data), padding=0.0)

    def plot_rtQA(self, init, n):

        plotitem = self.snrplot.getPlotItem()
        data = self.rSNR[:, 0:n]
        self.plot_ts(init, plotitem, data)

        plotitem = self.cnrplot.getPlotItem()
        data = self.rCNR[:, 0:n]
        self.plot_ts(init, plotitem, data)

        plotitem = self.meanplot.getPlotItem()
        data = np.append(self.rMean[:, 0:n], self.meanBas[:, 0:n], axis=0)
        data = np.append(data, self.meanCond[:, 0:n], axis=0)
        m = len(self.rSNR[:, 1])
        color = config.STAT_PLOT_COLORS[0:m] + config.ROI_BAS_COLORS[0:m] + config.ROI_COND_COLORS[0:m]
        style = [QtCore.Qt.SolidLine, QtCore.Qt.DashLine, QtCore.Qt.DashLine]
        self.plot_rStatValues(init, plotitem, data, color, style)

        plotitem = self.varplot.getPlotItem()
        data = np.append(self.rVar[:, 0:n], self.varBas[:, 0:n], axis=0)
        data = np.append(data, self.varCond[:, 0:n], axis=0)
        self.plot_rStatValues(init, plotitem, data, color, style)

    def plot_rStatValues(self, init, plotitem, data, color, style):

        if self.tsCheckBox.isChecked():

            sz, l = data.shape

            if init:

                plotitem.clear()
                plots = []

                muster = self.drawMusterPlot(plotitem)

                style = np.repeat(style, sz/3)

                for i, c, s in zip(range(sz), color, style):
                    pen = pg.mkPen(c, width=3.0, style=QtCore.Qt.PenStyle(s))
                    p = plotitem.plot(pen=pen)
                    plots.append(p)

                self.plot_ts.__dict__[plotitem] = plots, muster

            x = np.arange(1, l+1, dtype=np.float64)

            for p, y in zip(self.plot_ts.__dict__[plotitem][0], data):
                p.setData(x=x, y=np.array(y))

            items = plotitem.listDataItems()

            for m in self.plot_ts.__dict__[plotitem][1]:
                items.remove(m)

            if data.any():
                plotitem.setYRange(np.min(data[np.nonzero(data)]), np.max(data), padding=0.0)

    def drawMusterPlot(self, plotitem):
        ylim = config.MUSTER_Y_LIMITS

        if self.comboBox.model().item(2).isEnabled():
            muster = [
                plotitem.plot(x=self.musterInfo['xCond1'],
                              y=self.musterInfo['yCond1'],
                              fillLevel=ylim[0],
                              pen=config.MUSTER_PEN_COLORS[0],
                              brush=config.MUSTER_BRUSH_COLORS[0]),

                plotitem.plot(x=self.musterInfo['xCond2'],
                              y=self.musterInfo['yCond2'],
                              fillLevel=ylim[0],
                              pen=config.MUSTER_PEN_COLORS[1],
                              brush=config.MUSTER_BRUSH_COLORS[1]),
            ]

            if self.musterInfo['xCond3'][0] == -1:
                muster.append(
                    plotitem.plot(x=self.musterInfo['xCond3'],
                                  y=self.musterInfo['yCond3'],
                                  fillLevel=ylim[0],
                                  pen=config.MUSTER_PEN_COLORS[2],
                                  brush=config.MUSTER_BRUSH_COLORS[2])
                )
        else:
            muster = [
                plotitem.plot(x=[1, self._fd.xmax],
                              y=[-1000, 1000],
                              fillLevel=ylim[0],
                              pen=config.MUSTER_PEN_COLORS[3],
                              brush=config.MUSTER_BRUSH_COLORS[3])
            ]

        return muster

    def calculate_snr(self, data, iteration):
        sz = data.size
        snr = np.zeros((sz, 1))
        n = iteration

        variance = self.rVar[:, n-1]
        mean = self.rMean[:, n-1]
        m2 = self.m2

        meanPrev = mean

        if n:

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

        else:

            mean = data

        self.rMean[:, n] = mean
        self.m2 = m2
        self.rVar[:, n] = variance
        if iteration < 8:
            snr = np.zeros((sz, 1))
        for i in range(sz):
            self.rSNR[i][n] = snr[i]

        if not self.comboBox.currentIndex():

            names = ['SNR ']
            pens = [config.PLOT_PEN_COLORS[6]]
            for i in range(sz):
                names.append('ROI_' + str(i + 1) + ': ' + '{0:.3f}'.format(float(snr[i])))
                pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))

            self.makeTextValueLabel(self.valuesLabel, names, pens)

        self.iteration = n;

    def calculate_cnr(self, data, indexVolume):

        sz = data.size

        if indexVolume in self.indBas:
            if not self.iterBas:
                self.meanBas[:, indexVolume] = data
                self.varBas[:, indexVolume] = np.zeros(sz)
                self.iterBas += 1

            else:

                self.iterBas += 1

                for i in range(sz):
                    self.meanBas[i, indexVolume] = self.meanBas[i, indexVolume-1] + (data[i] - self.meanBas[i,indexVolume-1]) / self.iterBas
                    self.m2Bas[i] = self.m2Bas[i] + (data[i] - self.meanBas[i, indexVolume-1]) * (data[i] - self.meanBas[i, indexVolume])
                    self.varBas[i, indexVolume] = self.m2Bas[i] / (self.iterBas - 1)

        else:

            self.meanBas[:, indexVolume] = self.meanBas[:, indexVolume-1]
            self.varBas[:, indexVolume] = self.varBas[:, indexVolume-1]

        if indexVolume in self.indCond:

            if not self.iterCond:
                self.meanCond[:, indexVolume] = data
                self.varCond[:, indexVolume] = np.zeros(sz)
                self.iterCond += 1

            else:

                self.iterCond += 1

                for i in range(sz):
                    self.meanCond[i, indexVolume] = self.meanCond[i, indexVolume-1] + (data[i] - self.meanCond[i, indexVolume-1]) / self.iterCond
                    self.m2Cond[i] = self.m2Cond[i] + (data[i] - self.meanCond[i, indexVolume-1]) * (data[i] - self.meanCond[i, indexVolume])
                    self.varCond[i, indexVolume] = self.m2Cond[i] / (self.iterCond - 1)

        else:

            self.meanCond[:, indexVolume] = self.meanCond[:, indexVolume - 1]
            self.varCond[:, indexVolume] = self.varCond[:, indexVolume - 1]

        if self.iterCond:

            for i in range(sz):
                self.rCNR[i, indexVolume] = (self.meanCond[i, indexVolume] - self.meanBas[i, indexVolume]) / (np.sqrt(self.varCond[i, indexVolume] + self.varBas[i, indexVolume]))

            if self.comboBox.currentIndex() == 2:

                names = ['СNR ']
                pens = [config.PLOT_PEN_COLORS[6]]
                for i in range(sz):
                    names.append('ROI_' + str(i + 1) + ': ' + '{0:.3f}'.format(float(self.rCNR[i][indexVolume-1])))
                    pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))

                self.makeTextValueLabel(self.valuesLabel, names, pens)

    def plot_mcmd(self, data):

        self._fd.calc_mc_plots(data)
        self._fd.draw_mc_plots(self.mcrRadioButton.isChecked(), self._plot_translat, self._plot_rotat, self._plot_fd)
        names = ['<u>FD</u> ']
        pens = [config.PLOT_PEN_COLORS[6]]
        names.append('Threshold 1: ' + str(int(self._fd.excFD[0])))
        pens.append(config.PLOT_PEN_COLORS[1])
        names.append('Threshold 2: ' + str(int(self._fd.excFD[1])))
        pens.append(config.PLOT_PEN_COLORS[2])
        names.append('<br><u>MD</u> ')
        pens.append(config.PLOT_PEN_COLORS[6])
        names.append('Threshold: ' + str(int(self._fd.excVD)))
        pens.append(config.PLOT_PEN_COLORS[2])
        names.append('<br><u>Mean FD</u> ')
        pens.append(config.PLOT_PEN_COLORS[6])
        names.append('{0:.3f}'.format(self._fd.meanFD))
        pens.append(config.PLOT_PEN_COLORS[6])
        names.append('<br><u>Mean MD</u> ')
        pens.append(config.PLOT_PEN_COLORS[6])
        names.append('{0:.3f}'.format(self._fd.meanMD))
        pens.append(config.PLOT_PEN_COLORS[6])
        self.makeTextValueLabel(self.mcmdValuesLabel, names, pens)

    def plot_stepsAndSpikes(self, data, posSpike, negSpike):

        self.glmProcTimeSeries = np.append(self.glmProcTimeSeries, data, axis=1)
        sz, l = self.glmProcTimeSeries.shape

        for i in range(sz):
            if posSpike[i] == 1:
                if self.posSpikes[str(i)].any():
                    self.posSpikes[str(i)] = np.append(self.posSpikes[str(i)], l-1)
                else:
                    self.posSpikes[str(i)] = np.array([l-1])
            if negSpike[i] == 1:
                if self.negSpikes[str(i)].any():
                    self.negSpikes[str(i)] = np.append(self.negSpikes[str(i)], l-1)
                else:
                    self.negSpikes[str(i)] = np.array([l-1])

        x = np.arange(0, l, dtype=np.float64)

        plotitem = self.spikes_plot.getPlotItem()
        plotitem.clear()
        plots = []

        muster = self.drawMusterPlot(plotitem)

        for i, c in zip(range(sz), config.ROI_PLOT_COLORS):
            pen = pg.mkPen(color=c, width=config.ROI_PLOT_WIDTH)
            p = plotitem.plot(pen=pen)
            plots.append(p)

        self.plot_stepsAndSpikes.__dict__[plotitem] = plots, muster

        for p, y in zip(self.plot_stepsAndSpikes.__dict__[plotitem][0], self.glmProcTimeSeries):
            p.setData(x=x, y=np.array(y))

        for i, c in zip(range(sz), config.ROI_PLOT_COLORS):

            if self.posSpikes[str(i)].any():
                brush = pg.mkBrush(color=c)
                p = plotitem.scatterPlot(symbol='o', size=20, brush=brush)
                plots.append(p)
                plots[-1].setData(x=x[self.posSpikes[str(i)]], y=self.glmProcTimeSeries[i, self.posSpikes[str(i)]])

                pen = pg.mkPen(color=pg.mkColor(0, 0, 0), width=1.5*config.ROI_PLOT_WIDTH)
                p = plotitem.plot(pen=pen)
                plots.append(p)

                mask = np.zeros((l, 1))
                mask[self.posSpikes[str(i)]] = 1
                mask[self.posSpikes[str(i)]-1] = 1
                y = np.array(self.glmProcTimeSeries[i,:])
                y = y[np.where(mask == 1)[0]]
                x1 = x
                x1 = x1[np.where(mask == 1)[0]]

                plots[-1].setData(x=x1, y=y, connect='pairs')

            if self.negSpikes[str(i)].any():
                brush = pg.mkBrush(color=c)
                p = plotitem.scatterPlot(symbol='d', size=20, brush=brush)
                plots.append(p)
                plots[-1].setData(x=x[self.negSpikes[str(i)]], y=self.glmProcTimeSeries[i, self.negSpikes[str(i)]])

                pen = pg.mkPen(color=pg.mkColor(0, 0, 0), width=1.5*config.ROI_PLOT_WIDTH)
                p = plotitem.plot(pen=pen)
                plots.append(p)

                mask = np.zeros((l, 1))
                mask[self.negSpikes[str(i)]] = 1
                mask[self.negSpikes[str(i)]-1] = 1
                y = np.array(self.glmProcTimeSeries[i,:])
                y = y[np.where(mask == 1)[0]]
                x1 = x
                x1 = x1[np.where(mask == 1)[0]]

                plots[-1].setData(x=x1, y=y, connect='pairs')

        cnt = 0;
        for i in range(sz):
            cnt = cnt + np.count_nonzero(self.posSpikes[str(i)])
        names = ['Positive spikes: ' + str(int(cnt))]

        cnt = 0;
        for i in range(sz):
            cnt = cnt + np.count_nonzero(self.negSpikes[str(i)])
        names.append('<br>Negative spikes: ' + str(int(cnt)))
        pens = [pg.mkPen(color=config.STAT_PLOT_COLORS[0], width=1.2), pg.mkPen(color=config.STAT_PLOT_COLORS[0], width=1.2)]
        self.makeTextValueLabel(self.spikesLabel, names, pens)

        items = plotitem.listDataItems()

        for m in self.plot_stepsAndSpikes.__dict__[plotitem][1]:
            items.remove(m)

        if data.any():
            plotitem.setYRange(np.min(self.glmProcTimeSeries), np.max(self.glmProcTimeSeries), padding=0.0)

    def data_packing(self):

        tsRTQA = dict.fromkeys(['rMean', 'rVar', 'rSNR',
                                'meanBas', 'varBas', 'meanCond', 'varCond', 'rCNR',
                                'excFDIndexes_1', 'excFDIndexes_2', 'excMDIndexes'])

        tsRTQA['rMean'] = matlab.double(self.rMean.tolist())
        tsRTQA['rVar'] = matlab.double(self.rVar.tolist())
        tsRTQA['rSNR'] = matlab.double(self.rSNR.tolist())
        tsRTQA['meanBas'] = matlab.double(self.meanBas.tolist())
        tsRTQA['varBas'] = matlab.double(self.varBas.tolist())
        tsRTQA['meanCond'] = matlab.double(self.meanCond.tolist())
        tsRTQA['varCond'] = matlab.double(self.varCond.tolist())
        tsRTQA['rCNR'] = matlab.double(self.rCNR.tolist())
        tsRTQA['excFDIndexes_1'] = matlab.double(self._fd.excFDIndexes_1.tolist())
        tsRTQA['excFDIndexes_2'] = matlab.double(self._fd.excFDIndexes_2.tolist())
        tsRTQA['excMDIndexes'] = matlab.double(self._fd.excMDIndexes.tolist())

        return tsRTQA
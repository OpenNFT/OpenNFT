# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import uic

import numpy as np
import pyqtgraph as pg
import matlab
import itertools

from opennft import utils
from opennft import config
from opennft.rtqa_fdm import FD


class RTQAWindow(QtWidgets.QWidget):
    """Real-time quality assessment GUI and methods application class
    """

    # --------------------------------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent=parent, flags=QtCore.Qt.Window)

        uic.loadUi(utils.get_ui_file('rtqa.ui'), self)

        # parent data transfer block
        sz = int(parent.P['NrROIs'])
        self.musterInfo = parent.musterInfo

        if parent.P['isRestingState']:
            xrange = (parent.P['NrOfVolumes'] - parent.P['nrSkipVol'])
            self.comboBox.model().item(2).setEnabled(False)
            self.indBas = 0
            self.indCond = 0
        else:
            lastInds = np.zeros((self.musterInfo['condTotal'],))
            for i in range(self.musterInfo['condTotal']):
                lastInds[i] = self.musterInfo['tmpCond' + str(i + 1)][-1][1]
            parent.computeMusterPlotData(config.MUSTER_Y_LIMITS)
            xrange = max(lastInds)
            self.indBas = np.array(parent.P['inds'][0]) - 1
            self.indCond = np.array(parent.P['inds'][1]) - 1

        xrange = int(xrange)

        # main class data initialization block
        self.prot = parent.P['Prot']
        self._fd = FD(xrange)
        self.names = ['X', 'Y', 'Z', 'Pitch', 'Roll', 'Yaw', 'FD']
        self.iterBas = 0
        self.iterCond = 0
        self.init = True
        self.isStopped = True
        self.iteration = 1
        self.blockIter = 0
        self.noRegBlockIter = 0
        self.rMean = np.zeros((sz, xrange))
        self.m2 = np.zeros((sz, 1))
        self.rVar = np.zeros((sz, xrange))
        self.rSNR = np.zeros((sz, xrange))
        self.rNoRegMean = np.zeros((sz, xrange))
        self.noRegM2 = np.zeros((sz, 1))
        self.rNoRegVar = np.zeros((sz, xrange))
        self.rNoRegSNR = np.zeros((sz, xrange))
        self.meanBas = np.zeros((sz, xrange))
        self.varBas = np.zeros((sz, xrange))
        self.m2Bas = np.zeros((sz, 1))
        self.meanCond = np.zeros((sz, xrange))
        self.varCond = np.zeros((sz, xrange))
        self.m2Cond = np.zeros((sz, 1))
        self.rCNR = np.zeros((sz, xrange))
        self.glmProcTimeSeries = np.zeros((sz, xrange))
        self.posSpikes = dict.fromkeys(['{:d}'.format(x) for x in range(sz)], np.array(0))
        self.negSpikes = dict.fromkeys(['{:d}'.format(x) for x in range(sz)], np.array(0))
        self.rMSE = np.zeros((sz, xrange))
        self.DVARS = np.zeros((0, 1))
        self.excDVARS = 0
        self.linTrendCoeff = np.zeros((sz, xrange))
        self.checkedBoxesInd = []
        self.currentMode = 0

        # Additional GUI elements connection and initialization
        groupBoxLayout = self.roiGroupBox.layout()
        for i in range(sz):
            if i == sz-1:
                name = 'Whole brain ROI'
            else:
                name = 'ROI_' + str(i + 1)
            checkbox = QtWidgets.QCheckBox(name)
            checkbox.setStyleSheet("color: " + config.ROI_PLOT_COLORS[i].name())
            if not i:
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.roiCheckBoxStateChanged)
            groupBoxLayout.addWidget(checkbox)
        self.roiCheckBoxes = self.roiGroupBox.findChildren(QtWidgets.QCheckBox)
        self.mcrRadioButton.toggled.connect(self.onRadioButtonStateChanged)

        # Plots initialization
        self.snrPlot = pg.PlotWidget(self)
        self.snrPlot.setBackground((255, 255, 255))
        self.snrPlotLayout.addWidget(self.snrPlot)
        p = self.snrPlot.getPlotItem()
        self.plotsSetup(p, "SNR [a.u.]", xrange)
        self.drawMusterPlot(p)
        p.setYRange(-1, 1, padding=0.0)

        self.noRegSnrPlot = pg.PlotWidget(self)
        self.noRegSnrPlot.setBackground((255, 255, 255))
        self.noRegSnrPlotLayout.addWidget(self.noRegSnrPlot)
        p = self.noRegSnrPlot.getPlotItem()
        self.plotsSetup(p, "SNR [a.u.]", xrange)
        self.drawMusterPlot(p)
        p.setYRange(-1, 1, padding=0.0)

        self.msePlot = pg.PlotWidget(self)
        self.msePlot.setBackground((255, 255, 255))
        self.msePlotLayout.addWidget(self.msePlot)
        p = self.msePlot.getPlotItem()
        self.plotsSetup(p, "Mean squared error [a.u.]", xrange)
        self.drawMusterPlot(p)
        p.setYRange(-1, 1, padding=0.0)

        self.trendPlot = pg.PlotWidget(self)
        self.trendPlot.setBackground((255, 255, 255))
        self.linearTreandPlotLayout.addWidget(self.trendPlot)
        p = self.trendPlot.getPlotItem()
        self.plotsSetup(p, "Beta regressor amplitude [a.u.]", xrange)
        self.drawMusterPlot(p)
        p.setYRange(-1, 1, padding=0.0)

        self.fdPlot = pg.PlotWidget(self)
        self.fdPlot.setBackground((255, 255, 255))
        self.fdPlotLayout.addWidget(self.fdPlot)
        p = self.fdPlot.getPlotItem()
        self.plotsSetup(p, "FD [mm]", xrange)

        self.translatPlot = pg.PlotWidget(self)
        self.translatPlot.setBackground((255, 255, 255))
        self.tdPlotLayout.addWidget(self.translatPlot)
        p = self.translatPlot.getPlotItem()
        self.plotsSetup(p, "Amplitude [mm]", xrange)

        self.rotatPlot = pg.PlotWidget(self)
        self.rotatPlot.setBackground((255, 255, 255))
        self.rdPlotLayout.addWidget(self.rotatPlot)
        p = self.rotatPlot.getPlotItem()
        self.plotsSetup(p, "Amplitude [mm]", xrange)

        self.dvarsPlot = pg.PlotWidget(self)
        self.dvarsPlot.setBackground((255, 255, 255))
        self.dvarsPlotLayout.addWidget(self.dvarsPlot)
        p = self.dvarsPlot.getPlotItem()
        self.plotsSetup(p, "Amplitude [a.u.]", xrange)

        self.spikesPlot = pg.PlotWidget(self)
        self.spikesPlot.setBackground((255, 255, 255))
        self.spikesPlotLayout.addWidget(self.spikesPlot)
        p = self.spikesPlot.getPlotItem()
        self.plotsSetup(p, "Amplitude [a.u.]", xrange)
        self.drawMusterPlot(p)
        p.setYRange(-1, 1, padding=0.0)

        # CNR, means and variances plots and labels
        if not parent.P['isRestingState']:

            self.cnrPlot = pg.PlotWidget(self)
            self.cnrPlot.setBackground((255, 255, 255))
            self.cnrPlotLayout.addWidget(self.cnrPlot)
            p = self.cnrPlot.getPlotItem()
            self.plotsSetup(p, "CNR [a.u.]", xrange)
            self.drawMusterPlot(p)
            p.setYRange(-1, 1, padding=0.0)

            self.meanPlot = pg.PlotWidget(self)
            self.meanPlot.setBackground((255, 255, 255))
            self.meanPlotLayout.addWidget(self.meanPlot)
            p = self.meanPlot.getPlotItem()
            self.plotsSetup(p, "Mean [a.u.]", xrange)
            self.drawMusterPlot(p)
            p.setYRange(-1, 1, padding=0.0)

            self.varPlot = pg.PlotWidget(self)
            self.varPlot.setBackground((255, 255, 255))
            self.varPlotLayout.addWidget(self.varPlot)
            p = self.varPlot.getPlotItem()
            self.plotsSetup(p, "Variance [a.u.]", xrange)
            self.drawMusterPlot(p)
            p.setYRange(-1, 1, padding=0.0)

            names = ['ROI_1 rMean', ' bas', ' cond']
            color = [config.ROI_PLOT_COLORS[0], config.ROI_PLOT_COLORS[0], config.ROI_PLOT_COLORS[0]]
            for i in range(sz - 1):
                if i == sz - 2:
                    name = 'Whole brain ROI'
                else:
                    name = 'ROI_' + str(i + 2)
                names.append(name + ' rMean')
                names.append(' bas')
                names.append(' cond')
                color = color + [config.ROI_PLOT_COLORS[i + 1]] + [config.ROI_PLOT_COLORS[i + 1]] + [
                    config.ROI_PLOT_COLORS[i + 1]]
            pens = []
            for i in range(sz * 3):
                pens = pens + [pg.mkPen(color[i], width=1.2)]
            self.makeTextValueLabel(self.labelMean, names, pens)

            names = ['ROI_1 rVariance', ' bas', ' cond']
            for i in range(sz - 1):
                if i == sz - 2:
                    name = 'Whole brain ROI'
                else:
                    name = 'ROI_' + str(i + 2)
                names.append(name + ' rVariance')
                names.append(' bas')
                names.append(' cond')
            self.makeTextValueLabel(self.labelVar, names, pens)

        # Other labels initialization
        names = ['Translationals: ']
        pens = [config.PLOT_PEN_COLORS[6]]
        for i in range(3):
            names.append(self.names[i])
            pens.append(config.PLOT_PEN_COLORS[i])
        self.makeTextValueLabel(self.tdLabel, names, pens)

        names = ['Rotations: ']
        pens = [config.PLOT_PEN_COLORS[6]]
        for i in range(3):
            names.append(self.names[i + 3])
            pens.append(config.PLOT_PEN_COLORS[i + 3])
        self.makeTextValueLabel(self.rdLabel, names, pens)

        names = ['Framewise Displacement']
        pens = [config.PLOT_PEN_COLORS[0]]
        for i in range(len(config.DEFAULT_FD_THRESHOLDS) - 1):
            names.append('Threshold ' + str(i + 1))
            pens.append(config.PLOT_PEN_COLORS[i + 1])
        self.makeTextValueLabel(self.fdLabel, names, pens)

    # --------------------------------------------------------------------------
    def closeEvent(self, event):

        self.hide()
        event.accept()

    # --------------------------------------------------------------------------
    def plotsSetup(self, p, yName, xrange):

        p.setLabel('left', yName)
        p.setMenuEnabled(enableMenu=False)
        p.setMouseEnabled(x=False, y=False)
        p.showGrid(x=True, y=True, alpha=1)
        p.installEventFilter(self)
        p.disableAutoRange(axis=pg.ViewBox.XAxis)
        p.setXRange(1, xrange, padding=0.0)

    # --------------------------------------------------------------------------
    def onComboboxChanged(self):
        """  SNR/CNR label switching. Both modes use the same label
        """

        state = self.comboBox.currentIndex()

        # SNR state
        if state == 0:

            names = ['SNR ']
            pens = [config.PLOT_PEN_COLORS[6]]
            sz = len(self.rSNR)
            for i in range(sz):
                if i == sz - 1:
                    name = 'Whole brain ROI'
                else:
                    name = 'ROI_' + str(i + 1)
                names.append(name + ':  ' + '{0:.3f}'.format(float(self.rSNR[i][self.iteration])))
                pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))
            self.makeTextValueLabel(self.valuesLabel, names, pens, lineBreak='<br>')
            self.currentMode = 0

        # CNR state
        elif state == 2:

            self.stackedWidgetOptions.setCurrentIndex(0)

            names = ['СNR ']
            pens = [config.PLOT_PEN_COLORS[6]]
            sz = len(self.rCNR)
            for i in range(sz):
                if i == sz - 1:
                    name = 'Whole brain ROI'
                else:
                    name = 'ROI_' + str(i + 1)
                names.append(name + ':  ' + '{0:.3f}'.format(float(self.rCNR[i][self.iteration])))
                pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))
            self.makeTextValueLabel(self.valuesLabel, names, pens, lineBreak='<br>')
            self.currentMode = 2

    # --------------------------------------------------------------------------
    def onRadioButtonStateChanged(self):
        """ FD and MD mode change. Mode changing switch plots and plot title
        """

        if self.mcrRadioButton.isChecked():
            names = ['Micro Displacement']
            pens = [config.PLOT_PEN_COLORS[0]]
            names.append('Threshold')
            pens.append(config.PLOT_PEN_COLORS[2])
            self.makeTextValueLabel(self.fdLabel, names, pens)

        else:
            names = ['Framewise Displacement']
            pens = [config.PLOT_PEN_COLORS[0]]
            for i in range(len(config.DEFAULT_FD_THRESHOLDS) - 1):
                names.append('Threshold ' + str(i + 1))
                pens.append(config.PLOT_PEN_COLORS[i + 1])
            self.makeTextValueLabel(self.fdLabel, names, pens)

        self._fd.draw_mc_plots(self.mcrRadioButton.isChecked(), self.translatPlot, self.rotatPlot, self.fdPlot)

    # --------------------------------------------------------------------------
    def makeTextValueLabel(self, label, names, pens, lineBreak=' '):
        """ Dynamic generation of titles and value labels

        :param label: label for text update
        :param names: set of names
        :param pens: set of pens for each name
        :param lineBreak: line break for value labels, space by default for title labels
        """

        label.setText('')
        legendText = '<html><head/><body><p>'

        for n, c in zip(names, pens):
            cname = c.color().name()
            legendText += (
                    '<span style="font-weight:600;color:{};">'.format(cname) + '{}</span>'.format(n) + lineBreak)

        legendText += '</p></body></html>'

        label.setText(legendText)

    # --------------------------------------------------------------------------
    def roiCheckBoxStateChanged(self):
        """ Redrawing plots when the set of selected ROIs is changed even if run is stopped
        """

        self.init = True
        if self.isStopped:
            self.plotRTQA(self.rSNR.size)

    # --------------------------------------------------------------------------
    def drawMusterPlot(self, plotitem):

        ylim = config.MUSTER_Y_LIMITS

        if self.comboBox.model().item(2).isEnabled():

            muster = []

            for i in range(self.musterInfo['condTotal']):
                muster.append(
                    plotitem.plot(x=self.musterInfo['xCond' + str(i + 1)],
                                  y=self.musterInfo['yCond' + str(i + 1)],
                                  fillLevel=ylim[0],
                                  pen=config.MUSTER_PEN_COLORS[i],
                                  brush=config.MUSTER_BRUSH_COLORS[i])
                )

        else:
            muster = [
                plotitem.plot(x=[1, self._fd.xmax],
                              y=[-1000, 1000],
                              fillLevel=ylim[0],
                              pen=config.MUSTER_PEN_COLORS[9],
                              brush=config.MUSTER_BRUSH_COLORS[9])
            ]

        return muster

    # --------------------------------------------------------------------------
    def plotTs(self, init, plotitem, data, checkedBoxesInd):
        """ Time-series plot method

        :param init: flag for plot initializtion
        :param plotitem: time-series plotitem
        :param data: time-series value for drawing
        :param checkedBoxesInd: indexes of selected ROIs
        """

        if self.tsCheckBox.isChecked():

            sz, l = data.shape

            if init:

                plotitem.clear()
                plots = []

                muster = self.drawMusterPlot(plotitem)

                for i, c in zip(range(sz), np.array(config.ROI_PLOT_COLORS)[checkedBoxesInd]):
                    pen = pg.mkPen(color=c, width=config.ROI_PLOT_WIDTH)
                    p = plotitem.plot(pen=pen)
                    plots.append(p)

                self.plotTs.__dict__[plotitem] = plots, muster

            x = np.arange(1, l + 1, dtype=np.float64)

            plotitems = self.plotTs.__dict__[plotitem][0]
            for p, y in zip(plotitems, data):
                p.setData(x=x, y=np.array(y))

            items = plotitem.listDataItems()

            for m in self.plotTs.__dict__[plotitem][1]:
                items.remove(m)

            if data.any():
                if plotitem.vb.state["targetRange"][1] == [-1, 1]:
                    plotitem.enableAutoRange(enable=True, x=False, y=True)
                plotitem.setYRange(np.min(data), np.max(data), padding=0.0)

    # --------------------------------------------------------------------------
    def plotRTQA(self, n):
        """ Encapsulated plots drawing

        :param n: last volume index
        """

        # The set of active ROIs changing
        if self.init:
            sz, l = self.rSNR.shape
            checkedBoxes = [self.roiCheckBoxes[i].isChecked() for i in range(sz)]
            self.checkedBoxesInd = [j for j, val in enumerate(checkedBoxes) if val]

        # SNR plot
        plotitem = self.snrPlot.getPlotItem()
        data = self.rSNR[self.checkedBoxesInd, 0:n]
        self.plotTs(self.init, plotitem, data, self.checkedBoxesInd)

        if self.comboBox.model().item(2).isEnabled():
            # CNR plot
            plotitem = self.cnrPlot.getPlotItem()
            data = self.rCNR[self.checkedBoxesInd, 0:n]
            self.plotTs(self.init, plotitem, data, self.checkedBoxesInd)

            # Means plot
            plotitem = self.meanPlot.getPlotItem()
            data = np.append(self.rMean[self.checkedBoxesInd, 0:n], self.meanBas[self.checkedBoxesInd, 0:n], axis=0)
            data = np.append(data, self.meanCond[self.checkedBoxesInd, 0:n], axis=0)
            color = np.array(config.ROI_PLOT_COLORS)[self.checkedBoxesInd]
            color = np.append(color, np.array(config.ROI_PLOT_COLORS)[self.checkedBoxesInd])
            color = np.append(color, np.array(config.ROI_PLOT_COLORS)[self.checkedBoxesInd])
            style = [QtCore.Qt.SolidLine, QtCore.Qt.DashLine, QtCore.Qt.DashLine]
            self.plotStatValues(self.init, plotitem, data, color, style)

            # Variances plot
            plotitem = self.varPlot.getPlotItem()
            data = np.append(self.rVar[self.checkedBoxesInd, 0:n], self.varBas[self.checkedBoxesInd, 0:n], axis=0)
            data = np.append(data, self.varCond[self.checkedBoxesInd, 0:n], axis=0)
            self.plotStatValues(self.init, plotitem, data, color, style)

        # Spikes plot
        plotitem = self.spikesPlot.getPlotItem()
        data = self.glmProcTimeSeries[self.checkedBoxesInd, 0:n]
        self.plotSpikes(self.init, plotitem, data, self.checkedBoxesInd)

        # Kalman filter MSE plot
        plotitem = self.msePlot.getPlotItem()
        data = self.rMSE[self.checkedBoxesInd, 0:n]
        self.plotTs(self.init, plotitem, data, self.checkedBoxesInd)

        # Linear trend coefficients plot
        plotitem = self.trendPlot.getPlotItem()
        data = self.linTrendCoeff[self.checkedBoxesInd, 0:n]
        self.plotTs(self.init, plotitem, data, self.checkedBoxesInd)

        # No regulation SNR plot
        plotitem = self.noRegSnrPlot.getPlotItem()
        data = self.rNoRegSNR[self.checkedBoxesInd, 0:n]
        self.plotTs(self.init, plotitem, data, self.checkedBoxesInd)

        # DVARS plot
        plotitem = self.dvarsPlot.getPlotItem()
        plotitem.clear()
        plotitem.plot(y=self.DVARS, pen=config.PLOT_PEN_COLORS[0], name='DVARS')
        plotitem.plot(x=np.arange(0, self._fd.xmax, dtype=np.float64), y=config.DEFAULT_DVARS_THRESHOLD * np.ones(self._fd.xmax),
                        pen=config.PLOT_PEN_COLORS[2], name='thr')

        # Linear trend coefficients value label
        if self.comboBox.currentIndex() == 5:

            names = ['Linear trend beta ']
            pens = [config.PLOT_PEN_COLORS[6]]
            sz = self.linTrendCoeff.shape[0]
            for i in range(sz):
                if i == sz - 1:
                    name = 'Whole brain ROI'
                else:
                    name = 'ROI_' + str(i + 1)
                names.append(name + ': ' + '{0:.3f}'.format(float(self.linTrendCoeff[i, n - 1])))
                pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))
            self.makeTextValueLabel(self.trendLabel, names, pens, lineBreak='<br>')

        self.init = False

    # --------------------------------------------------------------------------
    def plotStatValues(self, init, plotitem, data, color, style):
        """ Drawing method for mean and variance statistics

        :param init: flag for plot initializtion
        :param plotitem: mean or variance plotitem
        :param data: signal values for drawing
        :param color: color of each ROI line
        :param style: style of each ROI line
        """

        if self.tsCheckBox.isChecked():

            sz, l = data.shape

            if init:

                plotitem.clear()
                plots = []

                muster = self.drawMusterPlot(plotitem)

                style = np.repeat(style, sz / 3)

                for i, c, s in zip(range(sz), color, style):
                    pen = pg.mkPen(c, width=3.0, style=QtCore.Qt.PenStyle(s))
                    p = plotitem.plot(pen=pen)
                    plots.append(p)

                self.plotTs.__dict__[plotitem] = plots, muster

            x = np.arange(1, l + 1, dtype=np.float64)

            for p, y in zip(self.plotTs.__dict__[plotitem][0], data):
                p.setData(x=x, y=np.array(y))

            items = plotitem.listDataItems()

            for m in self.plotTs.__dict__[plotitem][1]:
                items.remove(m)

            if data.any():
                plotitem.setYRange(np.min(data[np.nonzero(data)]), np.max(data), padding=0.0)

    # --------------------------------------------------------------------------
    def plotDisplacements(self, data, isNewDCMBlock):
        """ Calculation and drawing of Framewise and Micro Displacements

        :param data: motion correction data
        :param isNewDCMBlock: flag of new dcm block
        """

        self._fd.calc_mc_plots(data, isNewDCMBlock)

        self._fd.draw_mc_plots(self.mcrRadioButton.isChecked(), self.translatPlot, self.rotatPlot, self.fdPlot)

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
        self.makeTextValueLabel(self.mcmdValuesLabel, names, pens, lineBreak='<br>')

    # --------------------------------------------------------------------------
    def plotSpikes(self, init, plotitem, data, checkedBoxesInd):
        """ Spikes plot drawing

        :param init: flag for plot initializtion
        :param plotitem: spikes plotitem
        :param data: signal values for drawing
        :param checkedBoxesInd: indexes of selected ROIs
        """

        # First part - line drawing
        sz, l = data.shape
        x = np.arange(1, l + 1, dtype=np.float64)

        if init:
            plotitem.clear()
            plots = []

            muster = self.drawMusterPlot(plotitem)

            for i, c in zip(range(sz), np.array(config.ROI_PLOT_COLORS)[checkedBoxesInd]):
                pen = pg.mkPen(color=c, width=config.ROI_PLOT_WIDTH)
                p = plotitem.plot(pen=pen)
                plots.append(p)

            self.plotSpikes.__dict__[plotitem] = plots, muster

        plots = self.plotSpikes.__dict__[plotitem][0]
        for p, y in zip(plots, data):
            p.setData(x=x, y=np.array(y))

        # Second part - spikes marking
        for i, c in zip(range(sz), np.array(config.ROI_PLOT_COLORS)[checkedBoxesInd]):

            roiInd = checkedBoxesInd[i]
            if self.posSpikes[str(roiInd)].any():
                brush = pg.mkBrush(color=c)
                p = plotitem.scatterPlot(symbol='o', size=20, brush=brush)
                plots.append(p)
                plots[-1].setData(x=self.posSpikes[str(roiInd)] + 1,
                                  y=self.glmProcTimeSeries[roiInd, self.posSpikes[str(roiInd)]])

                pen = pg.mkPen(color=pg.mkColor(0, 0, 0), width=1.5 * config.ROI_PLOT_WIDTH)
                p = plotitem.plot(pen=pen)
                plots.append(p)

                inds = self.posSpikes[str(roiInd)]
                indX = np.array(list(itertools.chain.from_iterable(zip(inds, inds + 1))))
                indY = np.array(list(itertools.chain.from_iterable(zip(inds - 1, inds))))

                y = np.array(self.glmProcTimeSeries[roiInd, indY])
                x1 = indX

                plots[-1].setData(x=x1, y=y, connect='pairs')

            if self.negSpikes[str(roiInd)].any():
                brush = pg.mkBrush(color=c)
                p = plotitem.scatterPlot(symbol='d', size=20, brush=brush)
                plots.append(p)
                plots[-1].setData(x=self.negSpikes[str(roiInd)] + 1,
                                  y=self.glmProcTimeSeries[roiInd, self.negSpikes[str(roiInd)]])

                pen = pg.mkPen(color=pg.mkColor(0, 0, 0), width=1.5 * config.ROI_PLOT_WIDTH)
                p = plotitem.plot(pen=pen)
                plots.append(p)

                inds = self.negSpikes[str(roiInd)]
                indX = np.array(list(itertools.chain.from_iterable(zip(inds, inds + 1))))
                indY = np.array(list(itertools.chain.from_iterable(zip(inds - 1, inds))))

                y = np.array(self.glmProcTimeSeries[roiInd, indY])
                x1 = indX

                plots[-1].setData(x=x1, y=y, connect='pairs')

        items = plotitem.listDataItems()

        for m in self.plotSpikes.__dict__[plotitem][1]:
            items.remove(m)

        if data.any():
            plotitem.setYRange(np.min(self.glmProcTimeSeries) - 1, np.max(self.glmProcTimeSeries) + 1, padding=0.0)

        # number of spikes label
        sz, l = self.glmProcTimeSeries.shape
        cnt = 0
        for i in range(sz):
            cnt = cnt + np.count_nonzero(self.posSpikes[str(i)])
        names = ['( Circles ) <br>Positive spikes: ' + str(int(cnt))]

        cnt = 0
        for i in range(sz):
            cnt = cnt + np.count_nonzero(self.negSpikes[str(i)])
        names.append('<br>( Diamonds )<br>Negative spikes: ' + str(int(cnt)))
        pens = [pg.mkPen(color=config.ROI_PLOT_COLORS[9], width=1.2),
                pg.mkPen(color=config.ROI_PLOT_COLORS[9], width=1.2)]
        self.makeTextValueLabel(self.spikesLabel, names, pens, lineBreak='<br>')

    # --------------------------------------------------------------------------
    def snr(self, rMean, rVar, m2, rSNR, blockIter, data, indexVolume, isNewDCMBlock):
        """ Recursive time-series SNR calculation

        :param data: new value of raw time-series
        :param indexVolume: current volume index
        :param isNewDCMBlock: flag of new dcm block
        :return: calculated SNR are written in RTQA class
        """

        sz = data.size
        if isNewDCMBlock:
            blockIter = 0

        if blockIter:

            for i in range(sz):
                rMean[i, indexVolume] = rMean[i, indexVolume - 1] + (
                        data[i] - rMean[i, indexVolume - 1]) / (blockIter + 1)
                m2[i] = m2[i] + (data[i] - rMean[i, indexVolume - 1]) * (
                        data[i] - rMean[i, indexVolume])
                rVar[i, indexVolume] = m2[i] / blockIter
                rSNR[i, indexVolume] = rMean[i, indexVolume] / (rVar[i, indexVolume] ** (.5))

            blockIter += 1

        else:

            rVar[:, indexVolume] = np.zeros((sz,))
            m2 = np.zeros((sz,))
            rMean[:, indexVolume] = data
            blockIter = 1

        if blockIter < 8:
            rSNR[:, indexVolume] = np.zeros((sz,))

        return rMean, rVar, m2, rSNR, blockIter

    # --------------------------------------------------------------------------
    def calculateSNR(self, data, dataNoReg, indexVolume, isNewDCMBlock):

        sz = data.size

        # AR(1) was not applied.
        self.rMean, self.rVar, self.m2, self.rSNR, self.blockIter = self.snr(self.rMean, self.rVar, self.m2,
                                                                             self.rSNR, self.blockIter, data,
                                                                             indexVolume, isNewDCMBlock)

        # GLM regressors were estimated for time-series with AR(1) applied
        if dataNoReg.any():
            self.rNoRegMean, self.rNoRegVar, self.noRegM2, \
            self.rNoRegSNR, self.noRegBlockIter = self.snr(self.rNoRegMean, self.rNoRegVar, self.noRegM2, self.rNoRegSNR,
                                                           self.noRegBlockIter, dataNoReg, indexVolume, isNewDCMBlock)

        if self.comboBox.currentIndex() == 0:

            names = ['SNR ']
            pens = [config.PLOT_PEN_COLORS[6]]
            for i in range(sz):
                if i == sz - 1:
                    name = 'Whole brain ROI'
                else:
                    name = 'ROI_' + str(i + 1)
                names.append(name + ': ' + '{0:.3f}'.format(float(self.rSNR[i, indexVolume])))
                pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))

            self.makeTextValueLabel(self.valuesLabel, names, pens, lineBreak='<br>')

        else:
            if self.comboBox.currentIndex() == 6:

                names = ['no reg SNR ']
                pens = [config.PLOT_PEN_COLORS[6]]
                for i in range(sz):
                    if i == sz - 1:
                        name = 'Whole brain ROI'
                    else:
                        name = 'ROI_' + str(i + 1)
                    names.append(name + ': ' + '{0:.3f}'.format(float(self.rSNR[i, indexVolume])))
                    pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))

                self.makeTextValueLabel(self.noRegSnrValueLabel, names, pens, lineBreak='<br>')

        self.iteration = indexVolume

    # --------------------------------------------------------------------------
    def calculateCNR(self, data, indexVolume, isNewDCMBlock):
        """ Recursive time-series CNR calculation

        :param data: new value of raw time-series
        :param indexVolume: current volume index
        :param isNewDCMBlock: flag of new dcm block
        :return: calculated CNR are written in RTQA class
        """

        sz = data.size

        if isNewDCMBlock:
            self.iterBas = 0
            self.iterCond = 0
            return

        if indexVolume in self.indBas:
            if not self.iterBas:
                self.meanBas[:, indexVolume] = data
                self.varBas[:, indexVolume] = np.zeros(sz)
                self.m2Bas = np.zeros(sz)
                self.iterBas += 1

            else:

                for i in range(sz):
                    self.meanBas[i, indexVolume] = self.meanBas[i, indexVolume - 1] + (
                                data[i] - self.meanBas[i, indexVolume - 1]) / (self.iterBas + 1)
                    self.m2Bas[i] = self.m2Bas[i] + (data[i] - self.meanBas[i, indexVolume - 1]) * (
                                data[i] - self.meanBas[i, indexVolume])
                    self.varBas[i, indexVolume] = self.m2Bas[i] / self.iterBas

                self.iterBas += 1

        else:

            self.meanBas[:, indexVolume] = self.meanBas[:, indexVolume - 1]
            self.varBas[:, indexVolume] = self.varBas[:, indexVolume - 1]

        if indexVolume in self.indCond:

            if not self.iterCond:
                self.meanCond[:, indexVolume] = data
                self.varCond[:, indexVolume] = np.zeros(sz)
                self.m2Cond = np.zeros(sz)
                self.iterCond += 1

            else:

                for i in range(sz):
                    self.meanCond[i, indexVolume] = self.meanCond[i, indexVolume - 1] + (
                                data[i] - self.meanCond[i, indexVolume - 1]) / (self.iterCond + 1)
                    self.m2Cond[i] = self.m2Cond[i] + (data[i] - self.meanCond[i, indexVolume - 1]) * (
                                data[i] - self.meanCond[i, indexVolume])
                    self.varCond[i, indexVolume] = self.m2Cond[i] / self.iterCond

                self.iterCond += 1

        else:

            self.meanCond[:, indexVolume] = self.meanCond[:, indexVolume - 1]
            self.varCond[:, indexVolume] = self.varCond[:, indexVolume - 1]

        if self.iterCond:

            for i in range(sz):
                self.rCNR[i, indexVolume] = (self.meanCond[i, indexVolume] - self.meanBas[i, indexVolume]) / (
                    np.sqrt(self.varCond[i, indexVolume] + self.varBas[i, indexVolume]))

            if self.comboBox.currentIndex() == 2:

                names = ['СNR ']
                pens = [config.PLOT_PEN_COLORS[6]]
                for i in range(sz):
                    if i == sz - 1:
                        name = 'Whole brain ROI'
                    else:
                        name = 'ROI_' + str(i + 1)
                    names.append(name + ': ' + '{0:.3f}'.format(float(self.rCNR[i][indexVolume - 1])))
                    pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))

                self.makeTextValueLabel(self.valuesLabel, names, pens, lineBreak='<br>')

    # --------------------------------------------------------------------------
    def calculateSpikes(self, data, indexVolume, posSpikes, negSpikes):
        """ Spikes and GLM signal recording

        :param data: signal values after GLM process
        :param indexVolume: current volume index
        :param posSpikes: flags of positive spikes
        :param negSpikes: flags of negative spikes
        """

        sz, l = data.shape
        self.glmProcTimeSeries[:, indexVolume] = data[:, 0]

        for i in range(sz):
            if posSpikes[i] == 1:
                if self.posSpikes[str(i)].any():
                    self.posSpikes[str(i)] = np.append(self.posSpikes[str(i)], indexVolume)
                else:
                    self.posSpikes[str(i)] = np.array([indexVolume])
            if negSpikes[i] == 1 and l > 2:
                if self.negSpikes[str(i)].any():
                    self.negSpikes[str(i)] = np.append(self.negSpikes[str(i)], indexVolume)
                else:
                    self.negSpikes[str(i)] = np.array([indexVolume])

    # --------------------------------------------------------------------------
    def calculateMSE(self, indexVolume, inputSignal, outputSignal):
        """ Low pass filter performance estimated by recursive mean squared error

        :param indexVolume: current volume index
        :param inputSignal: signal value before filtration
        :param outputSignal: signal value after filtration

        """

        sz = inputSignal.size
        n = self.blockIter-1

        for i in range(sz):
            self.rMSE[i,indexVolume] = (n/(n+1)) * self.rMSE[i,indexVolume-1] + ((inputSignal[i]-outputSignal[i])**2)/(n+1)

        if self.comboBox.currentIndex() == 4:

            names = ['MSE ']
            pens = [config.PLOT_PEN_COLORS[6]]
            for i in range(sz):
                if i == sz - 1:
                    name = 'Whole brain ROI'
                else:
                    name = 'ROI_' + str(i + 1)
                names.append(name + ': ' + '{0:.3f}'.format(float(self.rMSE[i, indexVolume])))
                pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[i], width=1.2))

            self.makeTextValueLabel(self.mseLabel, names, pens, lineBreak='<br>')

    # --------------------------------------------------------------------------
    def calculateDVARS(self, dvarsValue, isNewDCMBlock):

        if self.iteration == 0 or isNewDCMBlock:
            self.DVARS = np.append(self.DVARS, 0)
        else:
            self.DVARS = np.append(self.DVARS, dvarsValue)

        if self.DVARS[-1] > config.DEFAULT_DVARS_THRESHOLD:
            self.excDVARS = self.excDVARS + 1

        if self.comboBox.currentIndex() == 7:

            names = ['DVARS ']
            pens = [config.PLOT_PEN_COLORS[6]]
            names.append('{0:.3f} '.format(float(self.DVARS[-1])))
            names.append('<br>Threshold : ' + str(int(self.excDVARS)))
            pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[-1], width=1.2))
            pens.append(pg.mkPen(color=config.ROI_PLOT_COLORS[-1], width=1.2))

            self.makeTextValueLabel(self.dvarsLabel, names, pens, lineBreak='<br>')

    # --------------------------------------------------------------------------
    def dataPacking(self):
        """ Packaging of python RTQA data for following save
        """

        tsRTQA = dict.fromkeys(['rMean', 'rVar', 'rSNR', 'rNoRegSNR',
                                'meanBas', 'varBas', 'meanCond', 'varCond', 'rCNR',
                                'excFDIndexes_1', 'excFDIndexes_2', 'excMDIndexes', 'FD', 'MD', 'DVARS', 'rMSE'])

        tsRTQA['rMean'] = matlab.double(self.rMean.tolist())
        tsRTQA['rVar'] = matlab.double(self.rVar.tolist())
        tsRTQA['rSNR'] = matlab.double(self.rSNR.tolist())
        tsRTQA['rNoRegSNR'] = matlab.double(self.rNoRegSNR.tolist())
        tsRTQA['meanBas'] = matlab.double(self.meanBas.tolist())
        tsRTQA['varBas'] = matlab.double(self.varBas.tolist())
        tsRTQA['meanCond'] = matlab.double(self.meanCond.tolist())
        tsRTQA['varCond'] = matlab.double(self.varCond.tolist())
        tsRTQA['rCNR'] = matlab.double(self.rCNR.tolist())
        tsRTQA['excFDIndexes_1'] = matlab.double(self._fd.excFDIndexes_1.tolist())
        tsRTQA['excFDIndexes_2'] = matlab.double(self._fd.excFDIndexes_2.tolist())
        tsRTQA['excMDIndexes'] = matlab.double(self._fd.excMDIndexes.tolist())
        tsRTQA['FD'] = matlab.double(self._fd.FD.tolist())
        tsRTQA['MD'] = matlab.double(self._fd.MD.tolist())
        tsRTQA['DVARS'] = matlab.double(self.DVARS.tolist())
        tsRTQA['rMSE'] = matlab.double(self.rMSE.tolist())

        return tsRTQA

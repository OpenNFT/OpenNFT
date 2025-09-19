# coding=utf-8

"""
# OpenNFT
OpenNFT is an Open-source NeuroFeedback Training framework
http://www.OpenNFT.org

For generic aspects refer to:
Yury Koush, John Ashburner, Evgeny Prilepin, Ronald Sladky, Peter Zeidman, Sergei Bibikov,
Frank Scharnowski, Artem Nikonorov, Dimitri Van De Ville,

OpenNFT: An open-source Python/Matlab framework for real-time fMRI neurofeedback training
based on activity, connectivity and multivariate pattern analysis. (2017) Neuroimage 157:489-503.

Real-time fMRI data for testing OpenNFT functionality. (2017) Data in Brief 14:344-347.

_________________________________________________________________________
Copyright (C) 2016-2021 OpenNFT.org

License
OpenNFT Software is open-source and is distributed under GNU GPL v3.0 license
(https://github.com/OpenNFT/OpenNFT/blob/master/LICENSE).

Disclaimer
The end-user is advised to justify their research or application outcome using pilot data and
complementary offline data analyses.

Contact
opennft@gmail.com
_________________________________________________________________________

The module below is written by Artem Nikonorov, Evgeny Prilepin, Yury Koush, Ronald Sladky

"""

import time
import glob
import queue
import enum
import re
import fnmatch
import threading
import multiprocessing

from pathlib import Path
from loguru import logger

import numpy as np
import pyqtgraph as pg
import pydicom

from watchdog.events import FileSystemEventHandler

from pyniexp.network import Udp
from scipy.io import loadmat

from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMenu, QMessageBox
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtCore import QSettings, QTimer, QEvent, QRegExp
from PyQt5.uic import loadUi
from PyQt5.QtGui import QRegExpValidator

from opennft import (
    config,
    conversions,
    runmatlab,
    ptbscreen,
    mosaicview,
    projview,
    mapimagewidget,
    plugin,
    utils,
    rtqa_gui,
    rtqa_calc,
    volviewformation,
    eventrecorder as erd,
)

if config.USE_POLLING_FS_OBSERVER:
    from watchdog.observers.polling import PollingObserver
else:
    from watchdog.observers import Observer
    
if config.USE_MRPULSE:
    from opennft import mrpulse

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)


class ImageViewMode(enum.IntEnum):
    mosaic = 0
    orthviewAnat = 1
    orthviewEPI = 2


class CreateFileEventHandler(FileSystemEventHandler):
    def __init__(self, filepat, fq: queue.Queue, recorder: erd.EventRecorder):
        self.filepat = filepat
        self.fq = fq
        self.recorder = recorder

    def on_created(self, event):
        # if not event.is_directory and event.src_path.endswith(self.filepat):
        if not event.is_directory and fnmatch.fnmatch(Path(event.src_path).name, self.filepat):
            # t1
            self.recorder.recordEvent(erd.Times.t1, 0, time.time())
            self.fq.put(event.src_path)


# --------------------------------------------------------------------------
class OpenNFT(QWidget):
    """Open Neurofeedback GUI application class
    """

    # --------------------------------------------------------------------------
    def initUdpSender(self):
        if not config.USE_UDP_FEEDBACK:
            return

        self.udpSender = Udp(
            IP=config.UDP_FEEDBACK_IP,
            port=config.UDP_FEEDBACK_PORT,
            control_signal=config.UDP_FEEDBACK_CONTROLCHAR,
            encoding='UTF-8'
        )
        self.udpSender.connect_for_sending()
        self.udpSender.sending_time_stamp = True

        self.udpCondForContrast = self.P['CondIndexNames']
        if type(self.udpCondForContrast[0]) != str:
            self.udpCondForContrast[0] = 'BAS'

    # --------------------------------------------------------------------------
    def finalizeUdpSender(self):
        if not config.USE_UDP_FEEDBACK:
            return
        self.udpSender.close()

    # --------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        loadUi(utils.get_ui_file('opennft.ui'), self)

        self.setWindowIcon(QIcon(str(config.OpenNFT_ICON)))
        self.displayEvent = multiprocessing.Event()
        self.endDisplayEvent = multiprocessing.Event()

        self.displayThread = None
        self.stopDisplayThread = True

        self.pbMoreParameters.setChecked(False)

        pg.setConfigOption('foreground',
                           self.palette().color(QPalette.Foreground))
        # self.plotBgColor = (210, 210, 210)
        self.plotBgColor = (255, 255, 255)

        self.mosaicImageView = mosaicview.MosaicImageViewWidget(self)
        self.layoutMosaic.addWidget(self.mosaicImageView)

        self.orthView = projview.ProjectionsWidget(self)
        self.layoutOrthView.addWidget(self.orthView)

        self.pos_map_thresholds_widget = mapimagewidget.MapImageThresholdsWidget(self)
        self.neg_map_thresholds_widget = mapimagewidget.MapImageThresholdsWidget(self, colormap='Blues_r')

        self.layoutHotMapThresholds.addWidget(self.pos_map_thresholds_widget)
        self.pos_map_thresholds_widget.setEnabled(False)
        self.layoutNegMapThresholds.addWidget(self.neg_map_thresholds_widget)
        self.neg_map_thresholds_widget.setEnabled(False)

        self.mcPlot = self.createMcPlot()

        (self.rawRoiPlot,
         self.procRoiPlot,
         self.normRoiPlot) = self.createRoiPlots()

        self.settingFileName = config.ROOT_PATH
        self.appSettings = QSettings(
            str(utils.get_app_settings_file()), QSettings.IniFormat, self)

        self.iteration = 1
        self.preiteration = 0
        self.pendingFilename = ''
        self.resetDone = False
        self.isInitialized = False
        self.isSetFileChosen = False
        self.isCalculateDcm = False  # todo: rename to computeModelInProgress
        self.isMainLoopEntered = False
        self.typicalFileSize = 0
        self.mainLoopLock = threading.Lock()
        self.displayData = None
        self.displayQueue = queue.Queue()

        if config.USE_POLLING_FS_OBSERVER:
            self.fs_observer = PollingObserver()
        else:
            self.fs_observer = Observer()

        self.mrPulses = None
        self.recorder = erd.EventRecorder()
        self.call_timer = QTimer(self)
        self.files_queue = queue.Queue()
        self.isOffline = None
        self.files_processed = []
        self.files_exported = []

        self.main_loop = None
        self.eng = None
        self.orth_view = None
        self.view_form_input = None
        self.view_form_output = None
        self.rtqa_input = None
        self.rtqa_output = None

        self.plugins = []

        self.fFinNFB = False
        self.orthViewUpdateInProgress = False
        self.outputSamples = {}
        self.musterInfo = {}

        # Core Matlab helper process
        matlab_helpers = runmatlab.get_matlab_helpers()

        self.mlMainHelper = matlab_helpers[config.MAIN_MATLAB_NAME]
        if config.USE_PTB_HELPER:
            self.mlPtbDcmHelper = matlab_helpers[config.PTB_MATLAB_NAME]
        self.mlModelHelper = matlab_helpers.get(config.MODEL_HELPER_MATLAB_NAME)

        if config.USE_PTB_HELPER:
            self.ptbScreen = ptbscreen.PtbScreen(self.mlPtbDcmHelper, self.recorder, self.endDisplayEvent)

        self.P = {}
        self.mainLoopData = {}
        self.shamData = None
        self.rtQA_matlab = {}
        self.reultFromHelper = None

        self.imageViewMode = ImageViewMode.mosaic
        self.currentCursorPos = (129, 95)
        self.currentProjection = projview.ProjectionType.coronal
        self.orthViewInitialize = True
        self.orthViewUpdateFuture = None
        self.orthViewUpdateCheckTimer = QTimer(self)
        self.mosaicViewUpdateCheckTimer = QTimer(self)

        self.settings = QSettings('', QSettings.IniFormat)
        self.reachedFirstFile = False

        self.initializeUi()
        self.readAppSettings()
        self.initialize(start=False)

        self.calc_rtqa = None
        self.windowRTQA = None
        self.isStopped = False

    # --------------------------------------------------------------------------
    def closeEvent(self, e):

        self.writeAppSettings()
        self.stop()
        self.hide()

        self.eng = None
        if self.orth_view:
            self.view_form_input["is_stopped"] = True
            self.orth_view.terminate()
        self.orth_view = None

        if self.calc_rtqa:
            self.calc_rtqa.terminate()
        self.calc_rtqa = None

        if runmatlab.is_shared_matlab():
            runmatlab.detach_matlab()
        else:
            runmatlab.destroy_matlab()

    # --------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if event.type() == QEvent.GraphicsSceneMouseDoubleClick:
            # Replace plot views
            plotWidget = obj.getViewWidget()

            # Find widget layout
            if self.layoutPlot1.indexOf(plotWidget) == 0:
                plotLayout = self.layoutPlot1
            elif self.layoutPlot2.indexOf(plotWidget) == 0:
                plotLayout = self.layoutPlot2
            elif self.layoutPlot3.indexOf(plotWidget) == 0:
                plotLayout = self.layoutPlot3
            else:
                return False

            mainPlotWidget = self.layoutPlotMain.takeAt(0).widget()

            self.layoutPlotMain.addWidget(plotWidget)
            plotLayout.removeWidget(plotWidget)
            plotLayout.addWidget(mainPlotWidget)

            # Fix layouts stretch after replacing
            for i, s in enumerate([1, 1, 1]):
                self.layoutLeftPlots.setStretch(i, s)

            return True

        return False

    # --------------------------------------------------------------------------
    def createMcPlot(self):
        mctrotplot = pg.PlotWidget(self)
        mctrotplot.setBackground(self.plotBgColor)
        self.layoutPlot1.addWidget(mctrotplot)

        p = mctrotplot.getPlotItem()
        p.setTitle('MC', size='')
        p.setLabel('left', "Amplitude [a.u.]")
        p.setMenuEnabled(enableMenu=False)
        p.setMouseEnabled(x=False, y=False)
        p.installEventFilter(self)

        return mctrotplot

    # --------------------------------------------------------------------------
    def createRoiPlots(self):
        rawroiplot = pg.PlotWidget(self)
        self.layoutPlot2.addWidget(rawroiplot)

        p = rawroiplot.getPlotItem()
        p.setTitle('Raw ROI', size='')
        p.setLabel('left', "Amplitude [a.u.]")
        p.setMenuEnabled(enableMenu=False)
        p.setMouseEnabled(x=False, y=False)
        p.installEventFilter(self)

        procroiplot = pg.PlotWidget(self)
        self.layoutPlot3.addWidget(procroiplot)

        p = procroiplot.getPlotItem()
        p.setTitle('Proc ROI', size='')
        p.setLabel('left', "Amplitude [a.u.]")
        p.setMenuEnabled(enableMenu=False)
        p.setMouseEnabled(x=False, y=False)
        p.installEventFilter(self)

        normroiplot = pg.PlotWidget(self)
        self.layoutPlotMain.addWidget(normroiplot)

        p = normroiplot.getPlotItem()
        p.setTitle('Norm ROI', size='')
        p.setLabel('left', "Amplitude [a.u.]")
        p.setMenuEnabled(enableMenu=False)
        p.setMouseEnabled(x=False, y=False)
        p.installEventFilter(self)

        plots = (
            rawroiplot,
            procroiplot,
            normroiplot
        )

        for p in plots:
            p.setBackground(self.plotBgColor)

        return plots

    # --------------------------------------------------------------------------
    def textChangedDual(self, leFrom, leTo):
        pos = leTo.cursorPosition()
        leTo.setText(leFrom.text())
        leTo.setCursorPosition(pos)

    # --------------------------------------------------------------------------
    def initializeUi(self):
        top_size = int(self.height() * 0.7)
        bottom_size = self.height() - top_size
        h_sizes = [top_size, bottom_size]
        self.splitterMainVer.setSizes(h_sizes)

        w_sizes = [self.width() // 2] * 2
        self.splitterMainHor.setSizes(w_sizes)

        self.btnInit.clicked.connect(lambda: self.initialize(start=True))

        if not config.AUTO_RTQA:
            self.btnPlugins.clicked.connect(self.showPluginDlg)
            self.btnPlugins.setEnabled(False)
            self.btnSetup.clicked.connect(self.setup)
            self.btnStart.clicked.connect(self.start)
            self.btnStop.clicked.connect(self.stop)
            self.btnRTQA.clicked.connect(self.rtQA)
            self.btnRTQA.setEnabled(False)

            self.leFirstFile.textChanged.connect(lambda: self.textChangedDual(self.leFirstFile, self.leFirstFile2))
            self.leFirstFile2.textChanged.connect(lambda: self.textChangedDual(self.leFirstFile2, self.leFirstFile))

            self.pbMoreParameters.toggled.connect(self.onShowMoreParameters)

            self.btnChooseSetFile.clicked.connect(self.onChooseSetFile)
            self.btnChooseSetFile2.clicked.connect(self.onChooseSetFile)

            self.btnChooseProtocolFile.clicked.connect(self.onChooseProtocolFile)

            self.btnChhoseWeghts.clicked.connect(self.onChooseWeightsFile)

            self.btnChooseRoiAnatFolder.clicked.connect(
                lambda: self.onChooseFolder('RoiAnatFolder', self.leRoiAnatFolder))

            self.btnChooseRoiGroupFolder.clicked.connect(
                lambda: self.onChooseFolder('RoiGroupFolder', self.leRoiGroupFolder))

            self.btnChooseStructBgFile.clicked.connect(self.onChooseStructBgFile)

            self.btnMCTempl.clicked.connect(self.onChooseMCTemplFile)

            self.btnChooseWorkFolder.clicked.connect(
                lambda: self.onChooseFolder('WorkFolder', self.leWorkFolder))
            self.btnChooseWatchFolder.clicked.connect(
                lambda: self.onChooseFolder('WatchFolder', self.leWatchFolder))

            self.btnStart.setEnabled(False)
        else:
            self.stackedWidget.setCurrentIndex(1)
            self.btnPlugins.setEnabled(False)
            self.pbMoreParameters.setEnabled(False)
            self.btnSetup.setEnabled(False)
            self.btnStart.clicked.connect(self.start)
            self.btnStop.clicked.connect(self.stop)
            self.btnRTQA.clicked.connect(self.rtQA)
            self.btnRTQA.setEnabled(False)

            self.btnChooseWatchFolder3.clicked.connect(
                lambda: self.onChooseFolder('WatchFolder', self.leWatchFolder3))
            self.btnChooseRoiFolder.clicked.connect(
                lambda: self.onChooseFolder('RoiFolder', self.leRoiFolder))
            self.btnMCTempl3.clicked.connect(self.onChooseMCTemplFile)

            self.cbImageViewMode.model().item(1).setEnabled(False)

            if not config.SELECT_ROIS:
                self.label_16.setVisible(False)
                self.leRoiFolder.setVisible(False)
                self.btnChooseRoiFolder.setVisible(False)

            if not config.USE_EPI_TEMPLATE:
                self.label_26.setVisible(False)
                self.leMCTempl3.setVisible(False)
                self.btnMCTempl3.setVisible(False)

        self.cbImageViewMode.currentIndexChanged.connect(self.onChangeImageViewMode)
        self.orthView.cursorPositionChanged.connect(self.onChangeOrthViewCursorPosition)

        self.call_timer.timeout.connect(self.call_main_loop)
        self.orthViewUpdateCheckTimer.timeout.connect(self.onCheckOrthViewUpdated)
        self.mosaicViewUpdateCheckTimer.timeout.connect(self.onCheckMosaicViewUpdated)

        self.cbType.currentTextChanged.connect(self.onChangeFBType)

        self.cbDataType.currentTextChanged.connect(self.onChangeDataType)
        self.onChangeDataType()

        self.btnChooseShamFile.clicked.connect(lambda: self.onChooseFile('ShamFile', self.leShamFile))

        self.cbUsePTB.stateChanged.connect(self.onChangePTB)
        self.onChangePTB()

        ipv4_regexp = QRegExp(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}")

        self.leTCPDataIP.setValidator(QRegExpValidator(ipv4_regexp, self))
        self.cbUseTCPData.stateChanged.connect(self.onChangeUseTCPData)
        self.onChangeUseTCPData()

        self.leUDPFeedbackIP.setValidator(QRegExpValidator(ipv4_regexp, self))
        self.cbUseUDPFeedback.stateChanged.connect(self.onChangeUseUDPFeedback)

        self.pos_map_thresholds_widget.thresholds_manually_changed.connect(self.onInteractWithMapImage)
        self.neg_map_thresholds_widget.thresholds_manually_changed.connect(self.onInteractWithMapImage)

        self.posMapCheckBox.toggled.connect(self.onChangePosMapVisible)
        self.negMapCheckBox.toggled.connect(self.onChangeNegMapVisible)

        self.sliderMapsAlpha.valueChanged.connect(lambda v: self.mosaicImageView.set_pos_map_opacity(v / 100.0))
        self.sliderMapsAlpha.valueChanged.connect(lambda v: self.mosaicImageView.set_neg_map_opacity(v / 100.0))
        self.sliderMapsAlpha.valueChanged.connect(lambda v: self.orthView.set_pos_map_opacity(v / 100.0))
        self.sliderMapsAlpha.valueChanged.connect(lambda v: self.orthView.set_neg_map_opacity(v / 100.0))

        self.onChangePosMapVisible()
        self.onChangeNegMapVisible()
        self.onChangeUseUDPFeedback()

    # --------------------------------------------------------------------------
    def onChangeFBType(self, value):
        if value == 'DCM':
            self.cbFeedbackPlot.setChecked(False)
            self.cbFeedbackPlot.setEnabled(False)
        else:
            self.cbFeedbackPlot.setEnabled(True)

    # --------------------------------------------------------------------------
    def onChangePosMapVisible(self):
        is_visible = self.posMapCheckBox.isChecked()

        self.mosaicImageView.set_pos_map_visible(is_visible)
        self.orthView.set_pos_map_visible(is_visible)

    # --------------------------------------------------------------------------
    def onChangeNegMapVisible(self):
        is_visible = self.negMapCheckBox.isChecked()

        self.mosaicImageView.set_neg_map_visible(is_visible)
        self.orthView.set_neg_map_visible(is_visible)

    # --------------------------------------------------------------------------
    def onChangeNegMapPolicy(self):

        if self.windowRTQA:
            is_rtqa_volume = self.rtqa_output["show_vol"]
        else:
            is_rtqa_volume = False

        if is_rtqa_volume:
            setattr(self, '__neg_map_state', self.negMapCheckBox.isChecked())
            self.negMapCheckBox.setChecked(False)
            self.negMapCheckBox.setEnabled(False)
        else:
            neg_map_state = getattr(self, '__neg_map_state', self.negMapCheckBox.isChecked())
            self.negMapCheckBox.setChecked(neg_map_state)
            self.negMapCheckBox.setEnabled(True)

    # --------------------------------------------------------------------------
    def showPluginDlg(self):
        self.btnStart.setEnabled(False)  # force rerunning Setup

        if self.pluginWindow.exec_():
            self.plugins = []
            for p in range(len(self.pluginWindow.plugins)):
                if self.pluginWindow.lvPlugins.model().item(p).checkState():
                    if 'plugin_prot' in self.pluginWindow.plugins[p].META.keys():
                        if self.settings.value('Prot') != self.pluginWindow.plugins[p].META['plugin_prot']:
                            QMessageBox.warning(self, 'Plugin compatibility issue',
                                "Plugin '"+self.pluginWindow.plugins[p].META['plugin_name']+"' requires a protocol '"+self.pluginWindow.plugins[p].META['plugin_prot']+"'."+
                                "\nIt is not compatible with current prortocol '"+self.settings.value('Prot')+"' and will not be used.")
                            continue
                    self.plugins += [plugin.Plugin(self, self.pluginWindow.plugins[p])]

    # --------------------------------------------------------------------------
    def updatePlugins(self):
        for i in range(len(self.plugins)):
            self.plugins[i].update()

    # --------------------------------------------------------------------------
    def onChangeDataType(self):
        self.cbgetMAT.setChecked(self.cbgetMAT.isChecked() and self.cbDataType.currentText() == 'DICOM')
        self.cbgetMAT.setEnabled(self.cbDataType.currentText() == 'DICOM')

    # --------------------------------------------------------------------------
    def onChangePTB(self):
        self.cbScreenId.setEnabled(self.cbUsePTB.isChecked())
        self.cbDisplayFeedbackFullscreen.setEnabled(self.cbUsePTB.isChecked())
        self.sbTargANG.setEnabled(self.cbUsePTB.isChecked())
        self.sbTargRAD.setEnabled(self.cbUsePTB.isChecked())
        self.sbTargDIAM.setEnabled(self.cbUsePTB.isChecked())

    # --------------------------------------------------------------------------
    def onChangeUseTCPData(self):
        self.leTCPDataIP.setEnabled(self.cbUseTCPData.isChecked())
        self.leTCPDataPort.setEnabled(self.cbUseTCPData.isChecked())

    # --------------------------------------------------------------------------
    def onChangeUseUDPFeedback(self):
        self.leUDPFeedbackIP.setEnabled(self.cbUseUDPFeedback.isChecked())
        self.leUDPFeedbackPort.setEnabled(self.cbUseUDPFeedback.isChecked())
        self.leUDPFeedbackControlChar.setEnabled(self.cbUseUDPFeedback.isChecked())
        self.cbUDPSendCondition.setEnabled(self.cbUseUDPFeedback.isChecked())
        if not (self.cbUseUDPFeedback.isChecked()):
            self.cbUDPSendCondition.setChecked(False)

    # --------------------------------------------------------------------------
    def onShowMoreParameters(self, flag: bool):
        self.stackedWidgetMain.setCurrentIndex(int(flag))

    # --------------------------------------------------------------------------
    def getFreeMemmapFilename(self):
        path = Path(self.P['WorkFolder'])
        fname = path / 'OrthView.dat'
        if not fname.exists():
            return str(fname)

        try:
            f = open(fname, 'w+')
            f.close()
            return str(fname)
        except IOError:
            fname = path / 'OrthView1.dat'

        if not fname.exists():
            return str(fname)

        try:
            f = open(fname, 'w+')
            f.close()
            return str(fname)
        except IOError:
            logger.info('POSSIBLE PROBLEMS WITH MEMMAP ACCESS!')
            return str(fname)

    # --------------------------------------------------------------------------
    def initMainLoopData(self):
        # Data types
        self.mainLoopData['DataType'] = self.cbDataType.currentText()

        self.eng.workspace['mainLoopData'] = self.mainLoopData

        self.eng.workspace['rtQA_matlab'] = self.rtQA_matlab

        self.eng.setupProcParams(nargout=0)

        if self.P['isRTQA']:
            self.eng.epiWholeBrainROI(nargout=0)

        with utils.timeit("Receiving 'P' from Matlab:"):
            self.P = self.eng.workspace['P']

    # --------------------------------------------------------------------------
    def displayScreen(self):
        self.displayQueue.put(self.displayData)
        self.displayEvent.set()

    # --------------------------------------------------------------------------
    def onEventDisplay(self):
        while True:
            self.displayEvent.wait()
            if self.stopDisplayThread:
                return
            # logger.info('{}', self.displayStack[0]['iteration'])
            # logger.info('{}', self.displayStack[0]['displayStage'])
            self.ptbScreen.displayLock.acquire()
            self.ptbScreen.display(self.displayQueue)
            self.displayEvent.clear()

    # --------------------------------------------------------------------------
    def checkFileIsReady(self, path, fname):
        acquisitionFinished = True
        filesize = Path(path).stat().st_size
        if self.typicalFileSize <= 0:
            time.sleep(0.050)
            if filesize < Path(path).stat().st_size:
                acquisitionFinished = False

        else:
            if self.typicalFileSize - filesize > 4000:  # suppose that minimal copying block is 4K
                acquisitionFinished = False

        if not acquisitionFinished:
            if self.pendingFilename != fname:
                logger.info('Acquisition in progress - "{}"', fname)
                self.pendingFilename = fname

            self.files_queue.put_nowait(fname)
            self.isMainLoopEntered = False
        else:
            self.typicalFileSize = Path(path).stat().st_size

        return acquisitionFinished

    # --------------------------------------------------------------------------
    def call_main_loop(self):
        if not self.main_loop:
            self.main_loop = self.main_loop_iteration()
            return

        try:
            next(self.main_loop)
        except StopIteration:
            self.main_loop = self.main_loop_iteration()

    # --------------------------------------------------------------------------
    def main_loop_iteration(self):
        if self.eng is None:
            return

        self.mainLoopLock.acquire()
        if self.isMainLoopEntered:
            self.mainLoopLock.release()
            return
        self.isMainLoopEntered = True
        self.mainLoopLock.release()

        if self.preiteration < self.iteration:
            # this code is executed before file is acquired

            self.eng.mainLoopEntry(self.iteration, nargout=0)

            self.displayData = self.eng.initDispalyData(self.iteration)

            # t6, display instruction prior to data acquisition for current iteration
            self.recorder.recordEvent(erd.Times.t6, self.iteration)

            # display instruction prior to data acquisition for current iteration
            if self.P['Type'] in ['PSC', 'Corr']:
                if config.USE_PTB:
                    logger.info('instruction + {}', self.iteration)
                    self.displayScreen()

                if self.iteration > self.P['nrSkipVol'] and config.UDP_SEND_CONDITION:
                    self.udpSender.send_data(
                        self.udpCondForContrast[int(self.eng.evalin('base', 'mainLoopData.condition')) - 1])

            elif self.P['Type'] == 'DCM':
                if not self.isCalculateDcm and config.USE_PTB:
                    self.displayScreen()

            elif self.P['Type'] == 'SVM':
                if self.displayData and config.USE_UDP_FEEDBACK:
                    logger.info('Sending by UDP - instrValue = ')  # + str(self.displayData['instrValue'])
                    # self.udpSender.send_data(self.displayData['instrValue'])

        if self.cbUseTCPData.isChecked():
            fname = str(Path(self.P['WatchFolder'])
                        / self.P['FirstFileNameTxt'].replace('Image Series No', 'ImgSerNr').replace('#', 'iter').format(
                **(self.P), iter=self.iteration))
        else:
            try:
                fname = self.files_queue.get_nowait()
            except queue.Empty:
                if (self.previousIterStartTime > 0) and (self.preiteration < self.iteration):
                    if (time.time() - self.previousIterStartTime) > (self.P['TR'] / 1000):
                        logger.info('Scanner is too slow...')
                if not self.isOffline and len(self.files_exported) > 0:
                    fname = None
                else:
                    self.preiteration = self.iteration
                    self.isMainLoopEntered = False
                    return

            if not self.isOffline and self.files_queue.qsize() > 0:
                logger.info("Toolbox is too slow, on file {}", fname)
                logger.info("{} files in queue", self.files_queue.qsize())

        self.preiteration = self.iteration

        # data acquisition
        if fname is not None:
            path = str(Path(self.P['WatchFolder'], fname))
            if (not self.isOffline) and (not self.cbUseTCPData.isChecked()) and self.reachedFirstFile:
                if not self.checkFileIsReady(path, fname):
                    self.isMainLoopEntered = False
                    return

            self.files_exported.append(fname)

        # check file sequence
        if (not self.isOffline) and (not self.cbUseTCPData.isChecked()) and (len(self.files_processed) > 0):

            if config.DICOM_SIEMENS_XA30:
                file_name = Path(self.files_processed[-1]).parts[-1]
                splitted_name = file_name.split("_")
                last_fname = splitted_name[0] + "_" + splitted_name[1] + "_" + splitted_name[2] + ".dcm"
            else:
                last_fname = self.files_processed[-1]
            r = re.findall(r'\D(\d+).\w+$', last_fname)
            last_num = int(r[-1])
            new_fname = fname
            fname = None
            for cur_fname in self.files_exported:
                if config.DICOM_SIEMENS_XA30:
                    cur_name = cur_fname
                    file_name = Path(cur_fname).parts[-1]
                    splitted_name = file_name.split("_")
                    cur_fname = splitted_name[0] + "_" + splitted_name[1] + "_" + splitted_name[2] + ".dcm"
                r = re.findall(r'\D(\d+).\w+$', cur_fname)
                cur_num = int(r[-1])
                if cur_num - last_num == 1:
                    fname = cur_fname
                    break

            if fname is None:
                if new_fname is not None:
                    logger.warning('Non-sequential export: ' + new_fname)
                self.isMainLoopEntered = False
                return
            else:
                if config.DICOM_SIEMENS_XA30:
                    self.files_exported.remove(cur_name)
                    fname = cur_name
                else:
                    self.files_exported.remove(fname)

        autoRTQAMCTempl = (self.iteration == self.P['nrSkipVol'] + 1) and config.AUTO_RTQA \
                          and not self.P['useEPITemplate'] \
                          and not self.autoRTQASetup

        if autoRTQAMCTempl:
            self.P['MCTempl'] = fname
            self.eng.workspace['P'] = self.P
            self.setupAutoRTQA()
        elif self.P['useEPITemplate'] and not self.autoRTQASetup:
            self.eng.workspace['P'] = self.P
            self.setupAutoRTQA()

        # t2
        self.recorder.recordEvent(erd.Times.t2, self.iteration, time.time())

        if not self.reachedFirstFile:
            if config.DICOM_SIEMENS_XA30:
                firstFileName = self.P['FirstFileName'].split('.')[0]
            else:
                firstFileName = self.P['FirstFileName']
            if not firstFileName in fname:
                logger.info('Volume skipped, waiting for first file')
                self.isMainLoopEntered = False
                return
            else:
                logger.info('First file was reached')
                self.reachedFirstFile = True

        if self.iteration > self.P['NrOfVolumes']:
            logger.info('Volumes limit reached')
            self.stop()
            self.isMainLoopEntered = False
            return

        if config.AUTO_RTQA and not self.autoRTQASetup:
            self.files_processed.append(fname)
            self.iteration += 1
            self.isMainLoopEntered = False
            return

        logger.info('Call iteration for file "{}"', Path(fname).name)

        # Start elapsed time
        startingTime = time.time()

        self.previousIterStartTime = startingTime

        if self.iteration == 1 or autoRTQAMCTempl:
            with utils.timeit('  setup after first volume:'):
                self.eng.setupFirstVolume(fname, nargout=0)

        # Main logic
        # data preprocessing
        if config.USE_YIELD:
            self.call_timer.setInterval(np.int32(config.MAIN_LOOP_CALL_PERIOD / 3))
            prepr_vol_state = self.eng.preprVol(fname, self.iteration, background=True, nargout=0)
            while not prepr_vol_state.done():
                yield
        else:
            self.eng.preprVol(fname, self.iteration, background=False, nargout=0)

        # t3
        self.recorder.recordEvent(erd.Times.t3, self.iteration, time.time())
        self.updatePlugins()

        if self.windowRTQA:
            is_rtqa_volume = self.rtqa_output["show_vol"]
        else:
            is_rtqa_volume = False

        is_stat_map_created = bool(self.eng.evalin('base', 'mainLoopData.statMapCreated'))

        if self.imageViewMode == ImageViewMode.mosaic:
            self.updateMosaicViewAsync()

        if (is_rtqa_volume and config.FIRST_SNR_VOLUME < self.iteration) or \
                (is_stat_map_created and not is_rtqa_volume):
            self.updateOrthViewAsync()

        # spatio-temporal data processing
        with utils.timeit('  preprocess signal:'):
            self.outputSamples = self.eng.preprSig(self.iteration)

        # t4
        self.recorder.recordEvent(erd.Times.t4, self.iteration, time.time())
        self.updatePlugins()

        if self.P['Type'] == 'DCM':
            if self.isCalculateDcm:
                # here calc already in progress
                dcmBlocks = np.array(self.P['endDCMblock'][0])
                lastBlockIteration = self.iteration - self.P['nrBlankScans'] - self.P['nrSkipVol']
                lastBlankScan = len(np.where(dcmBlocks == lastBlockIteration)[0]) > 0
                if lastBlankScan:
                    logger.info('get lastBlankScan...')
                    logger.info('dcm blocks {}', dcmBlocks)

                if (self.tagFuture.done() and self.oppFuture.done()) or lastBlankScan:
                    # t12 last DCM model computation is done
                    self.recorder.recordEvent(erd.Times.t12, self.iteration, time.time())
                    dcmTagLE = self.tagFuture.result()
                    dcmOppLE = self.oppFuture.result()
                    logger.info('DCM calculated')

                    # feedback estimation
                    self.displayData = self.eng.nfbCalc(self.iteration, self.displayData, dcmTagLE, dcmOppLE, True,
                                                        nargout=1)

                    # t5
                    self.recorder.recordEvent(erd.Times.t5, self.iteration, time.time())
                    self.isCalculateDcm = False

            else:
                self.isCalculateDcm = self.eng.dcmBegin(self.iteration, nargout=1)

                if self.isCalculateDcm:
                    # display blank screen in ptb helper before calculate DCM
                    if config.USE_PTB:
                        self.displayData['displayBlankScreen'] = 1
                        self.displayScreen()
                        QApplication.processEvents()
                        self.endDisplayEvent.wait()
                        self.endDisplayEvent.clear()

                    # Parallel DCM computing on two matlab engines
                    # t11 first DCM model computation started
                    self.recorder.recordEvent(erd.Times.t11, self.iteration, time.time())

                    if config.USE_MATLAB_MODEL_HELPER:
                        self.tagFuture = self.mlModelHelper.engine.dcmCalc(
                            'Tag', nargout=1, background=True)
                        self.oppFuture = self.mlModelHelper.engine.dcmCalc(
                            'Opp', nargout=1, background=True)
                    elif config.USE_PTB_HELPER:
                        self.tagFuture = self.mlPtbDcmHelper.engine.dcmCalc(
                            'Tag', nargout=1, background=True)
                        self.oppFuture = self.mlPtbDcmHelper.engine.dcmCalc(
                            'Opp', nargout=1, background=True)
                    else:
                        dcmTagLE = []
                        dcmOppLE = []

                else:
                    dcmTagLE = []
                    dcmOppLE = []

        elif self.P['Type'] == 'SVM':
            # feedback estimation
            self.displayData = self.eng.nfbCalc(self.iteration, self.displayData, nargout=1)

            # t5
            self.recorder.recordEvent(erd.Times.t5, self.iteration, time.time())

        elif self.P['Type'] in ['PSC', 'Corr']:
            self.displayData = self.eng.nfbCalc(self.iteration, self.displayData, nargout=1)

            # t5
            self.recorder.recordEvent(erd.Times.t5, self.iteration, time.time())

            if self.P['Prot'] != 'Inter':
                if config.USE_PTB:
                    if self.displayData:
                        if self.P['Prot'] == 'ContTask':
                            # Here task condition is evaluated: if condition is 3 (task) and the current
                            # iteration corresponds with the onset of a task block (kept in TaskFirstVol)
                            # taskseq is set to one. While set to 1, Display in ptbScreen.py
                            # will use the taskse flag to call the ptbTask function.
                            # cond = self.eng.evalin('base', 'mainLoopData.displayData.condition')
                            cond = self.displayData['condition']
                            if cond == 3 and int(self.P['TaskFirstVol'][0][self.iteration - 1]) == 1:
                                self.displayData['taskseq'] = 1
                                self.displayScreen()
                                QApplication.processEvents()
                                self.endDisplayEvent.wait()
                                self.endDisplayEvent.clear()
                            else:
                                self.displayData['taskseq'] = 0
                                self.displayData['displayStage'] = 'feedback'
                                self.displayScreen()
                        else:
                            self.displayData['taskseq'] = 0
                            self.displayData['displayStage'] = 'feedback'
                            self.displayScreen()

        if self.displayData:
            if config.USE_SHAM:
                self.displayData['dispValue'] = self.shamData[self.iteration - self.P['nrSkipVol'] - 1]

            if config.USE_UDP_FEEDBACK:
                logger.info('Sending by UDP - dispValue = {}', self.displayData['dispValue'])
                self.udpSender.send_data(self.displayData['dispValue'])

            self.displaySamples.append(self.displayData['dispValue'])

        # main logic end

        init = self.iteration == (self.P['nrSkipVol'] + 1)

        # rtQA calculation for time-series
        if bool(self.outputSamples) and self.windowRTQA:

            dataRealRaw = np.array(self.outputSamples['rawTimeSeries'], ndmin=2)
            dataGLM = np.array(self.eng.evalin('base', 'mainLoopData.glmProcTimeSeries(:,end)'), ndmin=2)
            dataProc = np.array(self.outputSamples['kalmanProcTimeSeries'], ndmin=2)
            dataMC = np.array(self.outputSamples['motCorrParam'], ndmin=2)
            n = len(dataRealRaw[0, :]) - 1
            dataRaw = dataRealRaw[:, n]

            if n == 0:
                offsetMCParam = np.array(self.eng.evalin('base', 'P.offsetMCParam'), ndmin=1)
                self.rtqa_input["offset_mc"] = offsetMCParam

            if self.P['Type'] != 'DCM':
                betaCoeff = np.array(
                    self.eng.evalin('base', 'rtQA_matlab.linRegr(:,mainLoopData.indVolNorm)'), ndmin=2)
            else:
                betaCoeff = np.zeros((int(self.P['NrROIs']), 1))

            posSpikes = np.array(self.eng.evalin('base', 'rtQA_matlab.kalmanSpikesPos(:,mainLoopData.indVolNorm)'),
                                 ndmin=2)
            negSpikes = np.array(self.eng.evalin('base', 'rtQA_matlab.kalmanSpikesNeg(:,mainLoopData.indVolNorm)'),
                                 ndmin=2)

            if self.P['Type'] == 'DCM' and (self.iteration - self.P['nrSkipVol']) in self.P['beginDCMblock'][0]:
                isNewDCMBlock = True
            else:
                isNewDCMBlock = False

            if self.P['Type'] != 'DCM' and not self.P['isAutoRTQA']:
                dataNoRegGLM = np.squeeze(np.array(
                    self.eng.evalin('base', 'mainLoopData.noRegGlmProcTimeSeries(:,end)'), ndmin=2), axis=1)
            else:
                dataNoRegGLM = np.array([])

            self.rtqa_input["raw_ts"] = dataRaw
            self.rtqa_input["glm_ts"] = dataGLM
            self.rtqa_input["no_reg_glm_ts"] = dataNoRegGLM
            self.rtqa_input["proc_ts"] = dataProc[:, n]
            self.rtqa_input["mc_ts"] = dataMC[n, :]
            self.rtqa_input["beta_coeff"] = betaCoeff
            self.rtqa_input["pos_spikes"] = posSpikes
            self.rtqa_input["neg_spikes"] = negSpikes
            self.rtqa_input["is_new_dcm_block"] = isNewDCMBlock
            self.rtqa_input["iteration"] = n
            self.rtqa_input["roi_checked"] = self.selectedRoi
            self.rtqa_input["data_ready"] = True
            if self.windowRTQA.isVisible():
                self.windowRTQA.plotRTQA()
            self.rtqa_input["calc_ready"] = False

        with utils.timeit('  Drawings:'):
            self.drawRoiPlots(init)
            self.drawMcPlots(init)

        # Stop Elapsed time and record
        elapsedTime = time.time() - startingTime
        self.recorder.recordEventDuration(erd.Times.d0, self.iteration, elapsedTime)
        self.files_processed.append(fname)

        self.leElapsedTime.setText('{:.4f}'.format(elapsedTime))
        self.leCurrentVolume.setText('%d' % self.iteration)

        # logger.info('**********  {}', self.recorder.files[-1])
        logger.info('Elapsed time: {:.4f} s', elapsedTime)

        QApplication.processEvents()

        if self.iteration == self.P['NrOfVolumes']:
            logger.info('Last iteration reached...')
            self.stop()

        self.iteration += 1
        self.call_timer.setInterval(config.MAIN_LOOP_CALL_PERIOD)
        self.isMainLoopEntered = False

    # --------------------------------------------------------------------------
    def getFileSearchString(self, file_name_template, path, ext):
        file_series_part = re.findall(r"\{#:(\d+)\}", file_name_template)
        file_num_part = re.findall(r"_\d+_(\d+.\w+)", file_name_template)
        if len(file_series_part) > 0:
            file_series_len = int(file_series_part[0])
            fname = path.stem[:-file_series_len]
            search_string = '%s*%s' % (fname, ext)
        elif len(file_num_part) > 0:
            fname = file_name_template.replace(file_num_part[0], "*")
            search_string = '%s%s' % (fname, ext)
        else:
            search_string = '*%s' % ext

        return search_string

    # --------------------------------------------------------------------------
    def startInOfflineMode(self):
        path = Path(self.P['WatchFolder'], self.P['FirstFileName'])
        ext = re.findall(r"\.\w*$", str(path))
        if not ext:
            if self.P['DataType'] == 'IMAPH':
                ext = config.IMAPH_FILES_EXTENSION
            else:  # dicom as default
                ext = config.DICOM_FILES_EXTENSION
        else:
            ext = ext[-1]

        searchString = self.getFileSearchString(self.P['FirstFileNameTxt'], path, ext)
        path = path.parent / searchString

        files = sorted(glob.glob(str(path)))

        if not files:
            logger.info("No files found in offline mode. Check WatchFolder settings!")
            self.stop()
            return

        self.files_queue = queue.Queue()

        for f in files:
            self.files_queue.put(f)

        self.call_timer.start(config.MAIN_LOOP_CALL_PERIOD)

    # --------------------------------------------------------------------------
    def startFilesystemWatching(self):
        self.files_queue = queue.Queue()

        path = Path(self.P['WatchFolder'], self.P['FirstFileName'])

        ext = re.findall(r"\.\w*$", str(path))
        if not ext:
            if self.P['DataType'] == 'IMAPH':
                ext = config.IMAPH_FILES_EXTENSION
            else:  # dicom as default
                ext = config.DICOM_FILES_EXTENSION
        else:
            ext = ext[-1]

        searchString = self.getFileSearchString(self.P['FirstFileNameTxt'], path, ext)
        path = path.parent

        logger.info('Searching for {} in {}', searchString, path)

        event_handler = CreateFileEventHandler(
            searchString, self.files_queue, self.recorder)

        self.fs_observer = Observer()
        self.fs_observer.schedule(
            event_handler, str(path), recursive=True)

        self.call_timer.start()
        self.fs_observer.start()

    # --------------------------------------------------------------------------
    def makeRoiPlotLegend(self):
        roiNames = []
        dyn = ' dyn' if self.P['DynROI'] else ''

        for roiName in self.P['ROINames']:
            roiName = Path(roiName).stem
            if len(roiName) > config.MAX_ROI_NAME_LENGTH:
                roiName = roiName[:2] + '..' + roiName[-2:] + dyn
            roiNames.append(roiName)

        self.labelPlotLegend.setText('')
        legendText = '<html><head/><body><p>'

        numRoi = int(self.P['NrROIs'])

        for i, n, c in zip(range(1, numRoi + 1), roiNames, config.ROI_PLOT_COLORS):
            cname = pg.mkPen(color=c).color().name()
            legendText += (
                    '<span style="font-weight:600;color:{};">'.format(cname)
                    + 'ROI_{} {}</span>, '.format(i, n))

        legendText += (
            '<span style="font-weight:600;color:k;">Operation: {}</span>'.format(self.P['RoiAnatOperation']))
        legendText += '</p></body></html>'

        self.labelPlotLegend.setText(legendText)

    # --------------------------------------------------------------------------
    def setupRoiPlots(self):
        self.makeRoiPlotLegend()

        rawTimeSeries = self.rawRoiPlot.getPlotItem()
        proc = self.procRoiPlot.getPlotItem()
        norm = self.normRoiPlot.getPlotItem()

        rawTimeSeries.clear()
        proc.clear()
        norm.clear()

        if self.P['isAutoRTQA']:
            grid = True
        else:
            grid = False

        self.basicSetupPlot(rawTimeSeries, grid)
        self.basicSetupPlot(proc, grid)
        self.basicSetupPlot(norm, grid)

        self.drawMusterPlot(rawTimeSeries)
        self.drawMusterPlot(proc)
        self.drawMusterPlot(norm)
        rawTimeSeries.setYRange(-1, 1, padding=0.0)
        proc.setYRange(-1, 1, padding=0.0)
        norm.setYRange(-1, 1, padding=0.0)

    # --------------------------------------------------------------------------
    def setupMcPlots(self):
        mctrrot = self.mcPlot.getPlotItem()
        self.basicSetupPlot(mctrrot)

    # --------------------------------------------------------------------------
    def basicSetupPlot(self, plotitem, grid=True):
        if not self.P['isAutoRTQA']:
            lastInds = np.zeros((self.musterInfo['condTotal'],))
            for i in range(self.musterInfo['condTotal']):
                lastInds[i] = self.musterInfo['tmpCond' + str(i + 1)][-1][1]
            xmax = max(lastInds)
        else:
            xmax = (self.P['NrOfVolumes'] - self.P['nrSkipVol'])

        plotitem.disableAutoRange(axis=pg.ViewBox.XAxis)
        plotitem.setXRange(1, xmax, padding=0.0)
        plotitem.showGrid(x=grid, y=grid, alpha=config.PLOT_GRID_ALPHA)

    # --------------------------------------------------------------------------
    def initialize(self, start=True):
        ts = time.time()

        self.isInitialized = False

        if not runmatlab.connect_to_matlab(start=start):
            if not start:
                logger.warning('There is no main Matlab session yet. Press "Initialize" button.')
            return

        logger.info('Using Matlab session "{}" as MAIN', self.mlMainHelper.name)
        if config.USE_PTB_HELPER:
            logger.info('Using Matlab session "{}" for PTB', self.mlPtbDcmHelper.name)

        if config.USE_MATLAB_MODEL_HELPER:
            logger.info('Using Matlab session "{}" for Model Helper', self.mlModelHelper.name)

        self.mlMainHelper.prepare()

        if not (config.USE_MATLAB_MODEL_HELPER) and not (config.USE_PTB_HELPER):
            logger.warning('There is no main Matlab model helper. DCM calculation is not possible.')
        if config.USE_PTB_HELPER:
            self.mlPtbDcmHelper.prepare()
        if config.USE_MATLAB_MODEL_HELPER:
            self.mlModelHelper.prepare()

        self.eng = self.mlMainHelper.engine

        self.eng.workspace['P'] = self.P
        self.eng.workspace['mainLoopData'] = self.mainLoopData
        self.eng.workspace['rtQA_matlab'] = self.rtQA_matlab

        self.resetDone = True
        self.isInitialized = True

        if not config.AUTO_RTQA:
            self.frameParams.setEnabled(True)
            self.frameShortParams.setEnabled(True)
            self.btnSetup.setEnabled(self.isSetFileChosen)
            self.pluginWindow = plugin.PluginWindow()
            self.btnPlugins.setEnabled(True)
        else:
            self.frameAutoRtqaParams.setEnabled(True)
            self.btnChooseRoiFolder.setEnabled(True)
            self.btnChooseWatchFolder3.setEnabled(True)
            self.label_15.setEnabled(True)
            self.label_16.setEnabled(True)
            self.leRoiFolder.setEnabled(True)
            self.leWatchFolder3.setEnabled(True)
            self.cbOfflineMode3.setEnabled(True)
            self.label_17.setEnabled(True)
            self.label_18.setEnabled(True)
            self.label_45.setEnabled(True)
            self.sbImgSerNr3.setEnabled(True)
            self.sbNFRunNr3.setEnabled(True)
            self.sbSkipVol3.setEnabled(True)
            self.sbVolumesNr3.setEnabled(True)
            self.label_44.setEnabled(True)
            self.label_46.setEnabled(True)
            self.label_11.setEnabled(True)
            self.label_21.setEnabled(True)
            self.label_24.setEnabled(True)
            self.sbSkipVol3.setEnabled(True)
            self.sbMatrixSizeX3.setEnabled(True)
            self.sbMatrixSizeY3.setEnabled(True)
            self.sbSlicesNr3.setEnabled(True)
            self.leFirstFile3.setEnabled(True)
            self.btnStart.setEnabled(True)
            self.presetupAutoRTQA()

        self.autoRTQASetup = False
        logger.info("Initialization finished ({:.2f} s)", time.time() - ts)

    # --------------------------------------------------------------------------
    def reset(self):
        self.P = {}
        self.mainLoopData = {}
        self.rtQA_matlab = {}
        self.reultFromHelper = None
        self.reachedFirstFile = False
        self.autoRTQASetup = False
        if self.orth_view:
            self.view_form_input["is_stopped"] = True
            self.view_form_input = None
            self.view_form_output = None
            self.orth_view.terminate()
        self.orth_view = None

        if self.calc_rtqa:
            self.calc_rtqa.terminate()
            self.calc_rtqa = None
            self.rtqa_input = None
            self.rtqa_output = None
        self.main_loop = None

        self.eng.workspace['P'] = self.P
        self.eng.workspace['mainLoopData'] = self.mainLoopData
        self.eng.workspace['rtQA_matlab'] = self.rtQA_matlab
        self.fFinNFB = False
        self.outputSamples = {}
        self.musterInfo = {}
        self.iteration = 1
        self.preiteration = 0
        self.files_processed = []
        self.files_exported = []
        self.files_queue = queue.Queue()

        self.mcPlot.getPlotItem().clear()
        self.procRoiPlot.getPlotItem().clear()
        self.rawRoiPlot.getPlotItem().clear()
        self.normRoiPlot.getPlotItem().clear()

        self.pos_map_thresholds_widget.reset()
        self.neg_map_thresholds_widget.reset()

        self.mosaicImageView.clear()
        self.orthView.clear()

        self.isMainLoopEntered = False
        self.typicalFileSize = 0
        self.displayQueue = queue.Queue()
        self.resetDone = True

    # --------------------------------------------------------------------------
    def setup(self):
        if not self.isInitialized:
            logger.error("Couldn't connect Matlab.\n PRESS INITIALIZE FIRST!")
            return

        with utils.timeit('Setup finished:'):
            logger.info("Setup application...")

            self.orthViewInitialize = True
            self.orthViewUpdateCheckTimer.stop()
            self.mosaicViewUpdateCheckTimer.stop()

            # for multiply setup
            # TODO: Is this flag necessary?
            if not self.resetDone:
                self.reset()
            # -self.chooseSetFile(self.leSetFile.text())

            self.actualize()
            self.isOffline = self.cbOfflineMode.isChecked()

            memMapFile = self.getFreeMemmapFilename()
            memMapFile = memMapFile.replace('OrthView', 'shared')
            logger.info('memMapFile: {}', memMapFile)
            self.P['memMapFile'] = memMapFile

            self.eng.workspace['P'] = self.P
            self.previousIterStartTime = 0
            self.displaySamples = []

            with utils.timeit("  Load protocol data:"):
                self.loadJsonProtocol()

            with utils.timeit("  Selecting ROI:"):
                self.selectRoi()

            self.P.update(self.eng.workspace['P'])

            logger.info("  Setup plots...")
            if not self.P['isAutoRTQA']:
                self.createMusterInfo()

            self.setupRoiPlots()
            self.setupMcPlots()

            with utils.timeit('  initMainLoopData:'):
                self.initMainLoopData()

            self.view_form_init()

            self.roiDict = dict()
            self.selectedRoi = []
            roi_menu = QMenu()
            roi_menu.triggered.connect(self.onRoiChecked)
            self.roiSelectorBtn.setMenu(roi_menu)
            nrROIs = int(self.P['NrROIs'])
            for i in range(nrROIs):
                if self.P['isRTQA'] and i + 1 == nrROIs:
                    roi = 'Whole brain ROI'
                else:
                    roi = 'ROI_{}'.format(i + 1)
                roi_action = roi_menu.addAction(roi)
                roi_action.setCheckable(True)
                if not (self.P['isRTQA'] and i + 1 == nrROIs):
                    roi_action.setChecked(True)
                    self.roiDict[roi] = True
                    self.selectedRoi.append(i)

            action = roi_menu.addAction("All")
            action.setCheckable(False)

            action = roi_menu.addAction("None")
            action.setCheckable(False)

            self.roiSelectorBtn.setEnabled(True)

            if config.USE_SHAM:
                logger.warning("Sham feedback has been selected")
                fext = Path(self.P['ShamFile']).suffix
                if fext == '.txt':  # expect a textfile with float numbers in a single  column or row
                    NFBdata = np.loadtxt(self.P['ShamFile'], unpack=False)
                elif fext == '.mat':  # expect "mainLoopData"
                    NFBdata = loadmat(self.P['ShamFile'])['dispValues']

                dispValues = list(NFBdata.flatten())
                if len(dispValues) != self.P['NrOfVolumes'] - self.P['nrSkipVol']:
                    logger.error(
                        "Number of display values ({:d}) in {} does not correspond to number of volumes ({:d} - {:d} skipped).\n SELECT ANOTHER SHAM FILE".format(
                            len(dispValues), self.P['ShamFile'], self.P['NrOfVolumes'], self.P['nrSkipVol']))
                    return
                self.shamData = [float(v) for v in dispValues]
                logger.info("Sham data has been loaded")

            if config.USE_PTB:
                self.stopDisplayThread = False
                self.displayThread = threading.Thread(target=self.onEventDisplay)
                self.displayThread.start()

                with utils.timeit("  Preparation of PTB Screen:"):
                    sid = self.cbScreenId.currentIndex() + 1
                    path = Path(self.P['nfbDataFolder'])
                    eventRecordsPath = path / ('TimeVectors_display_' + str(self.P['NFRunNr']).zfill(2) + '.txt')

                    ptbP = {}
                    ptbP['eventRecordsPath'] = str(eventRecordsPath)
                    ptbP['TargDIAM'] = self.P['TargDIAM']
                    ptbP['TargRAD'] = self.P['TargRAD']
                    ptbP['TargANG'] = self.P['TargANG']
                    ptbP['NFRunNr'] = self.P['NFRunNr']
                    ptbP['Type'] = self.P['Type']
                    ptbP['WorkFolder'] = self.P['WorkFolder']
                    ptbP['DisplayFeedbackFullscreen'] = self.P['DisplayFeedbackFullscreen']
                    ptbP['Prot'] = self.P['Prot']
                    ptbP['FeedbackValDec'] = self.P['FeedbackValDec']
                    if self.P['Prot'] == 'ContTask':
                        ptbP['TaskFolder'] = self.P['TaskFolder']

                    self.ptbScreen.initialize(
                        sid, self.P['WorkFolder'], self.P['Prot'], ptbP)

            if config.USE_MRPULSE:
                (self.pulseProc, self.mrPulses) = mrpulse.start(self.P['NrOfVolumes'], self.displayEvent)

            self.recorder.initialize(self.P['NrOfVolumes'])
            self.eng.nfbInitReward(nargout=0)

            self.initUdpSender()

            with utils.timeit("  Initialize plugins:"):
                excPlugins = []
                for i in range(len(self.plugins)):
                    try:
                        self.plugins[i].initialize()
                    except KeyError as e:
                        logger.warning("Initializing plugin '{}' failed - {} not found in settings".format(
                            self.plugins[i].module.META['plugin_name'], str(e)))
                        excPlugins.append(i)
                for i in excPlugins:
                    del self.plugins[i]

            self.btnStart.setEnabled(True)
            if self.P['isRTQA']:
                self.rtqa_init()

            # self.eng.assignin('base', 'imageViewMode', int(self.imageViewMode), nargout=0)
            self.cbImageViewMode.setEnabled(False)
            self.cbImageViewMode.setCurrentIndex(0)
            self.isStopped = False

    # --------------------------------------------------------------------------
    def presetupAutoRTQA(self):

        if not self.isInitialized:
            logger.error("Couldn't connect Matlab.\n PRESS INITIALIZE FIRST!")
            return

        with utils.timeit('Setup finished:'):
            logger.info("Setup application...")

            self.btnRTQA.setEnabled(False)
            self.orthViewInitialize = True

            self.orthViewUpdateCheckTimer.stop()
            self.mosaicViewUpdateCheckTimer.stop()

            if not self.resetDone:
                self.reset()

            self.view_form_input = multiprocessing.Manager().dict()
            self.view_form_input["ready"] = False
            self.view_form_input["done_mosaic_templ"] = False
            self.view_form_input["done_mosaic_overlay"] = False
            self.view_form_input["done_orth"] = False

            self.actualizeAutoRTQA()
            self.isOffline = self.cbOfflineMode3.isChecked()

            memMapFile = self.getFreeMemmapFilename()
            memMapFile = memMapFile.replace('OrthView', 'shared')
            logger.info('memMapFile: {}', memMapFile)
            self.P['memMapFile'] = memMapFile

            if not config.SELECT_ROIS:
                self.P['NrROIs'] = 1
            self.eng.workspace['P'] = self.P
            self.previousIterStartTime = 0
            self.displaySamples = []

            self.recorder.initialize(self.P['NrOfVolumes'])

    # --------------------------------------------------------------------------
    def setupAutoRTQA(self):

        if not self.P['useEPITemplate']:
            dcm = pydicom.dcmread(self.P['MCTempl'])
            if not (hasattr(dcm, 'ImagePositionPatient') and hasattr(dcm, 'ImageOrientationPatient')):
                logger.error(
                    "DICOM template has no ImagePositionPatient and ImageOrientationPatient and could not be used as EPI template\nPlease, check DICOM export or use NII EPI template\n")
                self.fFinNFB = False
                self.stop()
                return

        with utils.timeit("  Load protocol data:"):
            self.loadJsonProtocol()

        with utils.timeit("  Selecting ROI:"):
            if config.SELECT_ROIS:
                self.selectRoi()

        with utils.timeit('  initMainLoopData:'):
            self.eng.setupProcParams(nargout=0)

            if self.P['isRTQA']:
                self.eng.epiWholeBrainROI(nargout=0)

            with utils.timeit("Receiving 'P' from Matlab:"):
                self.P = self.eng.workspace['P']

        self.P.update(self.eng.workspace['P'])

        logger.info("  Setup plots...")
        self.setupRoiPlots()
        self.setupMcPlots()

        self.view_form_init()

        self.roiDict = dict()
        self.selectedRoi = []
        roi_menu = QMenu()
        roi_menu.triggered.connect(self.onRoiChecked)
        self.roiSelectorBtn.setMenu(roi_menu)
        nrROIs = int(self.P['NrROIs'])
        for i in range(nrROIs):
            if not config.SELECT_ROIS or i + 1 == nrROIs:
                roi = 'Whole brain ROI'
            else:
                roi = 'ROI_{}'.format(i + 1)
            roi_action = roi_menu.addAction(roi)
            roi_action.setCheckable(True)
            if config.SELECT_ROIS and not (i + 1 == nrROIs) or not config.SELECT_ROIS:
                roi_action.setChecked(True)
                self.roiDict[roi] = True
                self.selectedRoi.append(i)

        action = roi_menu.addAction("All")
        action.setCheckable(False)

        action = roi_menu.addAction("None")
        action.setCheckable(False)

        self.roiSelectorBtn.setEnabled(True)

        self.initUdpSender()

        self.rtqa_init()

        self.autoRTQASetup = True
        self.cbImageViewMode.setCurrentIndex(0)
        self.cbImageViewMode.model().item(1).setEnabled(False)
        self.isStopped = False

    # --------------------------------------------------------------------------
    def view_form_init(self):

        nrROIs = int(self.eng.evalin('base', 'P.NrROIs'))
        x = self.P['MatrixSizeX']
        y = self.P['MatrixSizeY']
        z = self.P['NrOfSlices']
        ROI_vols = np.zeros((nrROIs, x, y, z))
        ROI_mats = np.zeros((nrROIs, 4, 4))
        if self.P['Type'] == 'DCM':
            if self.P['isRTQA']:
                # For DCM+rtQA, ROIs are stored in ROIsAnat and whole-brain EPI ROI is in ROIs.
                # ROIsAnat and whole-brain EPI ROI are transferred from Matlab.
                # For definition of nrROIs, see selectROI.m
                for i in range(nrROIs - 1):
                    ROI_vols[i] = np.array(self.eng.evalin('base', 'ROIsAnat(' + str(i + 1) + ').vol'), ndmin=3)
                    ROI_mats[i] = np.array(self.eng.evalin('base', 'ROIsAnat(' + str(i + 1) + ').mat'), ndmin=2)
                ROI_vols[nrROIs - 1] = np.array(self.eng.evalin('base', 'ROIs(end).vol'), ndmin=3)
                ROI_mats[nrROIs - 1] = np.array(self.eng.evalin('base', 'ROIs(end).mat'), ndmin=2)
            else:
                for i in range(nrROIs):
                    ROI_vols[i] = np.array(self.eng.evalin('base', 'ROIsAnat(' + str(i + 1) + ').vol'), ndmin=3)
                    ROI_mats[i] = np.array(self.eng.evalin('base', 'ROIsAnat(' + str(i + 1) + ').mat'), ndmin=2)
        else:
            for i in range(nrROIs):
                ROI_vols[i] = np.array(self.eng.evalin('base', 'ROIs(' + str(i + 1) + ').vol'), ndmin=3)
                ROI_mats[i] = np.array(self.eng.evalin('base', 'ROIs(' + str(i + 1) + ').mat'), ndmin=2)

        # # shared variables for OrthView process
        self.view_form_input = multiprocessing.Manager().dict()
        self.view_form_input["nr_ROIs"] = nrROIs
        self.view_form_input["ROI_vols"] = ROI_vols
        self.view_form_input["ROI_mats"] = ROI_mats
        self.view_form_input["cursor_pus"] = []
        self.view_form_input["flags_planes"] = []
        self.view_form_input["bg_type"] = "bgEPI"
        self.view_form_input["is_rtqa"] = False
        self.view_form_input["is_neg"] = self.negMapCheckBox.isChecked()
        self.view_form_input["is_ROI"] = config.USE_ROI
        if config.AUTO_RTQA:
            self.view_form_input["anat_volume"] = None
        else:
            self.view_form_input["anat_volume"] = self.P['StructBgFile']
        self.view_form_input["epi_volume"] = self.P['MCTempl']
        if config.AUTO_RTQA and not config.USE_EPI_TEMPLATE:
            self.view_form_input["epi_volume_type"] = "dcm"
        else:
            self.view_form_input["epi_volume_type"] = "nii"
        self.view_form_input["rtQA_volume"] = []
        self.view_form_input["stat_volume"] = str(self.eng.evalin('base', 'P.memMapFile')).replace('shared', 'statVol')
        self.view_form_input["mat"] = np.array(self.eng.evalin('base', 'mainLoopData.matTemplMotCorr'))
        self.view_form_input["dim"] = tuple([x, y, z])
        self.view_form_input["memmap_volume"] = self.P['memMapFile']
        self.view_form_input["view_mode"] = self.imageViewMode
        self.view_form_input["is_stopped"] = False
        self.view_form_input["auto_thr_pos"] = True
        self.view_form_input["auto_thr_neg"] = True
        self.view_form_input["ready"] = False
        self.view_form_input["overlay_ready"] = False
        self.view_form_input["done_mosaic_templ"] = False
        self.view_form_input["done_mosaic_overlay"] = False
        self.view_form_input["done_orth"] = False

        self.view_form_output = multiprocessing.Manager().dict()
        self.view_form_output["mosaic_templ"] = np.zeros((1, 1))
        self.view_form_output["mosaic_pos_overlay"] = None
        self.view_form_output["mosaic_neg_overlay"] = None
        self.view_form_output["ROI_t"] = np.zeros((1, 1))
        self.view_form_output["ROI_c"] = np.zeros((1, 1))
        self.view_form_output["ROI_s"] = np.zeros((1, 1))
        self.view_form_output["back_t"] = np.zeros((1, 1))
        self.view_form_output["back_c"] = np.zeros((1, 1))
        self.view_form_output["back_s"] = np.zeros((1, 1))
        self.view_form_output["overlay_t"] = np.zeros((1, 1))
        self.view_form_output["overlay_c"] = np.zeros((1, 1))
        self.view_form_output["overlay_s"] = np.zeros((1, 1))
        self.view_form_output["neg_overlay_t"] = np.zeros((1, 1))
        self.view_form_output["neg_overlay_c"] = np.zeros((1, 1))
        self.view_form_output["neg_overlay_s"] = np.zeros((1, 1))
        self.view_form_output["pos_thresholds"] = np.array([1, 255])
        self.view_form_output["neg_thresholds"] = np.array([1, 255])

        self.orth_view = volviewformation.VolViewFormation(self.view_form_input, self.view_form_output)
        self.orth_view.start()

    # --------------------------------------------------------------------------
    def rtqa_init(self):

        self.btnRTQA.setEnabled(True)

        self.rtqa_input = multiprocessing.Manager().dict()
        self.rtqa_input["nr_rois"] = self.P["NrROIs"]
        self.rtqa_input["dim"] = tuple([self.P['MatrixSizeX'], self.P['MatrixSizeY'], self.P['NrOfSlices']])
        self.rtqa_input["wb_roi_indexes"] = np.array(self.eng.evalin('base', 'ROIs(end).voxelIndex'),
                                                     dtype=np.int32, ndmin=2)
        wb_mask = np.ones((self.P['MatrixSizeX'] * self.P['MatrixSizeY'] * self.P['NrOfSlices'],))
        wb_mask[self.rtqa_input["wb_roi_indexes"]] = 0
        self.rtqa_input["wb_mask"] = wb_mask.astype(bool)
        self.rtqa_input["muster_info"] = self.musterInfo
        self.rtqa_input["xrange"] = self.P['NrOfVolumes'] - self.P['nrSkipVol']
        self.rtqa_input["is_auto_rtqa"] = self.P["isAutoRTQA"]
        self.rtqa_input["roi_checked"] = self.selectedRoi
        if not config.AUTO_RTQA:
            self.rtqa_input["ind_bas"] = np.array(self.P["inds"][0])
            self.rtqa_input["ind_cond"] = np.array(self.P["inds"][1])
        self.rtqa_input["volume"] = self.P["memMapFile"]
        self.rtqa_input["is_stopped"] = False
        self.rtqa_input["data_ready"] = False
        self.rtqa_input["calc_ready"] = False
        self.rtqa_input["roi_changed"] = False
        self.rtqa_input["raw_ts"] = []
        self.rtqa_input["glm_ts"] = []
        self.rtqa_input["no_reg_glm_ts"] = []
        self.rtqa_input["proc_ts"] = []
        self.rtqa_input["mc_ts"] = []
        self.rtqa_input["offset_mc"] = []
        self.rtqa_input["beta_coeff"] = []
        self.rtqa_input["pos_spikes"] = []
        self.rtqa_input["neg_spikes"] = []
        self.rtqa_input["is_new_dcm_block"] = True
        self.rtqa_input["iteration"] = 0
        self.rtqa_input["which_vol"] = 0
        self.rtqa_input["dvars_scale"] = self.P["scaleFactorDVARS"]
        self.rtqa_input["rtqa_vol_ready"] = False

        self.rtqa_output = multiprocessing.Manager().dict()
        self.rtqa_output["snr_vol"] = np.zeros(self.rtqa_input["dim"])
        self.rtqa_output["cnr_vol"] = np.zeros(self.rtqa_input["dim"])
        self.rtqa_output["show_vol"] = False
        self.rtqa_output["rSNR"] = []
        self.rtqa_output["rCNR"] = []
        self.rtqa_output["rMean"] = []
        self.rtqa_output["meanBas"] = []
        self.rtqa_output["meanCond"] = []
        self.rtqa_output["rVar"] = []
        self.rtqa_output["varBas"] = []
        self.rtqa_output["varCond"] = []
        self.rtqa_output["glmProcTimeSeries"] = []
        self.rtqa_output["rMSE"] = []
        self.rtqa_output["linTrendCoeff"] = []
        self.rtqa_output["rNoRegSNR"] = []
        self.rtqa_output["DVARS"] = []
        self.rtqa_output["excDVARS"] = []
        self.rtqa_output["mc_params"] = []
        self.rtqa_output["FD"] = []
        self.rtqa_output["MD"] = []
        self.rtqa_output["meanFD"] = []
        self.rtqa_output["meanMD"] = []
        self.rtqa_output["excFD"] = []
        self.rtqa_output["excMD"] = []
        self.rtqa_output["posSpikes"] = []
        self.rtqa_output["negSpikes"] = []

        if self.windowRTQA:
            self.windowRTQA.deleteLater()

        self.calc_rtqa = rtqa_calc.RTQACalculation(self.rtqa_input, self.rtqa_output)
        self.windowRTQA = rtqa_gui.RTQAWindow(self.calc_rtqa, self.rtqa_input, self.rtqa_output)
        self.calc_rtqa.start()

        self.windowRTQA.volumeCheckBox.stateChanged.connect(self.onShowRtqaVol)
        self.windowRTQA.volumeCheckBox.stateChanged.connect(self.onChangeNegMapPolicy)
        self.windowRTQA.comboBox.currentIndexChanged.connect(self.onModeChanged)

    # --------------------------------------------------------------------------
    def start(self):
        logger.info("*** Started ***")

        if self.P['isAutoRTQA']:
            self.presetupAutoRTQA()

        self.cbImageViewMode.setEnabled(True)
        self.pos_map_thresholds_widget.setEnabled(True)
        self.neg_map_thresholds_widget.setEnabled(True)
        self.btnPlugins.setEnabled(False)
        self.btnSetup.setEnabled(False)
        self.btnStart.setEnabled(False)
        self.btnStop.setEnabled(True)
        self.pbMoreParameters.setChecked(False)

        self.iteration = 1
        self.preiteration = 0
        self.fFinNFB = True

        if self.isOffline:
            if not config.USE_FAST_OFFLINE_LOOP:
                config.MAIN_LOOP_CALL_PERIOD = self.P['TR']
            self.startInOfflineMode()
        else:
            self.startFilesystemWatching()

        self.orthViewUpdateCheckTimer.stop()
        self.orthViewUpdateCheckTimer.start(30)
        self.mosaicViewUpdateCheckTimer.stop()
        self.mosaicViewUpdateCheckTimer.start(30)
        self.files_exported = []
        self.files_processed = []

    # --------------------------------------------------------------------------
    def stop(self):

        self.isStopped = True
        if self.windowRTQA:
            if not self.rtqa_input is None:
                self.rtqa_input["is_stopped"] = True
            self.eng.workspace['rtQA_python'] = self.calc_rtqa.dataPacking()
        self.btnStop.setEnabled(False)

        if 'isAutoRTQA' in self.P and not self.P['isAutoRTQA']:
            self.btnStart.setEnabled(False)
            self.btnSetup.setEnabled(True)
            self.btnPlugins.setEnabled(True)
        else:
            self.btnStart.setEnabled(True)
            self.btnSetup.setEnabled(False)
            self.btnPlugins.setEnabled(False)

        self.fs_observer.stop()
        self.call_timer.stop()

        if hasattr(config, 'USE_PTB') and config.USE_PTB:
            self.ptbScreen.deinitialize()
            if not self.stopDisplayThread:
                self.displayEvent.set()
                self.stopDisplayThread = True
                self.displayThread.join()
                self.stopDisplayThread = False
                self.displayEvent.clear()

        if config.USE_SLEEP_IN_STOP:
            time.sleep(2)

        self.resetDone = False

        try:
            while not self.nfbFinStarted.done():
                time.sleep(0.1)
        except AttributeError:
            self.nfbFinStarted = None

        if config.USE_MRPULSE and hasattr(self, 'mrPulses'):
            np_arr = mrpulse.toNpData(self.mrPulses)
            self.pulseProc.terminate()

        if self.iteration > 1 and self.P.get('nfbDataFolder'):
            path = Path(self.P['nfbDataFolder'])
            fname = path / ('TimeVectors_' + str(self.P['NFRunNr']).zfill(2) + '.txt')
            self.recorder.savetxt(str(fname))

        if self.fFinNFB:
            for i in range(len(self.plugins)):
                self.plugins[i].finalize()
            self.finalizeUdpSender()
            self.nfbFinStarted = self.eng.nfbSave(self.iteration, nargout=0, background=True)
            self.fFinNFB = False

        if self.recorder.records.shape[0] > 2:
            if self.recorder.records[0, erd.Times.d0] > 0:
                logger.info("Average elapsed time: {:.4f} s".format(
                    np.sum(self.recorder.records[1:, erd.Times.d0]) / self.recorder.records[0, erd.Times.d0]))

        logger.info('Finished.')

    # --------------------------------------------------------------------------
    def rtQA(self):
        self.windowRTQA.show()
        if self.isStopped:
            self.windowRTQA.plotRTQA()

    # --------------------------------------------------------------------------
    def onShowRtqaVol(self):

        self.windowRTQA.rtQAVolState()
        if self.isStopped:
            if self.imageViewMode == ImageViewMode.mosaic:
                self.updateMosaicViewAsync()
            else:
                self.updateOrthViewAsync()

    # --------------------------------------------------------------------------
    def onRoiChecked(self, action):
        if action.text() == "All":
            actList = self.roiSelectorBtn.menu().actions()
            actList = actList[0:-2]
            for act in actList:
                act.setChecked(True)
                self.roiDict[act.text()] = True
        elif action.text() == "None":
            actList = self.roiSelectorBtn.menu().actions()
            actList = actList[0:-2]
            for act in actList:
                act.setChecked(False)
                self.roiDict[act.text()] = False
        else:
            self.roiDict[action.text()] = action.isChecked()

        self.selectedRoi = np.where(list(self.roiDict.values()))[0]
        if self.windowRTQA:
            self.rtqa_input["roi_checked"] = self.selectedRoi

        self.drawRoiPlots(True)
        if self.isStopped:
            self.windowRTQA.plotRTQA()
            self.updateOrthViewAsync()

    # --------------------------------------------------------------------------
    def onModeChanged(self):

        if self.windowRTQA:
            self.windowRTQA.onComboboxChanged()
            self.onShowRtqaVol()

    # --------------------------------------------------------------------------
    def onChooseSetFile(self):
        if config.DONOT_USE_QFILE_NATIVE_DIALOG:
            fname = QFileDialog.getOpenFileName(
                self, "Select 'SET File'", str(self.settingFileName), 'ini files (*.ini)',
                options=QFileDialog.DontUseNativeDialog)[0]
        else:
            fname = QFileDialog.getOpenFileName(
                self, "Select 'SET File'", str(self.settingFileName), 'ini files (*.ini)')[0]

        fname = str(Path(fname))
        self.chooseSetFile(fname)

    # --------------------------------------------------------------------------
    def chooseSetFile(self, fname):
        if not fname:
            return

        if not Path(fname).is_file():
            return

        self.settingFileName = fname

        self.leSetFile.setText(fname)
        self.P['SetFile'] = fname

        self.settings = QSettings(fname, QSettings.IniFormat, self)
        self.loadSettingsFromSetFile()

        self.isSetFileChosen = True
        self.btnSetup.setEnabled(self.isInitialized)

    # --------------------------------------------------------------------------
    def onChooseWeightsFile(self):
        if config.DONOT_USE_QFILE_NATIVE_DIALOG:
            fname = QFileDialog.getOpenFileName(
                self, "Select 'Weights File'", self.leWeightsFile.text(), 'all files (*.*)',
                options=QFileDialog.DontUseNativeDialog)[0]
        else:
            fname = QFileDialog.getOpenFileName(
                self, "Select 'Weights File'", self.leWeightsFile.text(), 'all files (*.*)')[0]

        fname = str(Path(fname))
        self.chooseWeightsFile(fname)

    # --------------------------------------------------------------------------
    def chooseWeightsFile(self, fname):
        if not fname:
            return

        if not Path(fname).is_file():
            return

        self.leWeightsFile.setText(fname)
        self.P['WeightsFileName'] = fname

    # --------------------------------------------------------------------------
    def onChooseProtocolFile(self):
        fname = self.leProtocolFile.text()
        if config.DONOT_USE_QFILE_NATIVE_DIALOG:
            fname = QFileDialog.getOpenFileName(
                self, "Select Protocol File", fname, 'JPRT files (*.*)', options=QFileDialog.DontUseNativeDialog)[0]
        else:
            fname = QFileDialog.getOpenFileName(
                self, "Select Protocol File", fname, 'JPRT files (*.*)')[0]

        fname = str(Path(fname))
        if fname:
            self.leProtocolFile.setText(fname)
            self.P['ProtocolFile'] = fname

    # --------------------------------------------------------------------------
    def onChooseStructBgFile(self):
        if config.DONOT_USE_QFILE_NATIVE_DIALOG:
            fname = QFileDialog.getOpenFileName(
                self, "Select Structural File", str(config.ROOT_PATH), 'Template files (*.nii)',
                options=QFileDialog.DontUseNativeDialog)[0]
        else:
            fname = QFileDialog.getOpenFileName(
                self, "Select Structural File", str(config.ROOT_PATH), 'Template files (*.nii)')[0]

        fname = str(Path(fname))
        if fname:
            self.leStructBgFile.setText(fname)
            self.P['StructBgFile'] = fname

    # --------------------------------------------------------------------------
    def onChooseMCTemplFile(self):
        if config.DONOT_USE_QFILE_NATIVE_DIALOG:
            fname = QFileDialog.getOpenFileName(
                self, "Select MCTempl File", str(config.ROOT_PATH), 'Template files (*.nii)',
                options=QFileDialog.DontUseNativeDialog)[0]
        else:
            fname = QFileDialog.getOpenFileName(
                self, "Select MCTempl File", str(config.ROOT_PATH), 'Template files (*.nii)')[0]

        fname = str(Path(fname))
        if fname:
            if config.AUTO_RTQA and config.USE_EPI_TEMPLATE:
                self.leMCTempl3.setText(fname)
            else:
                self.leMCTempl.setText(fname)
            self.P['MCTempl'] = fname

    # --------------------------------------------------------------------------
    def onChooseFolder(self, name, le):
        dname = QFileDialog.getExistingDirectory(
            self, "Select '{}' directory".format(name), str(config.ROOT_PATH))
        dname = str(Path(dname))
        if dname:
            le.setText(dname)
            self.P[name] = dname

    # --------------------------------------------------------------------------
    def onChooseFile(self, name, le):
        if config.DONOT_USE_QFILE_NATIVE_DIALOG:
            fname = QFileDialog.getOpenFileName(
                self, "Select '{}' directory".format(name), str(config.ROOT_PATH), 'Any file (*.*)',
                options=QFileDialog.DontUseNativeDialog)[0]
        else:
            fname = QFileDialog.getOpenFileName(
                self, "Select '{}' directory".format(name), str(config.ROOT_PATH), 'Any file (*.*)')[0]

        fname = str(Path(fname))
        if fname:
            le.setText(fname)
            self.P[name] = fname

    # --------------------------------------------------------------------------
    def onChangeImageViewMode(self, index):
        if index == 0:
            stack_index = 0
            mode = ImageViewMode.mosaic
        elif index == 1:
            stack_index = 1
            mode = ImageViewMode.orthviewAnat
        else:
            stack_index = 1
            mode = ImageViewMode.orthviewEPI

        self.stackedWidgetImages.setCurrentIndex(stack_index)
        self.imageViewMode = mode
        self.view_form_input["view_mode"] = self.imageViewMode

        # if self.eng:
        #     self.eng.assignin('base', 'imageViewMode', int(mode), nargout=0)

        if self.cbImageViewMode.isEnabled():
            self.updateOrthViewAsync()
            self.onInteractWithMapImage()

    # --------------------------------------------------------------------------
    def updateMosaicViewAsync(self):

        if self.windowRTQA:
            is_snr_map_created = self.rtqa_input["rtqa_vol_ready"]
            is_rtqa_volume = self.rtqa_output["show_vol"]
        else:
            is_rtqa_volume = False
            is_snr_map_created = False

        is_stat_map_created = bool(self.eng.evalin('base', 'mainLoopData.statMapCreated'))

        self.view_form_input["is_rtqa"] = is_rtqa_volume
        if self.windowRTQA and self.view_form_input["is_rtqa"]:
            if self.rtqa_input["which_vol"] == 0:
                self.view_form_input["rtQA_volume"] = self.rtqa_output["snr_vol"]
            else:
                self.view_form_input["rtQA_volume"] = self.rtqa_output["cnr_vol"]
        if is_rtqa_volume:
            self.view_form_input["is_neg"] = False
        else:
            self.view_form_input["is_neg"] = self.negMapCheckBox.isChecked()
        self.view_form_input["overlay_ready"] = (is_stat_map_created and not is_rtqa_volume) \
                                                or (is_snr_map_created and is_rtqa_volume)
        self.view_form_input["ready"] = True

    # --------------------------------------------------------------------------
    def updateOrthViewAsync(self):
        if not self.orth_view:
            return

        if self.imageViewMode == ImageViewMode.orthviewEPI or self.P['isAutoRTQA']:
            bgType = 'bgEPI'
        else:
            bgType = 'BgStruct'

        is_rtqa_volume = self.rtqa_output["show_vol"] if self.windowRTQA else False

        # if not self.view_form_input["ready"]:
        self.view_form_input["view_mode"] = self.imageViewMode
        self.view_form_input["cursor_pus"] = self.currentCursorPos
        self.view_form_input["flags_planes"] = self.currentProjection.value
        self.view_form_input["bg_type"] = bgType
        self.view_form_input["is_rtqa"] = is_rtqa_volume
        if self.windowRTQA:
            if self.rtqa_input["which_vol"] == 0:
                self.view_form_input["rtQA_volume"] = self.rtqa_output["snr_vol"]
            else:
                self.view_form_input["rtQA_volume"] = self.rtqa_output["cnr_vol"]
        if is_rtqa_volume:
            self.view_form_input["is_neg"] = False
        else:
            self.view_form_input["is_neg"] = self.negMapCheckBox.isChecked()
        self.view_form_input["ready"] = True

    # --------------------------------------------------------------------------
    def onChangeOrthViewCursorPosition(self, pos, proj):
        self.currentCursorPos = pos
        self.currentProjection = proj

        logger.debug('New cursor coords {} for proj "{}" have been received', pos, proj.name)
        self.updateOrthViewAsync()

    # --------------------------------------------------------------------------
    def onInteractWithMapImage(self):
        sender = self.sender()

        if sender is self.pos_map_thresholds_widget:
            self.pos_map_thresholds_widget.auto_thresholds = False
            self.view_form_input["auto_thr_pos"] = False
            self.view_form_output["pos_thresholds"] = self.pos_map_thresholds_widget.get_thresholds()

        if sender is self.neg_map_thresholds_widget:
            self.neg_map_thresholds_widget.auto_thresholds = False
            self.view_form_input["auto_thr_neg"] = False
            self.view_form_output["neg_thresholds"] = self.neg_map_thresholds_widget.get_thresholds()

        if self.imageViewMode == ImageViewMode.mosaic:
            self.updateMosaicViewAsync()
        else:
            self.updateOrthViewAsync()

    # --------------------------------------------------------------------------
    def onCheckOrthViewUpdated(self):

        if self.view_form_input["done_orth"]:

            self.orthViewUpdateInProgress = True

            rgba_pos_map_image = None
            rgba_neg_map_image = None

            for proj in projview.ProjectionType:

                if proj == projview.ProjectionType.transversal:
                    bg_image = self.view_form_output['back_t']
                    rgba_pos_map_image = self.view_form_output['overlay_t']
                    if not self.view_form_input["is_rtqa"] and self.negMapCheckBox.isChecked():
                        rgba_neg_map_image = self.view_form_output['neg_overlay_t']
                elif proj == projview.ProjectionType.sagittal:
                    bg_image = self.view_form_output['back_s']
                    rgba_pos_map_image = self.view_form_output['overlay_s']
                    if not self.view_form_input["is_rtqa"] and self.negMapCheckBox.isChecked():
                        rgba_neg_map_image = self.view_form_output['neg_overlay_s']
                elif proj == projview.ProjectionType.coronal:
                    bg_image = self.view_form_output['back_c']
                    rgba_pos_map_image = self.view_form_output['overlay_c']
                    if not self.view_form_input["is_rtqa"] and self.negMapCheckBox.isChecked():
                        rgba_neg_map_image = self.view_form_output['neg_overlay_c']

                self.orthView.set_background_image(proj, bg_image)
                if rgba_pos_map_image is not None and rgba_pos_map_image.ndim == 3:
                    self.orthView.set_pos_map_image(proj, rgba_pos_map_image)
                if rgba_neg_map_image is not None and rgba_neg_map_image.ndim == 3:
                    self.orthView.set_neg_map_image(proj, rgba_neg_map_image)

            pos_thr = self.view_form_output["pos_thresholds"]
            self.pos_map_thresholds_widget.set_thresholds(pos_thr)

            if not self.view_form_input["is_rtqa"] and self.negMapCheckBox.isChecked():
                neg_thr = self.view_form_output["neg_thresholds"]
                self.neg_map_thresholds_widget.set_thresholds(neg_thr)

            roi_t = []
            roi_c = []
            roi_s = []
            for i in self.selectedRoi:
                roi_t.append(self.view_form_output["ROI_t"][i])
                roi_c.append(self.view_form_output["ROI_c"][i])
                roi_s.append(self.view_form_output["ROI_s"][i])

            self.orthView.set_roi(projview.ProjectionType.transversal, roi_t, self.selectedRoi)
            self.orthView.set_roi(projview.ProjectionType.coronal, roi_c, self.selectedRoi)
            self.orthView.set_roi(projview.ProjectionType.sagittal, roi_s, self.selectedRoi)

            if self.orthViewInitialize:
                self.orthView.reset_view()

            self.orthViewInitialize = False
            self.orthViewUpdateInProgress = False
            self.view_form_input["done_orth"] = False

    # --------------------------------------------------------------------------
    def onCheckMosaicViewUpdated(self):

        if self.view_form_input["done_mosaic_templ"] and self.iteration > 1:
            background_image = self.view_form_output["mosaic_templ"]
            if background_image.size > 0:
                self.mosaicImageView.set_background_image(background_image)
            else:
                return

            self.view_form_input["done_mosaic_templ"] = False

        # SNR/Stat map display
        if self.view_form_input["done_mosaic_overlay"]:

            rgba_pos_map_image = self.view_form_output["mosaic_pos_overlay"]
            pos_thr = self.view_form_output["pos_thresholds"]
            self.pos_map_thresholds_widget.set_thresholds(pos_thr)

            if rgba_pos_map_image is not None:
                self.mosaicImageView.set_pos_map_image(rgba_pos_map_image)

            if not self.view_form_input["is_rtqa"] and self.negMapCheckBox.isChecked():

                rgba_neg_map_image = self.view_form_output["mosaic_neg_overlay"]
                neg_thr = self.view_form_output["neg_thresholds"]
                self.neg_map_thresholds_widget.set_thresholds(neg_thr)

                if rgba_neg_map_image is not None:
                    self.mosaicImageView.set_neg_map_image(rgba_neg_map_image)

            self.view_form_input["done_mosaic_overlay"] = False

    # --------------------------------------------------------------------------
    def loadSettingsFromSetFile(self):

        if not config.AUTO_RTQA:
            # --- top ---
            self.leProtocolFile.setText(self.settings.value('StimulationProtocol', ''))
            self.leWorkFolder.setText(self.settings.value('WorkFolder', ''))
            self.leWatchFolder.setText(self.settings.value('WatchFolder', ''))
            if (self.settings.value('Type', '')) == 'DCM':
                self.leRoiAnatFolder.setText(self.settings.value('RoiAnatFolder', ''))
            else:
                self.leRoiAnatFolder.setText(self.settings.value('RoiFilesFolder', ''))
            self.leRoiAnatOperation.setText(self.settings.value('RoiAnatOperation', 'mean(norm_percValues)'))
            self.leRoiGroupFolder.setText(self.settings.value('RoiGroupFolder', ''))
            self.leStructBgFile.setText(self.settings.value('StructBgFile', ''))
            self.leMCTempl.setText(self.settings.value('MCTempl', ''))
            if (self.settings.value('Prot', '')) == 'ContTask':
                self.leTaskFolder.setText(self.settings.value('TaskFolder', ''))

            # --- middle ---
            self.leProjName.setText(self.settings.value('ProjectName', ''))
            self.leSubjectID.setText(self.settings.value('SubjectID', ''))
            self.leFirstFile.setText(self.settings.value('FirstFileNameTxt', '001_{Image Series No:06}_{#:06}.dcm'))
            self.sbNFRunNr.setValue(int(self.settings.value('NFRunNr', '1')))
            self.sbImgSerNr.setValue(int(self.settings.value('ImgSerNr', '1')))
            self.sbVolumesNr.setValue(int(self.settings.value('NrOfVolumes')))
            self.sbSlicesNr.setValue(int(self.settings.value('NrOfSlices')))
            self.sbTR.setValue(int(self.settings.value('TR')))
            self.sbSkipVol.setValue(int(self.settings.value('nrSkipVol')))
            self.sbMatrixSizeX.setValue(int(self.settings.value('MatrixSizeX')))
            self.sbMatrixSizeY.setValue(int(self.settings.value('MatrixSizeY')))

            # --- bottom left ---
            self.cbOfflineMode.setChecked(str(self.settings.value('OfflineMode', 'true')).lower() == 'true')

            if self.settings.value('UseTCPData', None) is None:
                logger.warning('Upgrade settings format from version 1.0.rc0')

            self.cbUseTCPData.setChecked(str(self.settings.value('UseTCPData', 'false')).lower() == 'true')
            if self.cbUseTCPData.isChecked():
                self.leTCPDataIP.setText(self.settings.value('TCPDataIP', ''))
                self.leTCPDataPort.setText(str(self.settings.value('TCPDataPort', '')))

            self.leMaxFeedbackVal.setText(str(self.settings.value('MaxFeedbackVal', '100')))  # FixMe
            self.leMinFeedbackVal.setText(str(self.settings.value('MinFeedbackVal', '-100')))
            self.sbFeedbackValDec.setValue(int(self.settings.value('FeedbackValDec', '0')))  # FixMe
            self.cbNegFeedback.setChecked(str(self.settings.value('NegFeedback', 'false')).lower() == 'true')
            self.cbFeedbackPlot.setChecked(str(self.settings.value('PlotFeedback', 'true')).lower() == 'true')

            self.leShamFile.setText(self.settings.value('ShamFile', ''))

            self.cbUsePTB.setChecked(str(self.settings.value('UsePTB', 'false')).lower() == 'true')
            if not config.USE_PTB_HELPER:
                self.cbUsePTB.setChecked(False)
                self.cbUsePTB.setEnabled(False)

            self.cbScreenId.setCurrentIndex(int(self.settings.value('DisplayFeedbackScreenID', 0)))
            self.cbDisplayFeedbackFullscreen.setChecked(
                str(self.settings.value('DisplayFeedbackFullscreen')).lower() == 'true')

            self.cbUseUDPFeedback.setChecked(str(self.settings.value('UseUDPFeedback')).lower() == 'true')
            self.leUDPFeedbackIP.setText(self.settings.value('UDPFeedbackIP', ''))
            self.leUDPFeedbackPort.setText(str(self.settings.value('UDPFeedbackPort', '1234')))
            self.leUDPFeedbackControlChar.setText(str(self.settings.value('UDPFeedbackControlChar', '')))
            self.cbUDPSendCondition.setChecked(str(self.settings.value('UDPSendCondition')).lower() == 'true')

            # --- bottom right ---
            idx = self.cbDataType.findText(self.settings.value('DataType', 'DICOM'))
            if idx >= 0:
                self.cbDataType.setCurrentIndex(idx)
            self.cbgetMAT.setChecked(str(self.settings.value('GetMAT')).lower() == 'true')
            idx = self.cbProt.findText(self.settings.value('Prot', 'Inter'))
            if idx >= 0:
                self.cbProt.setCurrentIndex(idx)
            idx = self.cbType.findText(self.settings.value('Type', 'PSC'))
            if idx >= 0:
                self.cbType.setCurrentIndex(idx)

            # --- main viewer ---
            self.sbTargANG.setValue(float(self.settings.value('TargANG', 0)))
            self.sbTargRAD.setValue(float(self.settings.value('TargRAD', 0)))
            self.sbTargDIAM.setValue(float(self.settings.value('TargDIAM', 0.0)))
            self.leWeightsFile.setText(str(self.settings.value('WeightsFileName', '')))

            self.actualize
        else:
            self.leWatchFolder3.setText(self.settings.value('WatchFolder', ''))
            if config.SELECT_ROIS:
                self.leRoiFolder.setText(self.settings.value('RoiFolder', ''))
            if config.USE_EPI_TEMPLATE:
                self.leMCTempl3.setText(self.settings.value('MCTempl', ''))
            self.leRoiAnatOperation.setText(self.settings.value('RoiAnatOperation', 'mean(norm_percValues)'))

            self.leProjName.setText(self.settings.value('ProjectName', ''))
            self.leSubjectID.setText(self.settings.value('SubjectID', ''))
            self.leFirstFile3.setText(self.settings.value('FirstFileNameTxt', '001_{Image Series No:06}_{#:06}.dcm'))
            self.sbNFRunNr3.setValue(int(self.settings.value('NFRunNr', '1')))
            self.sbImgSerNr3.setValue(int(self.settings.value('ImgSerNr', '1')))
            self.sbVolumesNr3.setValue(int(self.settings.value('NrOfVolumes')))
            self.sbSkipVol3.setValue(int(self.settings.value('nrSkipVol')))
            self.sbSlicesNr3.setValue(int(self.settings.value('NrOfSlices')))
            self.sbMatrixSizeX3.setValue(int(self.settings.value('MatrixSizeX')))
            self.sbMatrixSizeY3.setValue(int(self.settings.value('MatrixSizeY')))

            self.cbOfflineMode3.setChecked(str(self.settings.value('OfflineMode', 'true')).lower() == 'true')

            self.actualizeAutoRTQA()

    # --------------------------------------------------------------------------
    def loadJsonProtocol(self):
        self.eng.loadJsonProtocol(nargout=0)

    # --------------------------------------------------------------------------
    def selectRoi(self):

        if self.P['Type'] in ['PSC', 'SVM', 'Corr', 'None']:
            if not Path(self.P['RoiFilesFolder']).is_dir():
                logger.error("Couldn't find: " + self.P['RoiFilesFolder'])
                return

            self.eng.selectROI(self.P['RoiFilesFolder'], nargout=0)

            if self.P['Type'] == 'Corr':
                if int(self.eng.evalin('base', 'P.NrROIs')) < 2:
                    logger.error("More than 1 ROI is required for Correlations")
                    return
                if int(self.eng.evalin('base', 'P.NrROIs')) > 2:
                    logger.error("Correlations between more than 2 ROI is not yet implemented")
                    return

        elif self.P['Type'] == 'DCM':
            p = [self.P['RoiAnatFolder'], self.P['RoiGroupFolder']]
            self.eng.selectROI(p, nargout=0)

    # --------------------------------------------------------------------------
    def actualizeAutoRTQA(self):
        logger.info("  Actualizing:")

        # --- top ---
        self.P['WatchFolder'] = self.leWatchFolder3.text()
        self.P['WorkFolder'] = str(Path(self.P['WatchFolder']).absolute().resolve().parent)
        if config.USE_EPI_TEMPLATE:
            self.P['MCTempl'] = self.leMCTempl3.text()
        else:
            self.P['MCTempl'] = []
        self.P['StructBgFile'] = ''

        self.P['Type'] = "None"
        if config.SELECT_ROIS:
            self.P['RoiFilesFolder'] = self.leRoiFolder.text()
        else:
            self.P['RoiFilesFolder'] = []
        self.P['RoiAnatOperation'] = "median(norm_percValues)"

        self.P['ProjectName'] = "Auto_RTQA"
        self.P['SubjectID'] = "foo"
        self.P['Prot'] = "Auto_RTQA"
        self.P['FirstFileNameTxt'] = self.leFirstFile3.text()
        self.P['ImgSerNr'] = self.sbImgSerNr3.value()
        self.P['NFRunNr'] = self.sbNFRunNr3.value()
        self.P['NrOfSlices'] = self.sbSlicesNr3.value()
        self.P['MatrixSizeX'] = self.sbMatrixSizeX3.value()
        self.P['MatrixSizeY'] = self.sbMatrixSizeY3.value()
        self.P['NrOfVolumes'] = self.sbVolumesNr3.value()
        self.P['nrSkipVol'] = self.sbSkipVol3.value()

        # Parsing FirstFileNameTxt template and replace it with variables ---
        fields = {
            'projectname': self.P['ProjectName'],
            'subjectid': self.P['SubjectID'],
            'imageseriesno': self.P['ImgSerNr'],
            'nfrunno': self.P['NFRunNr'],
            '#': 1
        }
        template = self.P['FirstFileNameTxt']
        template_elements = re.findall(r"\{([A-Za-z0-9_: ]+)\}", template)

        self.P['FirstFileName'] = self.P['FirstFileNameTxt']

        for template_element in template_elements:
            template = template.replace("{%s}" % template_element, "{%s}" % template_element.replace(" ", "").lower())

        self.P['FirstFileName'] = template.format(**fields)

        self.P['DataType'] = "DICOM"
        self.P['useEPITemplate'] = config.USE_EPI_TEMPLATE
        self.P['isAutoRTQA'] = config.AUTO_RTQA
        self.P['isRTQA'] = config.USE_RTQA
        self.P['isIGLM'] = config.USE_IGLM
        self.P['isDicomSiemensXA30'] = config.DICOM_SIEMENS_XA30
        self.P['isZeroPadding'] = config.zeroPaddingFlag
        self.P['nrZeroPadVol'] = config.nrZeroPadVol
        self.P['UseTCPData'] = False
        self.P['TR'] = 1500
        config.USE_UDP_FEEDBACK = False
        self.P['getMAT'] = False

        # Update settings file
        self.settings.setValue('WorkFolder', self.P['WorkFolder'])
        self.settings.setValue('WatchFolder', self.P['WatchFolder'])
        self.settings.setValue('MCTempl', self.P['MCTempl'])
        self.settings.setValue('RoiFolder', self.P['RoiFilesFolder'])
        self.settings.setValue('RoiAnatOperation', self.P['RoiAnatOperation'])
        self.P['PlotFeedback'] = False

        self.settings.setValue('ImgSerNr', self.P['ImgSerNr'])
        self.settings.setValue('NFRunNr', self.P['NFRunNr'])

        self.settings.setValue('FirstFileNameTxt', self.P['FirstFileNameTxt'])
        self.settings.setValue('FirstFileName', self.P['FirstFileName'])

        self.settings.setValue('NrOfVolumes', self.P['NrOfVolumes'])
        self.settings.setValue('nrSkipVol', self.P['nrSkipVol'])
        self.settings.setValue('NrOfSlices', self.P['NrOfSlices'])
        self.settings.setValue('MatrixSizeX', self.P['MatrixSizeX'])
        self.settings.setValue('MatrixSizeY', self.P['MatrixSizeY'])
        self.settings.setValue('OfflineMode', self.cbOfflineMode.isChecked())

    # --------------------------------------------------------------------------
    def actualize(self):
        logger.info("  Actualizing:")

        # --- top ---
        self.P['ProtocolFile'] = self.leProtocolFile.text()
        self.P['WorkFolder'] = self.leWorkFolder.text()
        self.P['WatchFolder'] = self.leWatchFolder.text()

        self.P['Type'] = self.cbType.currentText()
        if self.P['Type'] == 'DCM':
            self.P['RoiAnatFolder'] = self.leRoiAnatFolder.text()
        else:
            self.P['RoiFilesFolder'] = self.leRoiAnatFolder.text()
        self.P['RoiAnatOperation'] = self.leRoiAnatOperation.text()
        self.P['RoiGroupFolder'] = self.leRoiGroupFolder.text()
        self.P['StructBgFile'] = self.leStructBgFile.text()
        self.P['MCTempl'] = self.leMCTempl.text()

        # --- middle ---
        self.P['ProjectName'] = self.leProjName.text()
        self.P['SubjectID'] = self.leSubjectID.text()
        self.P['FirstFileNameTxt'] = self.leFirstFile.text()
        self.P['ImgSerNr'] = self.sbImgSerNr.value()
        self.P['NFRunNr'] = self.sbNFRunNr.value()

        self.P['NrOfVolumes'] = self.sbVolumesNr.value()
        self.P['NrOfSlices'] = self.sbSlicesNr.value()
        self.P['TR'] = self.sbTR.value()
        self.P['nrSkipVol'] = self.sbSkipVol.value()
        self.P['MatrixSizeX'] = self.sbMatrixSizeX.value()
        self.P['MatrixSizeY'] = self.sbMatrixSizeY.value()

        # --- bottom left ---
        self.P['UseTCPData'] = self.cbUseTCPData.isChecked()
        if self.P['UseTCPData']:
            self.P['TCPDataIP'] = self.leTCPDataIP.text()
            self.P['TCPDataPort'] = int(self.leTCPDataPort.text())
        self.P['DisplayFeedbackFullscreen'] = self.cbDisplayFeedbackFullscreen.isChecked()

        # --- bottom right ---
        self.P['DataType'] = str(self.cbDataType.currentText())
        self.P['getMAT'] = self.cbgetMAT.isChecked()
        self.P['Prot'] = str(self.cbProt.currentText())
        self.P['Type'] = str(self.cbType.currentText())
        self.P['isAutoRTQA'] = config.AUTO_RTQA
        self.P['isRTQA'] = config.USE_RTQA
        self.P['isIGLM'] = config.USE_IGLM
        self.P['isDicomSiemensXA30'] = config.DICOM_SIEMENS_XA30
        self.P['useEPITemplate'] = config.USE_EPI_TEMPLATE
        self.P['isZeroPadding'] = config.zeroPaddingFlag
        self.P['nrZeroPadVol'] = config.nrZeroPadVol

        if self.P['Prot'] == 'ContTask':
            self.P['TaskFolder'] = self.leTaskFolder.text()

        self.P['MaxFeedbackVal'] = float(self.leMaxFeedbackVal.text())
        self.P['MinFeedbackVal'] = float(self.leMinFeedbackVal.text())
        self.P['FeedbackValDec'] = self.sbFeedbackValDec.value()
        self.P['NegFeedback'] = self.cbNegFeedback.isChecked()
        self.P['PlotFeedback'] = self.cbFeedbackPlot.isChecked()

        self.P['ShamFile'] = self.leShamFile.text()

        # --- main viewer ---
        self.P['TargANG'] = self.sbTargANG.value()
        self.P['TargRAD'] = self.sbTargRAD.value()
        self.P['TargDIAM'] = self.sbTargDIAM.value()
        self.P['WeightsFileName'] = self.leWeightsFile.text()

        # Parsing FirstFileNameTxt template and replace it with variables ---
        fields = {
            'projectname': self.P['ProjectName'],
            'subjectid': self.P['SubjectID'],
            'imageseriesno': self.P['ImgSerNr'],
            'nfrunno': self.P['NFRunNr'],
            '#': 1
        }
        template = self.P['FirstFileNameTxt']
        template_elements = re.findall(r"\{([A-Za-z0-9_: ]+)\}", template)

        self.P['FirstFileName'] = self.P['FirstFileNameTxt']

        for template_element in template_elements:
            template = template.replace("{%s}" % template_element, "{%s}" % template_element.replace(" ", "").lower())

        self.P['FirstFileName'] = template.format(**fields)

        # Update GUI information
        self.leCurrentVolume.setText('%d' % self.iteration)
        self.leFirstFilePath.setText(str(Path(self.P['WatchFolder'], self.P['FirstFileName'])))

        filePathStatus = ""
        if Path(self.P['WatchFolder']).is_dir():
            filePathStatus += "MRI Watch Folder exists. "
        else:
            filePathStatus += "MRI Watch Folder does not exists. "
        if Path(self.leFirstFilePath.text()).is_file():
            filePathStatus += "First file exists. "
        else:
            filePathStatus += "First file does not exist. "

        # if Path(self.P['WatchFolder'],self.P['FirstFileName']).is_dir()
        self.lbFilePathStatus.setText(filePathStatus)

        # Update settings file
        # --- top ---
        self.settings.setValue('StimulationProtocol', self.P['ProtocolFile'])
        self.settings.setValue('WorkFolder', self.P['WorkFolder'])
        self.settings.setValue('WatchFolder', self.P['WatchFolder'])
        if self.P['Type'] == 'DCM':
            self.settings.setValue('RoiAnatFolder', self.P['RoiAnatFolder'])
        else:
            self.settings.setValue('RoiFilesFolder', self.P['RoiFilesFolder'])
        self.settings.setValue('RoiAnatOperation', self.P['RoiAnatOperation'])
        self.settings.setValue('RoiGroupFolder', self.P['RoiGroupFolder'])
        self.settings.setValue('StructBgFile', self.P['StructBgFile'])
        self.settings.setValue('MCTempl', self.P['MCTempl'])

        if self.P['Prot'] == 'ContTask':
            self.settings.setValue('TaskFolder', self.P['TaskFolder'])

        # --- middle ---
        self.settings.setValue('ProjectName', self.P['ProjectName'])
        self.settings.setValue('SubjectID', self.P['SubjectID'])
        self.settings.setValue('ImgSerNr', self.P['ImgSerNr'])
        self.settings.setValue('NFRunNr', self.P['NFRunNr'])

        self.settings.setValue('FirstFileNameTxt', self.P['FirstFileNameTxt'])
        self.settings.setValue('FirstFileName', self.P['FirstFileName'])

        self.settings.setValue('NrOfVolumes', self.P['NrOfVolumes'])
        self.settings.setValue('NrOfSlices', self.P['NrOfSlices'])
        self.settings.setValue('TR', self.P['TR'])
        self.settings.setValue('nrSkipVol', self.P['nrSkipVol'])
        self.settings.setValue('MatrixSizeX', self.P['MatrixSizeX'])
        self.settings.setValue('MatrixSizeY', self.P['MatrixSizeY'])

        # --- bottom left ---
        self.settings.setValue('OfflineMode', self.cbOfflineMode.isChecked())
        self.settings.setValue('UseTCPData', self.cbUseTCPData.isChecked())
        if self.cbUseTCPData.isChecked():
            self.settings.setValue('TCPDataIP', self.leTCPDataIP.text())
            self.settings.setValue('TCPDataPort', int(self.leTCPDataPort.text()))

        self.settings.setValue('MaxFeedbackVal', self.P['MaxFeedbackVal'])
        self.settings.setValue('MinFeedbackVal', self.P['MinFeedbackVal'])
        self.settings.setValue('FeedbackValDec', self.P['FeedbackValDec'])
        self.settings.setValue('NegFeedback', self.P['NegFeedback'])
        self.settings.setValue('PlotFeedback', self.P['PlotFeedback'])

        self.settings.setValue('ShamFile', self.P['ShamFile'])

        self.settings.setValue('UsePTB', self.cbUsePTB.isChecked())
        self.settings.setValue('DisplayFeedbackScreenID', self.cbScreenId.currentIndex())
        self.settings.setValue('DisplayFeedbackFullscreen', self.cbDisplayFeedbackFullscreen.isChecked())
        self.settings.setValue('TargANG', self.P['TargANG'])
        self.settings.setValue('TargRAD', self.P['TargRAD'])
        self.settings.setValue('TargDIAM', self.P['TargDIAM'])

        self.settings.setValue('UseUDPFeedback', self.cbUseUDPFeedback.isChecked())
        self.settings.setValue('UDPFeedbackIP', self.leUDPFeedbackIP.text())
        self.settings.setValue('UDPFeedbackPort', int(self.leUDPFeedbackPort.text()))
        self.settings.setValue('UDPFeedbackControlChar', self.leUDPFeedbackControlChar.text())
        self.settings.setValue('UDPSendCondition', self.cbUDPSendCondition.isChecked())

        # --- bottom right ---
        self.settings.setValue('DataType', self.P['DataType'])
        self.settings.setValue('GetMAT', self.P['getMAT'])
        self.settings.setValue('Prot', self.P['Prot'])
        self.settings.setValue('Type', self.P['Type'])

        self.settings.setValue('WeightsFileName', self.P['WeightsFileName'])

        # Update config
        config.USE_TCP_DATA = self.cbUseTCPData.isChecked()
        if config.USE_TCP_DATA:
            # TCP receiver settings
            config.TCP_DATA_IP = self.leTCPDataIP.text()
            config.TCP_DATA_PORT = int(self.leTCPDataPort.text())

        config.USE_SHAM = bool(len(self.P['ShamFile']))

        config.USE_PTB = self.cbUsePTB.isChecked()

        config.USE_UDP_FEEDBACK = self.cbUseUDPFeedback.isChecked()
        if config.USE_UDP_FEEDBACK:
            # UDP sender settings
            config.UDP_FEEDBACK_IP = self.leUDPFeedbackIP.text()
            config.UDP_FEEDBACK_PORT = int(self.leUDPFeedbackPort.text())
            config.UDP_FEEDBACK_CONTROLCHAR = self.leUDPFeedbackControlChar.text()
            config.UDP_SEND_CONDITION = self.cbUDPSendCondition.isChecked()
        else:
            config.UDP_SEND_CONDITION = False

    # --------------------------------------------------------------------------
    def createMusterInfo(self):
        # TODO: More general way to use any protocol
        tmpCond = list()
        nrCond = list()
        for c in self.P['Protocol']['ConditionIndex']:
            tmpCond.append(np.array(c['OnOffsets']).astype(np.int32))
            nrCond.append(tmpCond[-1].shape[0])

        if not ('BAS' in self.P['CondIndexNames']):  # implicit baseline
            # self.P['ProtCond'][0] - 0 is for Baseline indexes
            tmpCond.insert(0, np.array([np.array(t).astype(np.int32)[0, [0, -1]] for t in self.P['ProtCond'][0]]))
            nrCond.insert(0, tmpCond[0].shape[0])

        c = 1
        for c in range(len(tmpCond), 4):  # placeholders
            tmpCond.append(np.array([(0, 0), (0, 0)]))
            nrCond.append(tmpCond[-1].shape[0])

        if self.P['Prot'] == 'InterBlock':
            blockLength = tmpCond[0][0][1] - tmpCond[0][0][0] + c
        else:
            blockLength = 0
            for condNumber in range(len(tmpCond)):
                blockLength += tmpCond[condNumber][0][1] - tmpCond[condNumber][0][0]
            blockLength += c

        # ----------------------------------------------------------------------
        def removeIntervals(data, remData):
            dfs = []

            for n1, n2 in zip(data[:-1], data[1:]):
                df = n2[0] - n1[1] - blockLength - 1
                dfs.append(df)

            dfs = np.cumsum(dfs)

            idx = []
            last = 0

            for i, n in enumerate(dfs):
                if n > last:
                    idx.append(i + 1)
                    last = n

            for i, r in zip(idx, remData[:-1]):
                sz = (r[1] - r[0] + 1)
                data[i:, 0] -= sz
                data[i:, 1] -= sz

        if self.P['Prot'] == 'InterBlock':
            remCond = []

            for a, b in zip(tmpCond[2], tmpCond[3]):
                remCond.append((a[0], b[1]))

            removeIntervals(tmpCond[0], remCond)
            removeIntervals(tmpCond[1], remCond)

        # To break drawMusterPlot() at given length of conditions,
        # i.e., to avoid plotting some of them as for DCM feedback type
        condTotal = 2 if self.P['Prot'] == 'InterBlock' else len(tmpCond)

        tmpCondStr = ['tmpCond{:d}'.format(x + 1) for x in range(condTotal)]
        nrCondStr = ['nrCond{:d}'.format(x + 1) for x in range(condTotal)]
        self.musterInfo = dict.fromkeys(tmpCondStr + nrCondStr)
        self.musterInfo['condTotal'] = condTotal
        for condNumber in range(condTotal):
            self.musterInfo[tmpCondStr[condNumber]] = tmpCond[condNumber]
            self.musterInfo[nrCondStr[condNumber]] = nrCond[condNumber]
        self.musterInfo['blockLength'] = blockLength

    # --------------------------------------------------------------------------
    def computeMusterPlotData(self, ylim):
        singleY = np.array([ylim[0], ylim[1], ylim[1], ylim[0]])

        def computeConds(nrCond, tmpCond):
            xCond = np.zeros(nrCond * 4, dtype=np.float64)
            yCond = np.zeros(nrCond * 4, dtype=np.float64)

            for k in range(nrCond):
                i = slice(k * 4, (k + 1) * 4)

                xCond[i] = np.array([
                    tmpCond[k][0] - 1,
                    tmpCond[k][0] - 1,
                    tmpCond[k][1],
                    tmpCond[k][1],
                ])

                yCond[i] = singleY

            return xCond, yCond

        for cond in range(self.musterInfo['condTotal']):
            xCond, yCond = computeConds(self.musterInfo['nrCond' + str(cond + 1)],
                                        self.musterInfo['tmpCond' + str(cond + 1)])
            self.musterInfo['xCond' + str(cond + 1)] = xCond
            self.musterInfo['yCond' + str(cond + 1)] = yCond

    # --------------------------------------------------------------------------
    def drawRoiPlots(self, init):
        if not self.outputSamples:
            return

        if self.P['Prot'] != 'InterBlock':
            key = 'displRawTimeSeries'
        else:
            key = 'rawTimeSeries'

        dataRaw = np.array(self.outputSamples[key], ndmin=2)[self.selectedRoi, :]
        dataProc = np.array(self.outputSamples['kalmanProcTimeSeries'], ndmin=2)[self.selectedRoi, :]
        dataNorm = np.array(self.outputSamples['scalProcTimeSeries'], ndmin=2)[self.selectedRoi, :]
        if self.P['PlotFeedback']:
            dataNorm = np.concatenate(
                (dataNorm, np.array([self.displaySamples]) / self.P['MaxFeedbackVal'])
            )

        self.drawGivenRoiPlot(init, self.rawRoiPlot, dataRaw)
        self.drawGivenRoiPlot(init, self.procRoiPlot, dataProc)
        self.drawGivenRoiPlot(init, self.normRoiPlot, dataNorm)

    # --------------------------------------------------------------------------
    def drawGivenRoiPlot(self, init, plotwidget: pg.PlotWidget, data):
        plotitem = plotwidget.getPlotItem()

        sz, l = data.shape

        if init:

            plotitem.enableAutoRange(enable=True, x=False, y=True)

            plotitem.clear()
            muster = self.drawMusterPlot(plotitem)

            plots = []

            plot_colors = np.array(config.ROI_PLOT_COLORS)[self.selectedRoi]
            if self.P['PlotFeedback']:
                plot_colors = np.append(plot_colors, config.ROI_PLOT_COLORS[int(self.P['NrROIs'])])
            for i, c in zip(range(sz), plot_colors):
                pen = pg.mkPen(color=c, width=config.ROI_PLOT_WIDTH)
                p = plotitem.plot(pen=pen)
                plots.append(p)

            self.drawGivenRoiPlot.__dict__[plotitem] = plots, muster

        x = np.arange(1, l + 1, dtype=np.float64)

        for p, y in zip(self.drawGivenRoiPlot.__dict__[plotitem][0], data):
            p.setData(x=x, y=np.array(y))

        if self.P['Prot'] != 'InterBlock':
            if plotwidget == self.procRoiPlot:
                posMin = np.array(self.outputSamples['posMin'], ndmin=2)
                posMax = np.array(self.outputSamples['posMax'], ndmin=2)
                inds = list(self.selectedRoi)
                inds.append(len(posMin) - 1)
                posMin = posMin[inds]
                posMax = posMax[inds]

                self.drawMinMaxProcRoiPlot(
                    init, data,
                    posMin, posMax)

        items = plotitem.listDataItems()

        for m in self.drawGivenRoiPlot.__dict__[plotitem][1]:
            items.remove(m)

        plotitem.autoRange(items=items)
        if self.P['isAutoRTQA']:
            grid = True
        else:
            grid = False
        self.basicSetupPlot(plotitem, grid)

    # --------------------------------------------------------------------------
    def drawMusterPlot(self, plotitem: pg.PlotItem):
        ylim = config.MUSTER_Y_LIMITS

        if not self.P['isAutoRTQA']:
            self.computeMusterPlotData(ylim)
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
                plotitem.plot(x=[1, (self.P['NrOfVolumes'] - self.P['nrSkipVol'])],
                              y=[-1000, 1000],
                              fillLevel=ylim[0],
                              pen=config.MUSTER_PEN_COLORS[9],
                              brush=config.MUSTER_BRUSH_COLORS[9])
            ]

        return muster

    # --------------------------------------------------------------------------
    def drawMinMaxProcRoiPlot(self, init, data, posMin, posMax):
        plotitem = self.procRoiPlot.getPlotItem()
        sz = data.shape[0] + 1
        l = data.shape[1]

        if init:
            plotsMin = []
            plotsMax = []

            plot_colors = np.array(config.ROI_PLOT_COLORS)
            plot_colors = np.append(plot_colors[self.selectedRoi], plot_colors[-1])
            for i, c in zip(range(sz), plot_colors):
                plotsMin.append(plotitem.plot(pen=pg.mkPen(
                    color=c, width=config.ROI_PLOT_WIDTH)))
                plotsMax.append(plotitem.plot(pen=pg.mkPen(
                    color=c, width=config.ROI_PLOT_WIDTH)))

            self.drawMinMaxProcRoiPlot.__dict__['posMin'] = plotsMin
            self.drawMinMaxProcRoiPlot.__dict__['posMax'] = plotsMax

        x = np.arange(1, l + 1, dtype=np.float64)

        for pmi, mi, pma, ma in zip(
                self.drawMinMaxProcRoiPlot.__dict__['posMin'], posMin,
                self.drawMinMaxProcRoiPlot.__dict__['posMax'], posMax):
            mi = np.array(mi, ndmin=1)
            ma = np.array(ma, ndmin=1)
            pmi.setData(x=x, y=mi)
            pma.setData(x=x, y=ma)

    # --------------------------------------------------------------------------
    def drawMcPlots(self, init):
        if not self.outputSamples:
            return

        data = np.array(self.outputSamples['motCorrParam'])

        mctrrot = self.mcPlot.getPlotItem()

        if init:
            mctrrot.clear()

            plots = []

            for i, c in enumerate(config.MC_PLOT_COLORS):
                plots.append(mctrrot.plot(pen=c))

            self.drawMcPlots.__dict__['mctrrot'] = plots

        x = np.arange(1, data.shape[0] + 1, dtype=np.float64)

        for pt, i1, in zip(
                self.drawMcPlots.__dict__['mctrrot'], range(0, 6)):
            pt.setData(x=x, y=data[:, i1])

    # --------------------------------------------------------------------------
    def printToLog(self, message):
        # TODO: Use logging module
        print(message)

    # --------------------------------------------------------------------------
    def readAppSettings(self):
        self.appSettings.beginGroup('UI')

        self.restoreGeometry(self.appSettings.value(
            'WindowGeometry', self.saveGeometry()))
        self.splitterMainVer.restoreState(self.appSettings.value(
            'SplitterMainVerState', self.splitterMainVer.saveState()))
        self.splitterMainHor.restoreState(self.appSettings.value(
            'SplitterMainHorState', self.splitterMainHor.saveState()))

        self.appSettings.endGroup()

        self.appSettings.beginGroup('Params')

        if not config.AUTO_RTQA:
            self.settingFileName = self.appSettings.value(
                'SettingFileName', self.settingFileName)
            if self.settingFileName == str(config.AUTO_RTQA_SETTINGS):
                self.settingFileName = ''
        else:
            self.settingFileName = str(config.AUTO_RTQA_SETTINGS)

        self.appSettings.endGroup()

        self.chooseSetFile(self.settingFileName)

    # --------------------------------------------------------------------------
    def writeAppSettings(self):
        self.appSettings.beginGroup('UI')
        self.appSettings.setValue('WindowGeometry', self.saveGeometry())
        self.appSettings.setValue('SplitterMainVerState', self.splitterMainVer.saveState())
        self.appSettings.setValue('SplitterMainHorState', self.splitterMainHor.saveState())
        self.appSettings.endGroup()

        self.appSettings.beginGroup('Params')
        self.appSettings.setValue('SettingFileName', self.settingFileName)

        self.appSettings.endGroup()

    # --------------------------------------------------------------------------
    def onTest(self):
        """
        This is for DEBUG USAGE ONLY

        """
        # matlabSatusEvent
        # matlabStatusTimer

        mgr = multiprocessing.Manager()
        # ns = mgr.Namespace()
        # ns.ptb = self.ptbScreen
        self.displayData = {'feedbackType': 'DCM', 'condition': 2.0, 'dispValue': 0.0, 'Reward': ''}
        # self.ptbScreen.display(displayData)

        self.e1 = multiprocessing.Event()
        self.e2 = multiprocessing.Event()

        self.t1 = threading.Thread(target=self.onEventDisplay)  # , args=(evnt,)
        self.t1.start()

        # self.e1.set()
        # self.e2.wait()
        # self.t1.join()  # ns.ptb.display(displayData)

        # return
        if not hasattr(self, 'tvData'):
            (self.pulseProc, self.tvData) = mrpulse.start(1, 12, self.e1)
            self.testStarted = True
        else:
            np_arr = mrpulse.toNpData(self.tvData)
            logger.info('{}', np_arr)

            self.e1.set()
            self.e2.wait()
            self.t1.join()  # ns.ptb.display(displayData)

        return

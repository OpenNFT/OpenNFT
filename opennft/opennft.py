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

The module bellow is written by Artem Nikonorov, Evgeny Prilepin, Yury Koush, Ronald Sladky

"""

import os
import time
import glob
import queue
import enum
import re
import fnmatch
import threading
import multiprocessing

from loguru import logger

import numpy as np
import pyqtgraph as pg

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pyniexp.connection import Udp
from scipy.io import loadmat

from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtCore import QSettings, QTimer, QEvent, QRegExp
from PyQt5.uic import loadUi
from PyQt5.QtGui import QRegExpValidator

from opennft import (
    config,
    runmatlab,
    ptbscreen,
    mmapimage,
    mosaicview,
    projview,
    mapimagewidget,
    plugin,
    utils,
    rtqa,
    eventrecorder as erd,
)

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
        if not event.is_directory and fnmatch.fnmatch(os.path.basename(event.src_path), self.filepat):
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

        self.udpCondForContrast = self.P['CondForContrast']
        if not ('BAS' in self.P['CondIndexNames']): self.udpCondForContrast.insert(0, 'BAS')

    # --------------------------------------------------------------------------
    def finalizeUdpSender(self):
        if not config.USE_UDP_FEEDBACK:
            return
        self.udpSender.close()

    # --------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        loadUi(utils.get_ui_file('opennft.ui'), self)

        self.setWindowIcon(QIcon(config.OpenNFT_ICON))
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

        self.mosaic_background_image_reader = mmapimage.MosaicImageReader(image_name='imgViewTempl')
        self.mosaic_pos_map_image_reader = mmapimage.MosaicImageReader(image_name='statMap')
        self.mosaic_neg_map_image_reader = mmapimage.MosaicImageReader(image_name='statMap_neg')

        self.proj_background_images_reader = mmapimage.ProjectionImagesReader()
        self.proj_pos_map_images_reader = mmapimage.ProjectionImagesReader()
        self.proj_neg_map_images_reader = mmapimage.ProjectionImagesReader()

        self.pos_map_thresholds_widget = mapimagewidget.MapImageThresholdsWidget(self)
        self.neg_map_thresholds_widget = mapimagewidget.MapImageThresholdsWidget(self, colormap='Blues_r')

        self.layoutHotMapThresholds.addWidget(self.pos_map_thresholds_widget)
        self.layoutNegMapThresholds.addWidget(self.neg_map_thresholds_widget)

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

        self.mrPulses = None
        self.recorder = erd.EventRecorder()
        self.call_timer = QTimer(self)
        self.files_queue = queue.Queue()
        self.fs_observer = Observer()
        self.isOffline = None
        self.files_processed = []
        self.files_exported = []

        self.eng = None
        self.engSPM = None

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
        self.mlSpmHelper = matlab_helpers[config.SPM_MATLAB_NAME]
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

        self.settings = QSettings('', QSettings.IniFormat)
        self.reachedFirstFile = False

        self.initializeUi()
        self.readAppSettings()
        self.initialize(start=False)

        self.windowRTQA = None
        self.isStopped = False

    # --------------------------------------------------------------------------
    def closeEvent(self, e):

        self.writeAppSettings()
        self.stop()
        self.hide()

        self.mosaic_background_image_reader.clear()
        self.mosaic_pos_map_image_reader.clear()
        self.mosaic_neg_map_image_reader.clear()

        self.proj_background_images_reader.clear()
        self.proj_pos_map_images_reader.clear()
        self.proj_neg_map_images_reader.clear()

        self.eng = None
        self.engSPM = None

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

        self.leFirstFile.textChanged.connect(lambda: self.textChangedDual(self.leFirstFile, self.leFirstFile2))
        self.leFirstFile2.textChanged.connect(lambda: self.textChangedDual(self.leFirstFile2, self.leFirstFile))

        self.pbMoreParameters.toggled.connect(self.onShowMoreParameters)

        self.btnInit.clicked.connect(lambda: self.initialize(start=True))
        self.btnPlugins.clicked.connect(self.showPluginDlg)
        self.btnPlugins.setEnabled(False)
        self.btnSetup.clicked.connect(self.setup)
        self.btnStart.clicked.connect(self.start)
        self.btnStop.clicked.connect(self.stop)
        self.btnRTQA.clicked.connect(self.rtQA)
        self.btnRTQA.setEnabled(False)

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
        # self.btnTest.clicked.connect(self.onTest)

        self.btnChooseWorkFolder.clicked.connect(
            lambda: self.onChooseFolder('WorkFolder', self.leWorkFolder))
        self.btnChooseWatchFolder.clicked.connect(
            lambda: self.onChooseFolder('WatchFolder', self.leWatchFolder))

        self.btnStart.setEnabled(False)

        # if config.HIDE_TEST_BTN:
        #    self.btnTest.setVisible(False)

        self.cbImageViewMode.currentIndexChanged.connect(self.onChangeImageViewMode)
        self.orthView.cursorPositionChanged.connect(self.onChangeOrthViewCursorPosition)

        self.call_timer.timeout.connect(self.callMainLoopIteration)
        self.orthViewUpdateCheckTimer.timeout.connect(self.onCheckOrthViewUpdated)

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
            is_rtqa_volume = self.windowRTQA.volumeCheckBox.isChecked()
        else:
            is_rtqa_volume = False
        self.negMapCheckBox.setEnabled(not is_rtqa_volume)

        if is_rtqa_volume:
            setattr(self, '__neg_map_state', self.negMapCheckBox.isChecked())
            self.negMapCheckBox.setChecked(False)
        else:
            neg_map_state = getattr(self, '__neg_map_state', self.negMapCheckBox.isChecked())
            self.negMapCheckBox.setChecked(neg_map_state)

    # --------------------------------------------------------------------------
    def showPluginDlg(self):
        self.btnStart.setEnabled(False)  # force rerunning Setup

        if self.pluginWindow.exec_():
            self.plugins = []
            for p in range(len(self.pluginWindow.plugins)):
                if self.pluginWindow.lvPlugins.model().item(p).checkState():
                    self.plugins += [plugin.Plugin(self, self.pluginWindow.plugins[p])]

    # --------------------------------------------------------------------------
    def updatePlugins(self):
        for i in range(len(self.plugins)): self.plugins[i].update()

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
        path = os.path.normpath(self.P['WorkFolder'])
        fname = os.path.join(path, 'OrthView.dat')
        if not os.path.exists(fname):
            return fname

        try:
            f = open(fname, 'w+')
            f.close()
            return fname
        except IOError as e:
            fname = os.path.join(path, 'OrthView1.dat')

        if not os.path.exists(fname):
            return fname

        try:
            f = open(fname, 'w+')
            f.close()
            return fname
        except IOError as e:
            logger.info('POSSIBLE PROBLEMS WITH MEMMAP ACCESS!')
            return fname

    # --------------------------------------------------------------------------
    def initMainLoopData(self):
        # Data types
        self.mainLoopData['DataType'] = self.cbDataType.currentText()

        self.eng.workspace['mainLoopData'] = self.mainLoopData

        self.eng.workspace['rtQA_matlab'] = self.rtQA_matlab

        self.eng.setupProcParams(nargout=0)

        with utils.timeit("Receiving 'P' from Matlab:"):
            self.P = self.eng.workspace['P']

        # init OrthoView in helper
        self.spmHelperP = {
            'Type': self.P['Type'],
            'StructBgFile': os.path.normpath(self.P['StructBgFile']),
            'MCTempl': os.path.normpath(self.P['MCTempl']),
            'memMapFile': self.eng.evalin('base', 'P.memMapFile'),
            'tRoiBoundaries': [],
            'cRoiBoundaries': [],
            'sRoiBoundaries': [],
            'isRestingState': self.P['isRestingState'],
            'isIGLM': self.P['isIGLM'],
            'isROI': config.USE_ROI,
        }

        self.engSPM.helperPrepareOrthView(self.spmHelperP, 'bgEPI', nargout=0)

    # --------------------------------------------------------------------------
    def readOrthViewImages(self):
        memmap_fname = self.eng.evalin('base', 'P.memMapFile')

        # background anat or epi
        background_memmap_fname = memmap_fname.replace('shared', 'BackgOrthView')
        self.proj_background_images_reader.read(background_memmap_fname, self.engSPM)

        # SNR or stat map
        pos_map_memmap_fname = memmap_fname.replace('shared', 'OrthView')
        self.proj_pos_map_images_reader.read(pos_map_memmap_fname, self.engSPM)

        neg_map_memmap_fname = memmap_fname.replace('shared', 'OrthView_neg')
        self.proj_neg_map_images_reader.read(neg_map_memmap_fname, self.engSPM)

        # ROI from helperP
        self.spmHelperP = self.engSPM.workspace['helperP']

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
        filesize = os.path.getsize(path)
        if self.typicalFileSize <= 0:
            time.sleep(0.050)
            if filesize < os.path.getsize(path):
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
            self.typicalFileSize = os.path.getsize(path)

        return acquisitionFinished

    # --------------------------------------------------------------------------
    def callMainLoopIteration(self):
        if self.eng is None:
            return

        self.mainLoopLock.acquire()
        if self.isMainLoopEntered:
            self.mainLoopLock.release()
            return
        self.isMainLoopEntered = True
        self.mainLoopLock.release()

        if self.preiteration < self.iteration:
            # this code is executed before file is aquired

            self.eng.mainLoopEntry(self.iteration, nargout=0)

            self.displayData = self.eng.initDispalyData(self.iteration)

            # t6, display instruction prior to data acquisition for current iteration
            self.recorder.recordEvent(erd.Times.t6, self.iteration)

            # display instruction prior to data acquisition for current iteration
            if self.P['Type'] == 'PSC':
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

        if self.cbUseTCPData.isChecked() and self.eng.evalin('base', 'tcp.BytesAvailable'):
            fname = os.path.join(self.P['WatchFolder'],
                                 self.P['FirstFileName'])  # first file is required for initialization
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
            path = os.path.join(self.P['WatchFolder'], fname)
            if (not (self.cbUseTCPData.isChecked()) or not (self.reachedFirstFile)) and not self.isOffline:
                if not self.checkFileIsReady(path, fname):
                    self.isMainLoopEntered = False
                    return

            self.files_exported.append(fname)

        # check file sequence
        if (not self.isOffline) and (len(self.files_processed) > 0):

            last_fname = self.files_processed[-1]
            r = re.findall(r'\D(\d+).\w+$', last_fname)
            last_num = int(r[-1])
            new_fname = fname
            fname = None
            for cur_fname in self.files_exported:
                r = re.findall(r'\D(\d+).\w+$', cur_fname)
                cur_num = int(r[-1])
                if cur_num - last_num == 1:
                    fname = cur_fname
                    break

            if fname is None:
                if new_fname is not None:
                    logger.warning('Non-sequental export: ' + new_fname)
                self.isMainLoopEntered = False
                return
            else:
                self.files_exported.remove(fname)

        # t2
        self.recorder.recordEvent(erd.Times.t2, self.iteration, time.time())

        if not self.reachedFirstFile:
            if not self.P['FirstFileName'] in fname:
                logger.info('Volume skiped, waiting for first file')
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

        logger.info('Call iteration for file "{}"', os.path.basename(fname))

        # Start elapsed time
        startingTime = time.time()

        self.previousIterStartTime = startingTime

        if self.iteration == 1:
            with utils.timeit('  setup after first volume:'):
                self.eng.setupFirstVolume(fname, nargout=0)
                self.engSPM.assignin('base', 'matTemplMotCorr',
                                     self.eng.evalin('base', 'mainLoopData.matTemplMotCorr'),
                                     nargout=0)
                self.engSPM.assignin('base', 'dimTemplMotCorr',
                                     self.eng.evalin('base', 'mainLoopData.dimTemplMotCorr'),
                                     nargout=0)

        # Main logic
        # data preprocessing
        with utils.timeit('  preprocess fMRI Volume:'):
            self.eng.preprVol(fname, self.iteration, nargout=0)

        # t3
        self.recorder.recordEvent(erd.Times.t3, self.iteration, time.time())
        self.updatePlugins()

        if self.windowRTQA:
            is_rtqa_volume = self.windowRTQA.volumeCheckBox.isChecked()
        else:
            is_rtqa_volume = False

        if is_rtqa_volume and config.FIRST_SNR_VOLUME < self.iteration:
            self.updateOrthViewAsync()

        if (self.eng.evalin('base', 'mainLoopData.statMapCreated') == 1
                and not is_rtqa_volume):
            nrVoxInVol = self.eng.evalin('base', 'mainLoopData.nrVoxInVol')
            memMapFile = self.eng.evalin('base', 'P.memMapFile')

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

        elif self.P['Type'] == 'PSC':
            self.displayData = self.eng.nfbCalc(self.iteration, self.displayData, nargout=1)

            # t5
            self.recorder.recordEvent(erd.Times.t5, self.iteration, time.time())

            if self.P['Prot'] != 'Inter':
                if config.USE_PTB:
                    if self.displayData:
                        if self.P['Prot'] == 'ContTask':
                            #                       Here task condition is evaluated: if condition is 3 (task) and the current
                            #                       itteration corresponds with the onset of a task block (kept in TaskFirstVol)
                            #                       taskseq is set to one. While set to 1, Display  in ptbScreen.py
                            #                       will use the taskse flag to call the ptbTask function.
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
                self.displayData['dispValue'] = self.shamData[self.iteration - 1]

            if config.USE_UDP_FEEDBACK:
                logger.info('Sending by UDP - dispValue = {}', self.displayData['dispValue'])
                self.udpSender.send_data(self.displayData['dispValue'])

        # main logic end

        init = self.iteration == (self.P['nrSkipVol'] + 1)

        # rtQA calculation for time-series
        if bool(self.outputSamples) and self.windowRTQA:

            dataRealRaw = np.array(self.outputSamples['rawTimeSeries'], ndmin=2)
            dataGLM = np.array(self.eng.evalin('base', 'mainLoopData.glmProcTimeSeries(:,end)'), ndmin=2)
            dataProc = np.array(self.outputSamples['kalmanProcTimeSeries'], ndmin=2)
            dataMC = np.array(self.outputSamples['motCorrParam'], ndmin=2)
            n = len(dataRealRaw[0, :]) - 1
            data = dataRealRaw[:, n]

            if self.P['Type'] != 'DCM':
                betaCoeff = np.array(
                    self.eng.evalin('base', 'cellfun(@(a)a(mainLoopData.indVolNorm,2),rtQA_matlab.betRegr)'), ndmin=2)
            else:
                betaCoeff = np.zeros((int(self.P['NrROIs']),1))


            for i in range(int(self.P['NrROIs'])):
                self.windowRTQA.linTrendCoeff[i, n] = betaCoeff[i]

            posSpikes = np.array(self.eng.evalin('base', 'rtQA_matlab.kalmanSpikesPos(:,mainLoopData.indVolNorm)'),
                                 ndmin=2)
            negSpikes = np.array(self.eng.evalin('base', 'rtQA_matlab.kalmanSpikesNeg(:,mainLoopData.indVolNorm)'),
                                 ndmin=2)

            if self.P['Type'] == 'DCM' and (self.iteration - self.P['nrSkipVol']) in self.P['beginDCMblock'][0]:
                isNewDCMBlock = True
            else:
                isNewDCMBlock = False

            self.windowRTQA.calculateSNR(data, n, isNewDCMBlock)
            if not self.P['isRestingState']:
                self.windowRTQA.calculateCNR(data, n, isNewDCMBlock)
            self.windowRTQA.calculateSpikes(dataGLM, n, posSpikes, negSpikes)
            self.windowRTQA.calculateMSE(n, dataGLM, dataProc[:, n])

            self.windowRTQA.plotRTQA(n + 1)
            self.windowRTQA.plotDisplacements(dataMC[n, :], isNewDCMBlock)

        if self.imageViewMode == ImageViewMode.mosaic:
            with utils.timeit('Display mosaic image:'):
                self.displayMosaicImage()

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
        self.isMainLoopEntered = False

    # --------------------------------------------------------------------------
    def getFileSearchString(self, file_name_template, path, ext):
        file_series_part = re.findall(r"\{#:(\d+)\}", file_name_template)
        file_num_part = re.findall(r"_\d+_(\d+.\w+)", file_name_template)
        if len(file_series_part) > 0:
            file_series_len = int(file_series_part[0])
            fname = os.path.splitext(os.path.basename(path))[0][:-file_series_len]
            search_string = '%s*%s' % (fname, ext)
        elif len(file_num_part) > 0:
            fname = file_name_template.replace(file_num_part[0], "*")
            search_string = '%s%s' % (fname, ext)
        else:
            search_string = '*%s' % ext

        return search_string

    # --------------------------------------------------------------------------
    def startInOfflineMode(self):
        path = os.path.join(self.P['WatchFolder'], self.P['FirstFileName'])
        ext = re.findall(r"\.\w*$", str(path))
        if not ext:
            if self.P['DataType'] == 'IMAPH':
                ext = config.IMAPH_FILES_EXTENSION
            else:  # dicom as default
                ext = config.DICOM_FILES_EXTENSION
        else:
            ext = ext[-1]

        searchString = self.getFileSearchString(self.P['FirstFileNameTxt'], path, ext)
        path = os.path.join(os.path.dirname(path), searchString)

        files = sorted(glob.glob(path))

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

        path = os.path.join(self.P['WatchFolder'], self.P['FirstFileName'])

        ext = re.findall(r"\.\w*$", str(path))
        if not ext:
            if self.P['DataType'] == 'IMAPH':
                ext = config.IMAPH_FILES_EXTENSION
            else:  # dicom as default
                ext = config.DICOM_FILES_EXTENSION
        else:
            ext = ext[-1]

        searchString = self.getFileSearchString(self.P['FirstFileNameTxt'], path, ext)
        path = os.path.dirname(path)

        logger.info('Searching for {} in {}', searchString, path)

        event_handler = CreateFileEventHandler(
            searchString, self.files_queue, self.recorder)

        self.fs_observer = Observer()
        self.fs_observer.schedule(
            event_handler, path, recursive=True)

        self.call_timer.start()
        self.fs_observer.start()

    # --------------------------------------------------------------------------
    def makeRoiPlotLegend(self):
        roiNames = []
        dyn = ' dyn' if self.P['DynROI'] else ''

        for roiName in self.P['ROINames']:
            roiName, _ = os.path.splitext(os.path.basename(roiName))
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

        if self.P['isRestingState']:
            grid = True;
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
        if not self.P['isRestingState']:
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
        logger.info('Using Matlab session "{}" for SPM', self.mlSpmHelper.name)

        if config.USE_MATLAB_MODEL_HELPER:
            logger.info('Using Matlab session "{}" for Model Helper', self.mlModelHelper.name)

        self.mlMainHelper.prepare()

        if not (config.USE_MATLAB_MODEL_HELPER) and not (config.USE_PTB_HELPER):
            logger.warning('There is no main Matlab model helper. DCM calculation is not possible.')
        if config.USE_PTB_HELPER:
            self.mlPtbDcmHelper.prepare()
        self.mlSpmHelper.prepare()
        if config.USE_MATLAB_MODEL_HELPER:
            self.mlModelHelper.prepare()

        self.eng = self.mlMainHelper.engine
        self.engSPM = self.mlSpmHelper.engine

        self.eng.workspace['P'] = self.P
        self.eng.workspace['mainLoopData'] = self.mainLoopData
        self.eng.workspace['rtQA_matlab'] = self.rtQA_matlab

        self.frameParams.setEnabled(True)
        self.frameShortParams.setEnabled(True)
        self.btnSetup.setEnabled(self.isSetFileChosen)

        self.resetDone = True
        self.isInitialized = True

        self.pluginWindow = plugin.PluginWindow()
        self.btnPlugins.setEnabled(True)

        logger.info("Initialization finished ({:.2f} s)", time.time() - ts)

    # --------------------------------------------------------------------------
    def reset(self):
        self.P = {}
        self.mainLoopData = {}
        self.rtQA_matlab = {}
        self.reultFromHelper = None
        self.reachedFirstFile = False

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

        self.mosaic_background_image_reader.clear()
        self.mosaic_pos_map_image_reader.clear()
        self.mosaic_neg_map_image_reader.clear()

        self.proj_background_images_reader.clear()
        self.proj_pos_map_images_reader.clear()
        self.proj_neg_map_images_reader.clear()

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
            self.engSPM.workspace['P'] = self.P
            self.previousIterStartTime = 0

            with utils.timeit("  Load protocol data:"):
                self.loadJsonProtocol()

            with utils.timeit("  Selecting ROI:"):
                self.selectRoi()

            self.P.update(self.eng.workspace['P'])

            logger.info("  Setup plots...")
            if not self.P['isRestingState']:
                self.createMusterInfo()

            self.setupRoiPlots()
            self.setupMcPlots()

            with utils.timeit('  initMainLoopData:'):
                self.initMainLoopData()

            if config.USE_SHAM:
                logger.warning("Sham feedback has been selected")
                fext = os.path.splitext(self.P['ShamFile'])[1]
                if fext == '.txt':  # expect a textfile with float numbers in a single  column or row
                    NFBdata = np.loadtxt(self.P['ShamFile'], unpack=False)
                elif fext == '.mat':  # expect "mainLoopData"
                    NFBdata = loadmat(self.P['ShamFile'])['dispValues']

                dispValues = list(NFBdata.flatten())
                if len(dispValues) != self.P['NrOfVolumes']:
                    logger.error(
                        "Number of display values ({:d}) in {} does not correspond to number of volumes ({:d}).\n SELECT ANOTHER SHAM FILE".format(
                            len(dispValues), self.P['ShamFile'], self.P['NrOfVolumes']))
                    return
                self.shamData = [float(v) for v in dispValues]
                logger.info("Sham data has been loaded")

            if config.USE_PTB:
                self.stopDisplayThread = False
                self.displayThread = threading.Thread(target=self.onEventDisplay)
                self.displayThread.start()

                with utils.timeit("  Preparation of PTB Screen:"):
                    sid = self.cbScreenId.currentIndex() + 1
                    path = os.path.normpath(self.P['nfbDataFolder'])
                    eventRecordsPath = os.path.join(path,
                                                    'TimeVectors_display_' + str(self.P['NFRunNr']).zfill(2) + '.txt')

                    ptbP = {}
                    ptbP['eventRecordsPath'] = eventRecordsPath
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

                self.btnRTQA.setEnabled(True)

                if self.windowRTQA:
                    self.windowRTQA.deleteLater()

                self.windowRTQA = rtqa.RTQAWindow(parent=self)
                self.windowRTQA.volumeCheckBox.stateChanged.connect(self.onShowRtqaVol)
                self.windowRTQA.volumeCheckBox.stateChanged.connect(self.onChangeNegMapPolicy)
                self.windowRTQA.volumeCheckBox.stateChanged.connect(self.onInteractWithMapImage)
                self.windowRTQA.volumeCheckBox.toggled.connect(self.updateOrthViewAsync)
                self.windowRTQA.smoothedCheckBox.stateChanged.connect(self.onSmoothedChecked)
                self.windowRTQA.comboBox.currentIndexChanged.connect(self.onModeChanged)
                self.eng.assignin('base', 'rtQAMode', self.windowRTQA.currentMode, nargout=0)
                self.eng.assignin('base', 'isShowRtqaVol', self.windowRTQA.volumeCheckBox.isChecked(), nargout=0)
                self.eng.assignin('base', 'isSmoothed', self.windowRTQA.smoothedCheckBox.isChecked(), nargout=0)

                self.windowRTQA.isStopped = False;

            else:
                self.eng.assignin('base', 'rtQAMode', False, nargout=0)
                self.eng.assignin('base', 'isShowRtqaVol', False, nargout=0)
                self.eng.assignin('base', 'isSmoothed', False, nargout=0)

            self.onChangeNegMapPolicy()
            self.eng.assignin('base', 'imageViewMode', int(self.imageViewMode), nargout=0)
            self.eng.assignin('base', 'FIRST_SNR_VOLUME', config.FIRST_SNR_VOLUME, nargout=0)
            self.cbImageViewMode.setEnabled(False)
            self.cbImageViewMode.setCurrentIndex(0)
            self.isStopped = False

    # --------------------------------------------------------------------------
    def start(self):
        logger.info("*** Started ***")

        self.cbImageViewMode.setEnabled(True)
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
        self.orthViewUpdateCheckTimer.start(50)
        self.files_exported = []
        self.files_processed = []

    # --------------------------------------------------------------------------
    def stop(self):

        self.isStopped = True
        if self.windowRTQA:
            self.windowRTQA.isStopped = True;
            self.eng.workspace['rtQA_python'] = self.windowRTQA.dataPacking()
        self.btnStop.setEnabled(False)
        self.btnStart.setEnabled(False)
        self.btnSetup.setEnabled(True)
        self.btnPlugins.setEnabled(True)

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
            path = os.path.normpath(self.P['nfbDataFolder'])
            fname = os.path.join(path, 'TimeVectors_' + str(self.P['NFRunNr']).zfill(2) + '.txt')
            self.recorder.savetxt(fname)

        if self.fFinNFB:
            for i in range(len(self.plugins)): self.plugins[i].finalize()
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
        config.USE_RTQA = True

    # --------------------------------------------------------------------------
    def onShowRtqaVol(self):

        is_rtqa_volume = self.windowRTQA.volumeCheckBox.isChecked()
        self.eng.assignin('base', 'isShowRtqaVol', is_rtqa_volume, nargout=0)

        if self.isStopped:
            self.eng.offlineImageSwitch(nargout=0)

    # --------------------------------------------------------------------------
    def onSmoothedChecked(self):

        is_rtqa_smoothed = self.windowRTQA.smoothedCheckBox.isChecked()
        self.eng.assignin('base', 'isSmoothed', is_rtqa_smoothed, nargout=0)

    # --------------------------------------------------------------------------
    def onModeChanged(self):

        if self.windowRTQA:
            self.windowRTQA.onComboboxChanged()
            self.eng.assignin('base', 'rtQAMode', self.windowRTQA.currentMode, nargout=0)
            self.onShowRtqaVol()

        if not self.btnSetup.isEnabled():
            self.updateOrthViewAsync()
            self.onInteractWithMapImage()

        if self.isStopped:
            self.eng.offlineImageSwitch(nargout=0)

    # --------------------------------------------------------------------------
    def onChooseSetFile(self):
        if config.DONOT_USE_QFILE_NATIVE_DIALOG:
            fname = QFileDialog.getOpenFileName(
                self, "Select 'SET File'", self.settingFileName, 'ini files (*.ini)',
                options=QFileDialog.DontUseNativeDialog)[0]
        else:
            fname = QFileDialog.getOpenFileName(
                self, "Select 'SET File'", self.settingFileName, 'ini files (*.ini)')[0]

        fname = fname.replace('/', os.path.sep)
        self.chooseSetFile(fname)

    # --------------------------------------------------------------------------
    def chooseSetFile(self, fname):
        if not fname:
            return

        if not os.path.isfile(fname):
            return

        fname = fname.replace('/', os.path.sep)

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

        fname = fname.replace('/', os.path.sep)
        self.chooseWeightsFile(fname)

    # --------------------------------------------------------------------------
    def chooseWeightsFile(self, fname):
        if not fname:
            return

        if not os.path.isfile(fname):
            return
        fname = fname.replace('/', os.path.sep)
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

        fname = fname.replace('/', os.path.sep)
        if fname:
            self.leProtocolFile.setText(fname)
            self.P['ProtocolFile'] = fname

    # --------------------------------------------------------------------------
    def onChooseStructBgFile(self):
        if config.DONOT_USE_QFILE_NATIVE_DIALOG:
            fname = QFileDialog.getOpenFileName(
                self, "Select Structural File", config.ROOT_PATH, 'Template files (*.nii)',
                options=QFileDialog.DontUseNativeDialog)[0]
        else:
            fname = QFileDialog.getOpenFileName(
                self, "Select Structural File", config.ROOT_PATH, 'Template files (*.nii)')[0]

        fname = fname.replace('/', os.path.sep)
        if fname:
            self.leStructBgFile.setText(fname)
            self.P['StructBgFile'] = fname

    # --------------------------------------------------------------------------
    def onChooseMCTemplFile(self):
        if config.DONOT_USE_QFILE_NATIVE_DIALOG:
            fname = QFileDialog.getOpenFileName(
                self, "Select MCTempl File", config.ROOT_PATH, 'Template files (*.nii)',
                options=QFileDialog.DontUseNativeDialog)[0]
        else:
            fname = QFileDialog.getOpenFileName(
                self, "Select MCTempl File", config.ROOT_PATH, 'Template files (*.nii)')[0]

        fname = fname.replace('/', os.path.sep)
        if fname:
            self.leMCTempl.setText(fname)
            self.P['MCTempl'] = fname

    # --------------------------------------------------------------------------
    def onChooseFolder(self, name, le):
        dname = QFileDialog.getExistingDirectory(
            self, "Select '{}' directory".format(name), config.ROOT_PATH)
        dname = dname.replace('/', os.path.sep)
        if dname:
            le.setText(dname)
            self.P[name] = dname

    # --------------------------------------------------------------------------
    def onChooseFile(self, name, le):
        if config.DONOT_USE_QFILE_NATIVE_DIALOG:
            fname = QFileDialog.getOpenFileName(
                self, "Select '{}' directory".format(name), config.ROOT_PATH, 'Any file (*.*)',
                options=QFileDialog.DontUseNativeDialog)[0]
        else:
            fname = QFileDialog.getOpenFileName(
                self, "Select '{}' directory".format(name), config.ROOT_PATH, 'Any file (*.*)')[0]

        fname = fname.replace('/', os.path.sep)
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

        if self.eng:
            self.eng.assignin('base', 'imageViewMode', int(mode), nargout=0)

        if self.cbImageViewMode.isEnabled():
            self.updateOrthViewAsync()
            self.onInteractWithMapImage()

    # --------------------------------------------------------------------------
    def updateOrthViewAsync(self):
        if not self.engSPM:
            return

        if self.imageViewMode == ImageViewMode.orthviewEPI:
            bgType = 'bgEPI'
        else:
            bgType = 'BgStruct'

        rtqa = self.windowRTQA.volumeCheckBox.isChecked() if self.windowRTQA else False

        self.orthViewUpdateFuture = self.engSPM.helperUpdateOrthView(
            self.currentCursorPos, self.currentProjection.value, bgType,
            rtqa, background=True, nargout=0)

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
        if sender is self.neg_map_thresholds_widget:
            self.neg_map_thresholds_widget.auto_thresholds = False

        if self.imageViewMode == ImageViewMode.mosaic:
            self.displayMosaicImage()

        for proj in projview.ProjectionType:
            pos_map_image = self.proj_pos_map_images_reader.proj_image(proj)

            if pos_map_image is not None:
                rgba_pos_map_image = self.pos_map_thresholds_widget.compute_rgba(pos_map_image)

                if rgba_pos_map_image is not None:
                    self.orthView.set_pos_map_image(proj, rgba_pos_map_image)

            neg_map_image = self.proj_neg_map_images_reader.proj_image(proj)

            if neg_map_image is not None:
                rgba_neg_map_image = self.neg_map_thresholds_widget.compute_rgba(neg_map_image)

                if rgba_neg_map_image is not None:
                    self.orthView.set_neg_map_image(proj, rgba_neg_map_image)

    # --------------------------------------------------------------------------
    def onCheckOrthViewUpdated(self):
        if not self.orthViewUpdateFuture or not self.orthViewUpdateFuture.done():
            return

        self.orthViewUpdateInProgress = True

        # with utils.timeit('Getting new orthview projections...'):
        self.readOrthViewImages()

        # SNR/Stat map display
        is_stat_map_created = bool(self.eng.evalin('base', 'mainLoopData.statMapCreated'))
        is_snr_map_created = bool(self.eng.evalin('base', 'rtQA_matlab.snrMapCreated'))
        if self.windowRTQA:
            is_rtqa_volume_checked = self.windowRTQA.volumeCheckBox.isChecked()
        else:
            is_rtqa_volume_checked = False

        if (self.imageViewMode != ImageViewMode.mosaic) and (is_stat_map_created and not is_rtqa_volume_checked
                                                             or is_snr_map_created and is_rtqa_volume_checked):
            pos_maps_values = np.array([], dtype=np.uint8)
            neg_maps_values = np.array([], dtype=np.uint8)

            for proj in projview.ProjectionType:
                pos_map_image = self.proj_pos_map_images_reader.proj_image(proj)
                pos_maps_values = np.append(pos_maps_values, pos_map_image.ravel())

                neg_map_image = self.proj_neg_map_images_reader.proj_image(proj)
                neg_maps_values = np.append(neg_maps_values, neg_map_image.ravel())

                if pos_maps_values.size > 0:
                    self.pos_map_thresholds_widget.compute_thresholds(pos_maps_values)
                if neg_maps_values.size > 0:
                    self.neg_map_thresholds_widget.compute_thresholds(neg_maps_values)

        for proj in projview.ProjectionType:
            bg_image = self.proj_background_images_reader.proj_image(proj)
            self.orthView.set_background_image(proj, bg_image)

            pos_map_image = self.proj_pos_map_images_reader.proj_image(proj)
            rgba_pos_map_image = self.pos_map_thresholds_widget.compute_rgba(pos_map_image)

            neg_map_image = self.proj_neg_map_images_reader.proj_image(proj)
            rgba_neg_map_image = self.neg_map_thresholds_widget.compute_rgba(neg_map_image)

            if rgba_pos_map_image is not None:
                self.orthView.set_pos_map_image(proj, rgba_pos_map_image)

            if rgba_neg_map_image is not None:
                self.orthView.set_neg_map_image(proj, rgba_neg_map_image)

        self.orthView.set_roi(projview.ProjectionType.transversal, self.spmHelperP['tRoiBoundaries'])
        self.orthView.set_roi(projview.ProjectionType.coronal, self.spmHelperP['cRoiBoundaries'])
        self.orthView.set_roi(projview.ProjectionType.sagittal, self.spmHelperP['sRoiBoundaries'])

        if self.orthViewInitialize:
            self.orthView.reset_view()

        self.orthViewInitialize = False
        self.orthViewUpdateInProgress = False
        self.orthViewUpdateFuture = None

    # --------------------------------------------------------------------------
    def loadSettingsFromSetFile(self):
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

    # --------------------------------------------------------------------------
    def loadJsonProtocol(self):
        self.eng.loadJsonProtocol(nargout=0)

    # --------------------------------------------------------------------------
    def selectRoi(self):

        if self.P['Type'] == 'PSC':
            if not os.path.isdir(self.P['RoiFilesFolder']):
                logger.error("Couldn't find: " + self.P['RoiFilesFolder'])
                return

            self.eng.selectROI(self.P['RoiFilesFolder'], nargout=0)
            self.engSPM.selectROI(self.P['RoiFilesFolder'], nargout=0)

        elif self.P['Type'] == 'SVM':

            if not os.path.isdir(self.P['RoiFilesFolder']):
                logger.error("Couldn't find: " + self.P['RoiFilesFolder'])
                return

            self.eng.selectROI(self.P['RoiFilesFolder'], nargout=0)
            self.engSPM.selectROI(self.P['RoiFilesFolder'], nargout=0)

        elif self.P['Type'] == 'DCM':
            p = [self.P['RoiAnatFolder'], self.P['RoiGroupFolder']]
            self.eng.selectROI(p, nargout=0)
            self.engSPM.selectROI(p, nargout=0)
        elif self.P['Type'] == 'None':
            if not os.path.isdir(self.P['RoiFilesFolder']):
                logger.error("Couldn't find: " + self.P['RoiFilesFolder'])
                return

            self.eng.selectROI(self.P['RoiFilesFolder'], nargout=0)
            self.engSPM.selectROI(self.P['RoiFilesFolder'], nargout=0)

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
        self.P['isRestingState'] = bool(self.cbProt.currentText() == "Rest")
        self.P['isRTQA'] = config.USE_RTQA;
        self.P['isIGLM'] = config.USE_IGLM;
        self.P['isZeroPadding'] = config.zeroPaddingFlag;
        self.P['nrZeroPadVol'] = config.nrZeroPadVol;

        if self.P['Prot'] == 'ContTask':
            self.P['TaskFolder'] = self.leTaskFolder.text()

        self.P['MaxFeedbackVal'] = float(self.leMaxFeedbackVal.text())
        self.P['MinFeedbackVal'] = float(self.leMinFeedbackVal.text())
        self.P['FeedbackValDec'] = self.sbFeedbackValDec.value()
        self.P['NegFeedback'] = self.cbNegFeedback.isChecked()

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
        self.leFirstFilePath.setText('%s%s%s' % (self.P['WatchFolder'], os.path.sep, self.P['FirstFileName']))

        filePathStatus = ""
        if os.path.isdir(self.P['WatchFolder']):
            filePathStatus += "MRI Watch Folder exists. "
        else:
            filePathStatus += "MRI Watch Folder does not exists. "
        if os.path.isfile(self.leFirstFilePath.text()):
            filePathStatus += "First file exists. "
        else:
            filePathStatus += "First file does not exist. "

        # if os.path.isdir( self.P['WatchFolder'],os.path.sep,self.P['FirstFileName'] )
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
    def displayMosaicImage(self):
        background_image = None
        pos_map_image = None
        neg_map_image = None

        if 'imgViewTempl' not in self.P:
            if self.eng.evalin('base', 'length(imgViewTempl)') > 0:
                filename = self.eng.evalin('base', 'P.memMapFile')

                with utils.timeit("Receiving mosaic image from Matlab (read memmap):"):
                    self.mosaic_background_image_reader.read(filename, self.eng)
                background_image = self.mosaic_background_image_reader.image

                if background_image.size > 0:
                    self.mosaicImageView.set_background_image(background_image)
            else:
                return

        # SNR/Stat map display
        is_stat_map_created = bool(self.eng.evalin('base', 'mainLoopData.statMapCreated'))
        if self.windowRTQA:
            is_rtqa_volume_checked = self.windowRTQA.volumeCheckBox.isChecked()
            is_snr_map_created = bool(self.eng.evalin('base', 'rtQA_matlab.snrMapCreated'))
        else:
            is_rtqa_volume_checked = False
            is_snr_map_created = False

        if (background_image is not None
                and (is_stat_map_created and not is_rtqa_volume_checked
                     or is_snr_map_created and is_rtqa_volume_checked)):
            with utils.timeit("Receiving mosaic maps from Matlab:"):
                filename_pat = self.eng.evalin('base', 'P.memMapFile')
                filename_pos = filename_pat.replace('shared', 'statMap')
                filename_neg = filename_pat.replace('shared', 'statMap_neg')

                self.mosaic_pos_map_image_reader.read(filename_pos, self.eng)
                self.mosaic_neg_map_image_reader.read(filename_neg, self.eng)

            pos_map_image = self.mosaic_pos_map_image_reader.image
            neg_map_image = self.mosaic_neg_map_image_reader.image

        if pos_map_image is not None:
            self.pos_map_thresholds_widget.compute_thresholds(pos_map_image)
            rgba_pos_map_image = self.pos_map_thresholds_widget.compute_rgba(pos_map_image)

            if rgba_pos_map_image is not None:
                self.mosaicImageView.set_pos_map_image(rgba_pos_map_image)
        else:
            self.mosaicImageView.clear_pos_map()

        if neg_map_image is not None:
            self.neg_map_thresholds_widget.compute_thresholds(neg_map_image)
            rgba_neg_map_image = self.neg_map_thresholds_widget.compute_rgba(neg_map_image)

            if rgba_neg_map_image is not None:
                self.mosaicImageView.set_neg_map_image(rgba_neg_map_image)
        else:
            self.mosaicImageView.clear_neg_map()

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

        dataRaw = np.array(self.outputSamples[key], ndmin=2)
        dataProc = np.array(self.outputSamples['kalmanProcTimeSeries'], ndmin=2)
        dataNorm = np.array(self.outputSamples['scalProcTimeSeries'], ndmin=2)

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

            for i, c in zip(range(sz), config.ROI_PLOT_COLORS):
                pen = pg.mkPen(color=c, width=config.ROI_PLOT_WIDTH)
                p = plotitem.plot(pen=pen)
                plots.append(p)

            self.drawGivenRoiPlot.__dict__[plotitem] = plots, muster

        x = np.arange(1, l + 1, dtype=np.float64)

        for p, y in zip(self.drawGivenRoiPlot.__dict__[plotitem][0], data):
            p.setData(x=x, y=np.array(y))

        if self.P['Prot'] != 'InterBlock':
            if plotwidget == self.procRoiPlot:
                self.drawMinMaxProcRoiPlot(
                    init, data,
                    self.outputSamples['posMin'],
                    self.outputSamples['posMax'])

        items = plotitem.listDataItems()

        for m in self.drawGivenRoiPlot.__dict__[plotitem][1]:
            items.remove(m)

        plotitem.autoRange(items=items)
        if self.P['isRestingState']:
            grid = True;
        else:
            grid = False
        self.basicSetupPlot(plotitem, grid)

    # --------------------------------------------------------------------------
    def drawMusterPlot(self, plotitem: pg.PlotItem):
        ylim = config.MUSTER_Y_LIMITS

        if not self.P['isRestingState']:
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

            for i, c in zip(range(sz), config.ROI_PLOT_COLORS):
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
            mi = np.array(mi)
            ma = np.array(ma)
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
        self.settingFileName = self.appSettings.value(
            'SettingFileName', self.settingFileName)

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
        ns = mgr.Namespace()
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

# -*- coding: utf-8 -*-

"""

__________________________________________________________________________
Copyright (C) 2016-2021 OpenNFT.org

"""

from pathlib import Path
import pyqtgraph as pg


APP_NAME = 'OpenNFT'
LOG_LEVEL = 'DEBUG'

ROOT_PATH = Path(__file__).absolute().resolve().parent
UI_PATH = ROOT_PATH / 'ui'
PLUGIN_PATH = ROOT_PATH / 'plugins'
OpenNFT_ICON = ROOT_PATH / 'ui' / 'images' / 'appicon.png'
MATLAB_FUNCTIONS_PATH = ROOT_PATH / 'matlab'

AUTO_RTQA = False
SELECT_ROIS = False
USE_EPI_TEMPLATE = False
AUTO_RTQA_SETTINGS = ROOT_PATH / 'configs' / 'auto_rtqa_settings.ini'

# Matlab sessions
MAIN_MATLAB_NAME = 'MATLAB_NFB_MAIN'
PTB_MATLAB_NAME = 'MATLAB_NFB_PTB'
MODEL_HELPER_MATLAB_NAME = 'MATLAB_NFB_MODEL_HELPER'

MAIN_MATLAB_STARTUP_OPTIONS = '-nodesktop'
PTB_MATLAB_STARTUP_OPTIONS = '-nodesktop'
MODEL_HELPER_MATLAB_STARTUP_OPTIONS = '-nodesktop'

MATLAB_NAME_SUFFIX = ''

# MRI scan file extensions
DICOM_FILES_EXTENSION = '.dcm'
IMAPH_FILES_EXTENSION = '.img'

# For test purposes
USE_YIELD = True

# MRI triggering is required
USE_MRPULSE = False

# Time between two iterations
MAIN_LOOP_CALL_PERIOD = 30  # ms
# Fast offline loop for debugging
USE_FAST_OFFLINE_LOOP = True

# currently used only for DCM feedabck
USE_MATLAB_MODEL_HELPER = False

# use PTB helper and include PTB option in parameters
USE_PTB_HELPER = True

# use only when FFileDialog.by crashes when opening the dialog windows
DONOT_USE_QFILE_NATIVE_DIALOG = False

# the length of the TimeVector
# TIMEVECTOR_LENGTH = 8

# plotting initialization
PLOT_GRID_ALPHA = 0.7
ROI_PLOT_WIDTH = 2.0
MUSTER_Y_LIMITS = (-32767, 32768)
# transparency of design template overlay
MUSTER_PLOT_ALPHA = 50
MAX_ROI_NAME_LENGTH = 6

ROI_PLOT_COLORS = [
    pg.mkColor(0, 0, 255, 255),
    pg.mkColor(0, 255, 255, 255),
    pg.mkColor(0, 255, 0, 255),
    pg.mkColor(255, 0, 255, 255),
    pg.mkColor(255, 0, 0, 255),
    pg.mkColor(255, 255, 0, 255),
    pg.mkColor(140, 200, 240, 255),
    pg.mkColor(208, 208, 147, 255),
    pg.mkColor(147, 0, 0, 255),
    pg.mkColor(100, 175, 0, 255),
    pg.mkColor(147, 255, 0, 255),
    pg.mkColor(120, 147, 147, 255)
]

MUSTER_PEN_COLORS = [
    (73, 137, 255, 255),
    (255, 103, 86, 255),
    (22, 255, 104, 255),
    (200, 200, 100, 255),
    (125, 125, 125, 255),
    (200, 100, 200, 255),
    (100, 200, 200, 255),
    (255, 22, 104, 255),
    (250, 104, 22, 255),
    (245, 245, 245, 255)
]
MUSTER_BRUSH_COLORS = [
    (124, 196, 255, MUSTER_PLOT_ALPHA),
    (255, 156, 117, MUSTER_PLOT_ALPHA),
    (127, 255, 157, MUSTER_PLOT_ALPHA),
    (200, 200, 100, MUSTER_PLOT_ALPHA),
    (125, 125, 125, MUSTER_PLOT_ALPHA),
    (200, 100, 200, MUSTER_PLOT_ALPHA),
    (100, 200, 200, MUSTER_PLOT_ALPHA),
    (255, 22, 104, MUSTER_PLOT_ALPHA),
    (250, 104, 22, MUSTER_PLOT_ALPHA),
    (245, 245, 245, MUSTER_PLOT_ALPHA)
]

# Motion correction plot colors
MC_PLOT_COLORS = [
    (255, 123, 0),   # translations - x, y, z
    (255, 56, 109),
    (127, 0, 255),
    (0, 46, 255),    # rotations - alpha, betta, gamma
    (0, 147, 54),
    (145, 130, 43),
]

PROJ_ROI_COLORS = ROI_PLOT_COLORS

# debugging use only
USE_SLEEP_IN_STOP = False
HIDE_TEST_BTN = True

# Flag for new Siemens XA30 DICOM format
DICOM_SIEMENS_XA30 = False

# rtQA may cause linear performance loss on the big data
# due to saving process of iGLM quality parameters
USE_RTQA = True
USE_IGLM = True
USE_ROI = True
FIRST_SNR_VOLUME = 1

# zero padding settings
zeroPaddingFlag = False
nrZeroPadVol = 3

# FD defaults
DEFAULT_FD_RADIUS = 50  # radius multiplying angular displacement in FD compution
DEFAULT_FD_THRESHOLDS = [0.1, 0.2, 0.5]  # FD thresholds to display by default

# DVARS
DEFAULT_DVARS_THRESHOLD = 5

# plot display defaults
PLOT_BACKGROUND_COLOR = (255, 255, 255)

PLOT_PEN_COLORS = [
    # colors used to plot motion correction metrics
    pg.mkPen(pg.mkColor(0, 46, 255), width=1.2),
    pg.mkPen(pg.mkColor(255, 123, 0), width=1.2),
    pg.mkPen(pg.mkColor(255, 56, 109), width=1.2),
    pg.mkPen(pg.mkColor(127, 0, 255), width=1.2),
    pg.mkPen(pg.mkColor(0, 147, 54), width=1.2),
    pg.mkPen(pg.mkColor(145, 130, 43), width=1.2),
    pg.mkPen(pg.mkColor(0, 0, 0), width=1.2)
]

# -*- coding: utf-8 -*-

"""

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

"""

import os
import pyqtgraph as pg


LOG_LEVEL = 'DEBUG'

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
UI_PATH = os.path.join(ROOT_PATH, 'UI')
OpenNFT_ICON = os.path.join(ROOT_PATH, 'ui', 'images', 'appicon.png')
MATLAB_FUNCTIONS_PATH = os.path.join(ROOT_PATH, 'matlab')

# Matlab sessions
MAIN_MATLAB_NAME = 'MATLAB_NFB_MAIN'
PTB_MATLAB_NAME = 'MATLAB_NFB_PTB'
SPM_MATLAB_NAME = 'MATLAB_NFB_SPM'
MODEL_HELPER_MATLAB_NAME = 'MATLAB_NFB_MODEL_HELPER'

MAIN_MATLAB_STARTUP_OPTIONS = '-nodesktop'
PTB_MATLAB_STARTUP_OPTIONS = '-nodesktop'
SPM_MATLAB_STARTUP_OPTIONS = '-nodesktop'
MODEL_HELPER_MATLAB_STARTUP_OPTIONS = '-nodesktop'

MATLAB_NAME_SUFFIX = ''

# MRI scan file extensions
DICOM_FILES_EXTENSION = '.dcm'
IMAPH_FILES_EXTENSION = '.img'

# MRI triggering is required
USE_MRPULSE = False

# Time between two iterations
MAIN_LOOP_CALL_PERIOD = 30  # ms
# Fast offline loop for debugging
USE_FAST_OFFLINE_LOOP = True

# currently used only for DCM feedabck
USE_MATLAB_MODEL_HELPER = True

# use only when FFileDialog.by crashes when opening the dialog windows
DONOT_USE_QFILE_NATIVE_DIALOG = False

# the length of the TimeVector
#TIMEVECTOR_LENGTH = 8

# plotting initialization
PLOT_GRID_ALPHA = 0.7
ROI_PLOT_WIDTH = 2.0
ROI_PLOT_COLORS = ['b', 'r', 'g']
MUSTER_Y_LIMITS = (-1000, 1000)
MUSTER_PLOT_ALPHA = 220
MAX_ROI_NAME_LENGTH = 6

MUSTER_PEN_COLORS = [
    (73, 137, 255, 255),
    (255, 103, 86, 255),
    (22, 255, 104, 255),
    (255, 255, 255, 255)
]

MUSTER_BRUSH_COLORS = [
    (124, 196, 255, MUSTER_PLOT_ALPHA),
    (255, 156, 117, MUSTER_PLOT_ALPHA),
    (127, 255, 157, MUSTER_PLOT_ALPHA),
    (255, 255, 255, MUSTER_PLOT_ALPHA)
]

MC_PLOT_COLORS = [
    (255, 123, 0),
    (255, 56, 109),
    (127, 0, 255),
    (0, 46, 255),
    (0, 147, 54),
    (145, 130, 43),
]

#debuging use only
USE_SLEEP_IN_STOP = False
HIDE_TEST_BTN = True

USE_RTQA = False
FIRST_SNR_VOLUME = 2

# FD defaults
DEFAULT_FD_RADIUS = 50 # radius multiplying angular displacement in FD compution
DEFAULT_FD_THRESHOLDS = [0.2, 0.5] # FD thresholds to display by default

# plot display defaults
PLOT_BACKGROUND_COLOR = (255, 255, 255);
PLOT_PEN_COLORS = [ # colors used to plot motion correction metrics
    pg.mkPen(pg.mkColor(0, 46, 255), width=1.2),
    pg.mkPen(pg.mkColor(255, 123, 0), width=1.2),
    pg.mkPen(pg.mkColor(255, 56, 109), width=1.2),
    pg.mkPen(pg.mkColor(127, 0, 255), width=1.2),
    pg.mkPen(pg.mkColor(0, 147, 54), width=1.2),
    pg.mkPen(pg.mkColor(145, 130, 43), width=1.2)]




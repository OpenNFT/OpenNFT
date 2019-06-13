# -*- coding: utf-8 -*-

"""

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

"""

import os


LOG_LEVEL = 'DEBUG'

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
UI_PATH = os.path.join(ROOT_PATH, 'UI')
OpenNFT_ICON = os.path.join(ROOT_PATH, 'ui', 'images', 'appicon.png')
MATLAB_FUNCTIONS_PATH = os.path.join(ROOT_PATH, 'matlab')

# matlab processes
MAIN_MATLAB_SHARED_NAME_PREFIX = 'MATLAB_NFB_MAIN_'
PTB_MATLAB_SHARED_NAME_PREFIX = 'MATLAB_NFB_PTB_'
SPM_MATLAB_SHARED_NAME_PREFIX = 'MATLAB_NFB_SPM_'
MODEL_HELPER_MATLAB_SHARED_NAME_PREFIX = 'MATLAB_NFB_MODEL_HELPER_'

# if False we only detach Matlab sessions on exit
# useful when debugging
CLOSE_MATLAB_ON_EXIT = True

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
]

MUSTER_BRUSH_COLORS = [
    (124, 196, 255, MUSTER_PLOT_ALPHA),
    (255, 156, 117, MUSTER_PLOT_ALPHA),
    (127, 255, 157, MUSTER_PLOT_ALPHA),
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


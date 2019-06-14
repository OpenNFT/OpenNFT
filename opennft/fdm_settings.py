# Global settings and variables

import os
import pyqtgraph as pg

# Default format for files to accept as input for conversion (in watch_directory)
DEFAULT_INPUT_FILTER = "([0-9]+)_(?P<run>[0-9]+)_(?P<frame>[0-9]+).dcm" 
DEFAULT_NII_FILTER = "f.*.nii" # acceptable converted files for realignement (in nii_subdirectory)

# FD defaults
DEFAULT_FD_RADIUS = 50 # radius multiplying angular displacement in FD compution
DEFAULT_FD_THRESHOLDS = [0.2, 0.5] # FD thresholds to display by default

# UI
ECHO_STATUS_BAR_IN_TERMINAL = False # print in terminal all the infos normally displayed in the status bar

# plot display defaults
PLOT_INITIAL_XMAX = 20 # initial size of the x axis (frame number)
PLOT_BACKGROUND_COLOR = (255, 255, 255);
PLOT_PEN_COLORS = [ # colors used to plot motion correction metrics
    pg.mkPen(pg.mkColor(0, 46, 255), width=1.2),
    pg.mkPen(pg.mkColor(255, 123, 0), width=1.2),
    pg.mkPen(pg.mkColor(255, 56, 109), width=1.2),
    pg.mkPen(pg.mkColor(127, 0, 255), width=1.2),
    pg.mkPen(pg.mkColor(0, 147, 54), width=1.2),
    pg.mkPen(pg.mkColor(145, 130, 43), width=1.2)]
PLOT_EXPORT_WIDTH = 400
PLOT_EXPORT_HEIGHT = 200
PLOT_EXPORT_FORMAT = ".png"


# paths and filenames 
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
FDM_PATH = os.path.join(ROOT_PATH, 'fdm')
OPENNFT_PATH = os.path.join(ROOT_PATH, 'OpenNFT.py')

DEFAULT_WATCH_DIRECTORY_PATH = 'C:\\rtExport\\' #FDM_PATH # os.path.join(FDM_PATH, 'data')
NII_DIRECTORY_PATH = os.path.join(FDM_PATH, 'data')
STAT_DIRECTORY_PATH = os.path.join(FDM_PATH, 'stat')
FDM_OUTPUT = 'MC_summary.csv'

MATLAB_FUNCTIONS_PATH = FDM_PATH # modify to place the .m scripts elsewhere
MATLAB_CONVERT_FILENAME = 'fdm_convert_dcm_to_nii.m'
MATLAB_ALIGN2_FILENAME = 'fdm_align2_nii.m'
SPM_PREPROCESSING_BATCH_FILENAME = 'preprocess_nii.m'
SPM_REGRESS_BATCH_FILENAME = 'regress_fdm.m'

MATLAB_CONVERT_PATH = os.path.join(MATLAB_FUNCTIONS_PATH, MATLAB_CONVERT_FILENAME)
MATLAB_ALIGN2_PATH = os.path.join(MATLAB_FUNCTIONS_PATH, MATLAB_ALIGN2_FILENAME)
SPM_PREPROCESSING_BATCH_PATH = os.path.join(MATLAB_FUNCTIONS_PATH, SPM_PREPROCESSING_BATCH_FILENAME)
SPM_REGRESS_BATCH_PATH = os.path.join(MATLAB_FUNCTIONS_PATH, SPM_REGRESS_BATCH_FILENAME)

# tags to indicate automatic modifications in OpenNFT.py operated by fdm
OPENNFT_EDITED_BLOCK_START = '### EDITED BY fdm. Manual modification may break fdm (un)installation and operation'
OPENNFT_EDITED_BLOCK_END = '### end of fdm EDITED BLOCK'

# name of shared engine
MATLAB_SHARED_ENGINE_NAME = "FDM"

# regression batch defaults
REGRESSION_SMOOTH_FWHM = [6, 6, 6]
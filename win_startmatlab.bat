rem
rem This batch file starts multiple Matlab on win
rem Only for troubleshooting
rem IMPORTANT: Specify the absolute path to appropriate Matlab with installed Matlab engine
rem __________________________________________________________________________
rem Copyright (C) 2016-2019 OpenNFT.org

"Path\To\bin\matlab" -regserver -desktop -r "matlab.engine.shareEngine('MATLAB_NFB_MAIN_00001')"
"Path\To\bin\matlab" -regserver -nodesktop -r "matlab.engine.shareEngine('MATLAB_NFB_PTB_00001')"
"Path\To\bin\matlab" -regserver -nodesktop -r "matlab.engine.shareEngine('MATLAB_NFB_SPM_00001')"
rem uncomment for DCM feedback
rem "Path\To\bin\matlab" -regserver -nodesktop -r "matlab.engine.shareEngine('MATLAB_NFB_MODEL_HELPER_00001')"

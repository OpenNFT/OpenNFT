.. _uninstall:

Uninstall
=========

Uninstalling (installations using venv)
---------------------------------------

- Remove python virtual environment directory OpenNFT_venv (Administrator not required)
- Uninstall MATLAB (if it is needed)
- Uninstall Python (if it is needed)

Uninstalling (installations without using venv)
-----------------------------------------------

- Remove Python Matlab engine API: Remove installed matlab engine files from Python site-packages directory: pythonroot\Lib\site-packages\matlab
- Uninstall PyQt5 via uninstaller (for Python 3.4) or use `pip uninstall pyqt5` (for Python 3.5)
- Uninstall other dependencies python packages from cmd:

.. code-block::

    cd c:\OpenNFT
    pip uninstall pyqtgraph
    pip uninstall watchdog
    pip uninstall numpy

- Remove MATLAB toolboxes (if it is needed):
    - remove jsonlab folder from matlabroot/toolboxes
    - remove paths to SPM from Matlab, delete SPM12 folder
- Uninstall PTB toolbox (if it is needed)
- Uninstall Python (if it is needed)
- Uninstall MATLAB (if it is needed)


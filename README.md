# OpenNFT
OpenNFT is an integrated software package designed for neurofeedback training. It constitutes the core technical framework for developments in this exciting new field of neuroimaging. OpenNFT is based on best practices of Python and Matlab software and incorporates, but is not limited to, the functionality of the SPM and Psychtoolbox software suits. An integrated Python/Matlab framework is specifically selected to address the needs of neurofeedback developers and users with different background, which allows for flexibility in developments and implementations without compromising for speed and functionality. More specifically, the OpenNFT’s GUI, synchronization module, and multi-processing core are implemented in Python, whilst computational modules for neurofeedback are implemented in Matlab.

Refer to www.OpenNFT.org and to our Neuroimage manuscript ["OpenNFT: An open-source Python/Matlab framework for real-time fMRI neurofeedback training based on activity, connectivity and multivariate pattern analysis"](http://www.sciencedirect.com/science/article/pii/S1053811917305050) for further description.
Direct link to [OpenNFT manual](https://github.com/OpenNFT/opennft.github.io/blob/master/OpenNFT_Manual_v1.0.pdf).
Note, we are still tuning our pre-release version. Please check the updates regularly.

## Installation (based on the [OpenNFT manual](https://github.com/OpenNFT/opennft.github.io/blob/master/OpenNFT_Manual_v1.0.pdf))
1. Prerequisites
	- MATLAB
		- Image Processing Toolbox
		- Statistics and Machine Learning Toolbox
	- [Miniconda3](https://docs.conda.io/en/latest/miniconda.html)
	- [Git](https://git-scm.com/downloads): for installing SPM, Psychtoolbox and pyniexp

2. MATLAB Toolboxes
	- [SPM12](https://github.com/spm/spm12.git)
	- [Psychtoolbox 3](https://github.com/Psychtoolbox-3/Psychtoolbox-3.git)
	- [JSONlab](https://uk.mathworks.com/matlabcentral/mlc-downloads/downloads/submissions/33381/versions/22/download/zip)

3. Install Python packages in virtual environment (OpenNFT_venv)\
	`conda create --name OpenNFT_venv python=3.5`\
	`conda activate OpenNFT_venv`\
	`cd "<MATLABROOT>\extern\engines\python"`\
  `python setup.py build --build-base="<CONDAROOT>\envs\OpenNFT_venv\Lib\site-packages\MatlabEngineBuild" install`\
	`conda install pip setuptools`\
	`pip install PyQT5`\
	`pip install PyQT5-tools`\
	`pip install watchdog`\
	`pip install --no-deps git+https://github.com/pyqtgraph/pyqtgraph.git`\
	`pip install http://www.silx.org/pub/wheelhouse/numpy-1.13.1+mkl-cp35-cp35m-win_amd64.whl`
	
  - For MRpulse\
    `pip install pywin32`\
    `pip install pyHook-1.5.1-cp35-cp35m-win_amd64.whl` (from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyhook)
	
  - For UDP (feedback) transfers
    `pip install git+https://github.com/tiborauer/pyniexp.git`

## Demo dataset
https://github.com/OpenNFT/OpenNFT_Demo/releases  
#### N.B.:
Use the updated Setup and Protocol files provided with OpenNFT - https://github.com/OpenNFT/OpenNFT/tree/master/ini



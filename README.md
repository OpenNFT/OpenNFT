# OpenNFT
OpenNFT is an integrated software package designed for neurofeedback training. It constitutes the core technical framework for developments in this exciting new field of neuroimaging. OpenNFT is based on best practices of Python and Matlab software and incorporates, but is not limited to, the functionality of the SPM and Psychtoolbox software suits. An integrated Python/Matlab framework is specifically selected to address the needs of neurofeedback developers and users with different background, which allows for flexibility in developments and implementations without compromising for speed and functionality. More specifically, the OpenNFT’s GUI, synchronization module, and multi-processing core are implemented in Python, whilst computational modules for neurofeedback are implemented in Matlab.

Refer to www.OpenNFT.org and to our Neuroimage manuscript ["OpenNFT: An open-source Python/Matlab framework for real-time fMRI neurofeedback training based on activity, connectivity and multivariate pattern analysis"](http://www.sciencedirect.com/science/article/pii/S1053811917305050) for further description.
Direct link to [OpenNFT manual](https://github.com/OpenNFT/opennft.github.io/blob/master/OpenNFT_Manual_v1.0.pdf).
Note, we are still tuning our pre-release version. Please check the updates regularly.

## Installation (based on the [OpenNFT manual](https://github.com/OpenNFT/opennft.github.io/blob/master/OpenNFT_Manual_v1.0.pdf))

### Prerequisites
- MATLAB (x64) `>= R2016b`
    - Image Processing Toolbox
    - Statistics and Machine Learning Toolbox
- Python (x64) `>= 3.5, <= 3.6`, for example [Miniconda3](https://docs.conda.io/en/latest/miniconda.html)
- [Git](https://git-scm.com/downloads): for installing SPM, Psychtoolbox, OpenNFT

### Install MATLAB Toolboxes
- [SPM12](https://github.com/spm/spm12.git)
- [Psychtoolbox 3](https://github.com/Psychtoolbox-3/Psychtoolbox-3.git)
- [JSONlab](https://uk.mathworks.com/matlabcentral/mlc-downloads/downloads/submissions/33381/versions/22/download/zip)

### Install OpenNFT in virtual environment (OpenNFT_venv) with conda and Python 3.5
- `$ conda create --name OpenNFT_venv python=3.5`
- `$ conda activate OpenNFT_venv`
- `(OpenNFT_venv)$ conda install pip setuptools`
- (optional for numpy+MKL) `(OpenNFT_venv)$ pip install http://www.silx.org/pub/wheelhouse/numpy-1.13.1+mkl-cp35-cp35m-win_amd64.whl`
- `(OpenNFT_venv)$ pip install git+https://github.com/OpenNFT/OpenNFT.git --install-option "--matlab-root=<MATLABROOT>"`

Also if you do not set install option `--matlab-root` we try to find Matlab automatically.
You can check installation result using `-v` (verbose) option:

```
(OpenNFT_venv)$ pip install git+https://github.com/OpenNFT/OpenNFT.git -v
```

**NOTE**: 
If you use Windows and MATLAB has been installed to default direcory (Program Files) you need 
Administrator rights for installing Matlab Engine for Python (You need to install OpenNFT via pip as Administrator).

Also you can install OpenNFT from your working directory (OpenNFT project root directory):

```
(OpenNFT_venv)$ pip install /path/to/OpenNFT/root/dir/
```

or:

```
(OpenNFT_venv)$ cd /path/to/OpenNFT/root/dir/
(OpenNFT_venv)$ pip install .
```

Also you can use option `-e/--editable` for installing in [editable mode](https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs) (mode for development):

```
(OpenNFT_venv)$ pip install -e .
(OpenNFT_venv)$ pip list
Package               Version    Location
--------------------- ---------- -----------------------------
...
matlabengineforpython R2016b
...
numpy                 1.16.2+mkl
OpenNFT               1.0.0rc0   c:\workspace\projects\opennft
...
```

## Running OpenNFT application

Just run the following command:

`(OpenNFT_venv)$ opennft`

or with console window:

`(OpenNFT_venv)$ opennft_console`

## Demo dataset
https://github.com/OpenNFT/OpenNFT_Demo/releases 
 
#### N.B.:
Use the updated Setup and Protocol files provided with OpenNFT - https://github.com/OpenNFT/OpenNFT/tree/master/opennft/configs

# OpenNFT
OpenNFT is an integrated software package designed for neurofeedback training. It constitutes the core technical framework for developments in this exciting new field of neuroimaging. OpenNFT is based on best practices of Python and Matlab software and incorporates, but is not limited to, the functionality of the SPM and Psychtoolbox software suits. An integrated Python/Matlab framework is specifically selected to address the needs of neurofeedback developers and users with different background, which allows for flexibility in developments and implementations without compromising for speed and functionality. More specifically, the OpenNFT’s GUI, synchronization module, and multi-processing core are implemented in Python, whilst computational modules for neurofeedback are implemented in Matlab.

Refer to www.OpenNFT.org and to our Neuroimage manuscript ["OpenNFT: An open-source Python/Matlab framework for real-time fMRI neurofeedback training based on activity, connectivity and multivariate pattern analysis"](http://www.sciencedirect.com/science/article/pii/S1053811917305050) for further description.
Direct link to [OpenNFT manual](https://github.com/OpenNFT/opennft.github.io/blob/master/OpenNFT_Manual_v1.0.pdf).
Note, we are still tuning our pre-release version. Please check the updates regularly.

## Additional note for this fork (tiborauer)
TCP/UDP trasfer now uses the pyniexp package, which you can install with:
`pip install git+https://github.com/tiborauer/pyniexp.git`
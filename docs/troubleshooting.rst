.. _troubleshooting:

Troubleshooting
===============

Caveats
-------

Configuration files (ini files) as operating system dependent
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

All settings in the ini files, for example and most importantly the path definitions follow the conventions of your host operating system. E.g., use \ as file separator in Windows and / in a Unix-based system such as macOS.

DCM-based neurofeedback is based on DCM10
+++++++++++++++++++++++++++++++++++++++++

The currently implemented version of DCM neurofeedback is based on Koush et al., 2013 and 2015 publications where DCM10 as implemented in SPM8 (``spm_dcm_estimate_rt()``, ``spm_nlsi_GN_rt()``) was used. Other versions of DCM use different estimation methods and might fail to reproduce the same results and would require an additional testing.

SPM preprocessing is optimized for real-time applications
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Note the differences between the real-time modifications of the SPM12 inbuilt preprocessing functions (``spm_realign_rt()``, ``spm_reslice_rt()``) and their SPM12 analogues. Applied modifications have a sufficient quality level for real-time applications, but they are not necessarily matching your local SPM setup.

Spatial orientation of input data
+++++++++++++++++++++++++++++++++

Generally, you are advised to carefully check the spatial orientation of all the images provided to the software. Our software is independent of data spatial orientation, which is often a function of acquisition parameters. Unfortunately, most Phillips MR scanner setups do not provide adequate image header information when performing a real-time export. Additionally, Phillips real-time data may require a 180-degree flip to match the proper EPI template.

Optimize signal processing settings
+++++++++++++++++++++++++++++++++++

The configuration of the optimal signal processing settings depends on the experimental design and acquisition parameters. E.g., see Koush et al. 2012 for the setup of a Kalman filter.

Possible Matlab engine startup failure
++++++++++++++++++++++++++++++++++++++

Normally, pressing Initialize button we obtain one Matlab session running in desktop mode (with visible GUI) and two or three running without GUI. If you get a problem with Matlab startup after pressing Initialize, you could use batch files for starting Matlab manually. Run the win_startmatlab.bat for Windows system or macos_startmatlab.sh for macOS (see also Sections: :ref:`7_2_6` :ref:`7_2_7` :ref:`7_2_8`).

Runtime errors and troubleshooting
----------------------------------

Real-time exported files not found in watch folder
++++++++++++++++++++++++++++++++++++++++++++++++++

Please check that the real-time export is properly set up on your scanner and the host computer that is used for OpenNFT. If files are exported correctly, review if First File Path is set to the correct destination and the MRI Watch Folder is accessible.

- Press 'Review Parameters' and check the status of First File Path. If you pressed the Setup button and the field is empty indicates that you might have used an invalid syntax to specify the First File Name. Valid formats are:
    - Explicit file names that indicate the first file of the real-time export. Examples:
        - `001_000007_000001.dcm`
        - `001_000007_000001` (file extension will be added based on the MRI Data Type)
    - Template based mechanisms to fill parts of the filename with variables that are defined in the GUI. `{variable name}` defines a variable as specified by the caption in the OpenNFT GUI (e.g., Subject ID), `{#}` refers to the iteration/volume number, and `{…:06}` can be used to set a number format (e.g, 6 digits, zero fill, i.e., 000001). Variable names are case insensitive and spaces are ignored. Examples:
        - `001_{Image Series No:06}_{#:06}.dcm`
        - `{Project Name}/{Subject ID}/{NR Run No:03}_{Image Series No:06}_{#:06}.dcm`

This means users can easily adapt the file locations / file names to their scanner environment

- Check the status feedback:
    - `MRI Watch folder` exists indicates that the MRI watch folder was found. `MRI Watch folder does not exist` might indicate an error. However, this is not necessarily always the case, given that the folder will be created during image export in certain real-time setups (e.g., Philips DRIN dumper creates a run folder for each new export, e.g., c:\drin\0001, 0002, etc.)

    - `First file does not exist` indicates that OpenNFT has not located the first file of the image series during setup. This is desired in normal online mode operations, as the file export has not yet started. On the other hand, `First file exists` shows that the folder is not empty and might indicate that the wrong folder is used (e.g., the previous run). However, in offline mode, which can be used for offline testing, it is expected that the first file is already available.

Undefined function 'spm_select' for input arguments of type 'char'
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Make sure that SPM is installed and MATLAB is able to locate it in your system path. To test if the correct SPM version is found use `which spm` in a MATLAB window.

Undefined function or variable 'bwperim'
++++++++++++++++++++++++++++++++++++++++

Make sure that you have installed MATLAB’s Image Processing toolbox.

Undefined function or variable 'zscore'
+++++++++++++++++++++++++++++++++++++++

Make sure that you have installed MATLAB’s Statistics and Machine Learning toolbox.

Error when loading DICOM files
++++++++++++++++++++++++++++++

There is a known bug in the current implementation of MATLAB’s dicominfo.m. We used the following modifications to fix the problem:

Line #336

`personName = struct([]);` changed to

`personName = repmat(makePerson(pnParts),[1,numel(splitRawData)]);`

Line #353

`%personName = makePerson(pnParts);` changed to

`personName(p) = makePerson(pnParts);`

.. _7_2_6:

Error when starting Matlab processes on macOS
+++++++++++++++++++++++++++++++++++++++++++++

We observed problems when starting Matlab instances on macOS from within OpenNFT, either during startup or using the `Initialize` button. The way to fix this problem is to independently start and share the required Matlab instances (main, PTB, and SPM instances) using the macOS command line:

`/Applications/MATLAB_R2016b.app/bin/matlab -desktop -r "matlab.engine.shareEngine('MATLAB_NFB_MAIN_00001')"`

`/Applications/MATLAB_R2016b.app/bin/matlab -nodesktop -r "matlab.engine.shareEngine('MATLAB_NFB_PTB_00001')"`

`/Applications/MATLAB_R2016b.app/bin/matlab -nodesktop -r "matlab.engine.shareEngine('MATLAB_NFB_SPM_00001')"`

`/Applications/MATLAB_R2016b.app/bin/matlab -nodesktop -r "matlab.engine.shareEngine('MATLAB_NFB_MODEL_HELPER_00001')"`

The easiest way is to use our macos_startmatlab.sh to run the Matlab instances. Fourth instance is optional, see config.py for details.

.. _7_2_7:

Single-case error when starting Matlab processes on Win workstation with multiple accounts
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

On one workstation with multiple accounts and different account rights, we observed the problem with Matlab instances during startup, which was very similar to that described for macOS (Section :ref:`7_2_6`). However, the solution for macOS didn’t work unless an option `-regserver` was added:

.. code-block::

    "Path\To\bin\matlab" -regserver -desktop -r "matlab.engine.shareEngine('MATLAB_NFB_MAIN_00001')"
    "Path\To\bin\matlab" -regserver -nodesktop -r "matlab.engine.shareEngine('MATLAB_NFB_PTB_00001')"
    "Path\To\bin\matlab" -regserver -nodesktop -r "matlab.engine.shareEngine('MATLAB_NFB_SPM_00001')"
    "Path\To\bin\matlab" -regserver -nodesktop -r "matlab.engine.shareEngine('MATLAB_NFB_MODEL_HELPER_00001')"

The easiest way to solve it is to use win_startmatlab.bat to run the Matlab instances. Fourth instance is optional, see config.py for details.

.. _7_2_8:

Single-case error on Win for pop-up file dialog
+++++++++++++++++++++++++++++++++++++++++++++++

On the same workstation as in Section :ref:`7_2_7`, we observed the problem with opening the dialog windows. The problem is similar to described in `Stack Overflow <http://stackoverflow.com/questions/33145515/pythonw-exe-has-stopped-working-when-running-qfiledialog-getexistingdirectory>`_ . This problem was solved by adding `options=QFileDialog.DontUseNativeDialog` to the QFileDialog.getOpenFileName() call. Set DONOT_USE_QFILE_NATIVE_DIALOG flag in config.py in case of the similar problem.


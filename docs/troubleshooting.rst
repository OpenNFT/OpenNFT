.. _troubleshooting:

Troubleshooting
===============

Caveats
-------

Python Installations
++++++++++++++++++++

Python installations may require forced installations/upgrades using the following commands

for ``pip``:

.. code-block::

    python -m pip install --upgrade pip
    python -m pip install --upgrade --force-reinstall pip

and for ``wheel``:

.. code-block::

    python -m pip install --upgrade pip setuptools wheel
    python -m pip install --upgrade --force-reinstall pip setuptools wheel


Paths in the Configuration files
++++++++++++++++++++++++++++++++

All settings and path definitions in the ``*.ini`` files follow conventions of your host operating system, e.g., use '\\' as file separator in Windows and '/' in Unix-based systems.

DCM-based neurofeedback is based on DCM10
+++++++++++++++++++++++++++++++++++++++++

The currently implemented version of DCM neurofeedback is based on Koush et al., 2013 and 2015 publications where DCM10 is used (``spm_dcm_estimate_rt()``, ``spm_nlsi_GN_rt()``). Other versions of DCM may use different estimation methods and require additional testings.

SPM preprocessing is optimized for real-time applications
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Note the differences between the real-time modifications of the SPM12 inbuilt preprocessing functions (``spm_realign_rt()``, ``spm_reslice_rt()``) and their SPM12 analogues. Applied modifications have a sufficient quality level for real-time applications, but they are not necessarily matching your local SPM setup.

Spatial orientation of input data
+++++++++++++++++++++++++++++++++

Generally, you are advised to carefully check the spatial orientation of all the images provided to the software. Our software is independent of data spatial orientation, which is often a function of acquisition parameters. Unfortunately, most Phillips MR scanner setups do not provide adequate image header information when performing a real-time export. Additionally, Phillips real-time data may require a 180-degree flip to match the proper EPI template.

Optimize signal processing settings
+++++++++++++++++++++++++++++++++++

The configuration of the optimal signal processing settings depends on the experimental design and acquisition parameters, see Koush et al. 2012 for the setup of a Kalman filter.

Possible Matlab engine startup failure
++++++++++++++++++++++++++++++++++++++

If you get a problem with Matlab startup after pressing Initialize, you could use ``run_matlab`` command in terminal and/or contact developers via GitHub.

Runtime errors and troubleshooting
----------------------------------

Real-time exported files not found in watch folder
++++++++++++++++++++++++++++++++++++++++++++++++++

Please check that the real-time data export is properly set up on your scanner and the host computer that is used for OpenNFT. If files are exported correctly, review if the First File Path is set to the correct destination and the MRI Watch Folder is accessible.

- Press 'Review Parameters' and check the status of the First File Path. If you pressed the Setup button and the field is empty indicates that you might have used an invalid syntax to specify the First File Name. Valid formats are:
    - Explicit file names that indicate the first file of the real-time export. Examples:
        - `001_000007_000001.dcm`
        - `001_000007_000001` (file extension will be added based on the MRI Data Type)
    - Template based mechanisms to fill parts of the filename with variables that are defined in the GUI. `{variable name}` defines a variable as specified by the caption in the OpenNFT GUI (e.g., Subject ID), `{#}` refers to the iteration/volume number, and `{…:06}` can be used to set a number format (e.g, 6 digits, zero fill, i.e., 000001). Variable names are case insensitive and spaces are ignored. Examples:
        - `001_{Image Series No:06}_{#:06}.dcm`
        - `{Project Name}/{Subject ID}/{NR Run No:03}_{Image Series No:06}_{#:06}.dcm`

This means users can easily adapt the file locations and file names to their scanner environment.

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

There is a known bug in some implementations of MATLAB’s dicominfo.m. This modification can be used to fix it:

Line #336

`personName = struct([]);` changed to

`personName = repmat(makePerson(pnParts),[1,numel(splitRawData)]);`

Line #353

`%personName = makePerson(pnParts);` changed to

`personName(p) = makePerson(pnParts);`

.. _7_2_8:

Single-case error on Win for pop-up file dialog
+++++++++++++++++++++++++++++++++++++++++++++++

We observed the problem with opening the dialog windows. The problem is similar to described in `Stack Overflow <http://stackoverflow.com/questions/33145515/pythonw-exe-has-stopped-working-when-running-qfiledialog-getexistingdirectory>`_ . This problem was solved by adding `options=QFileDialog.DontUseNativeDialog` to the QFileDialog.getOpenFileName() call. Set DONOT_USE_QFILE_NATIVE_DIALOG flag in config.py in case of the similar problem.

.. _possible_error:

Run configuration problem
+++++++++++++++++++++++++

Sometimes it is necessary to select 'Store as project file'. Double-check if PyCharm switches to newly configured venv in the Terminal command line, if not you have to try to close and open the Terminal window.
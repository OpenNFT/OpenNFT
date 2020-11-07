.. _testing_opennft:

Testing OpenNFT
===============

There are two ways to test the OpenNFT functionality without concurrent real-time data acquisition. In offline mode, data is read from a folder that already contains the whole data set from a previous measurement. In online mode, the files are expected to arrive sequentially in the Watch Folder, as it happens during scanning.

Online OpenNFT mode using simulated fMRI data export
----------------------------------------------------

* Open ``testRTexp.py`` and set the source and destination data folders to perform the delayed copying of the fMRI data files. The simulated TR can be specified by the ``sleep()`` function in seconds.
* Launch OpenNFT, review the parameters and, in particular, uncheck the ``Offline mode`` checkbox before pressing Setup. Start the framework. It is now waiting for the first data file in the specified destination folder, i.e., the ``MRI Watch Folder``.
* Launch the testRTexp.py using

.. code-block::

    python Path\To\tests\testRTexp.py

Processing time in the right upper OpenNFT corner displays the time it takes to process each scan, which must be less than your simulated TR to satisfy the real-time property of the neurofeedback pipeline.

Offline OpenNFT mode using already acquired fMRI data
-----------------------------------------------------

* Launch OpenNFT, review the parameters and, in particular, check the ``Offline mode`` checkbox before pressing Setup. Press the Start button. OpenNFT is now processing the data in the ``MRI Watch folder`` as fast as possible.

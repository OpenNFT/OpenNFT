.. _quickstart:

Quickstart
==========

Before running the project, you should know, that you can disable following procedures via config.py:

* real-time quality assessment (USE_RTQA flag)
* incremental GLM (USE_IGLM flag)
* region of interest visualization (USE_ROI flag)

Initialization
--------------------------

Before you run the scanning process you need to initialize MATLAB sessions. You can do it two ways:

1. By pushing ``Initialize`` button

.. image:: _static/quickstart_1.png

2. Or by typing following command

.. code-block::

        run_matlab

After this, MATLAB sessions will be initialized.

.. note::

    You can change ``-nodesktop`` or ``-desktop`` parameter for MATLAB sessions in opennft/config.py file

Setup
------------------

After initialization you can choose Setup file of your scanning. This file contains the set of parameters, which you can change before pressing ``Setup`` button.

.. _here: https://github.com/OpenNFT/OpenNFT_Demo/releases

Configure files for demo data are located in /opennft/configs/
Demo data can be found here_.

.. image:: _static/quickstart_2.png

.. note::

    If you run OpenNFT on offline data - enable ``Offline mode``
    More about testing OpenNFT on different data is on :ref:`testing` page.


If you enable rtQA, you can check available modes for your experiment.

.. image:: _static/quickstart_3.png

Run
---------------

During the run you can change parameters of 3D image visualization

* View mode: mosaic, triplanar anatomy, triplanar EPI
* Opacity threshold
* Positive and negative statistical map (not available in rtQA mode)
* Lower and upper thresholds for positive and negative maps visualization

.. image:: _static/quickstart_4.png

Stop and Exit
--------------------------

To stop scanning process press ``Stop`` button. All data will be saved to /Your/Data/Path/NF_Data_1

After exit all MATLAB sessions will be terminated.


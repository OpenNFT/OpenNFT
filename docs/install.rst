.. _install:

Installation
============

The installation process is tested on three x86_64 platforms:

* Linux (Ubuntu 18.04)
* Mac OS (High Sierra 10.13.6)
* Windows 10

Prerequisites
-------------

The following software should be installed:

* `Git <https://git-scm.com/downloads>`_: for installing OpenNFT and, optionally, for installing SPM and Psychtoolbox
* MATLAB x86_64 R2017b or above
    - Image Processing Toolbox
    - Statistics and Machine Learning Toolbox
    - `SPM12 <https://github.com/spm/spm12>`_
    - `Psychtoolbox 3 <https://github.com/Psychtoolbox-3/Psychtoolbox-3>`_
    - `JSONlab <https://github.com/fangq/jsonlab/releases>`_
    - `prepNFB <https://github.com/lucp88/prepNFB>`_ (optional)
* `Python <https://www.python.org/downloads/>`_ x86_64 from 3.6.0 to 3.8.6

.. note::

    The minimum system requirements for OpenNFT are 8 GB RAM, i5 CPU with 2 or 4 free cores for two modes of the software using 3 or 4 Matlab processes, respectively, which needs to be compromised with the neurofeedback study design complexity, computational demands and the repetition time of the data acquisition.
    The recommended system configuration is 16 GB RAM and i7 CPU with 4 free cores. The maximum number of Matlab processes is defined by the end-user and is limited by the local workstation capabilities.


Install OpenNFT
---------------

We recommend a virtual environment for installing OpenNFT.

Create and Activate Virtual Environment
++++++++++++++++++++++++++++++++++++++++

.. rubric:: Unix (Linux, MacOS)

.. note::

    For Linux system you may first need the following command:

    .. code-block::

        sudo apt install python3-venv

.. code-block::

    cd /path/to/your/workspace/directory
    python3 -m venv opennft-venv
    source opennft-venv/bin/activate
    python -m pip install -U pip setuptools wheel

.. rubric:: Windows

.. code-block::

    cd C:\path\to\your\workspace\directory
    py -3 -m venv opennft-venv
    opennft-venv\Scripts\activate.bat
    python -m pip install -U pip setuptools wheel

Install from GitHub
+++++++++++++++++++

.. note::

    It is assumed that the virtual environment has been created and activated.
    Please see above how to create and activate the virtual environment on your platform.

Run the command:

.. code-block::

    pip install git+https://github.com/OpenNFT/OpenNFT.git

.. note::

    If you do not have the write access in ``MATLABROOT``, the installer will try to
    install "Matlab Engine for Python" with Administrator/root privileges, i.e., elevating privileges via UAC/sudo.

Install from Project Directory
++++++++++++++++++++++++++++++

Alternatively, you can install OpenNFT from your working directory (OpenNFT project root directory).
It is convenient if you are working on the project or want to contribute.

.. rubric:: Cloning the project repository

First, the project repository (or its fork) is cloned:

.. code-block::

    cd /path/to/your/workspace/directory
    git clone --recurse-submodules https://github.com/OpenNFT/OpenNFT.git

.. rubric:: Install the project dependencies

Second, project dependencies are installed:

.. note::

    The virtual environment should be activated.
    See above how to create and activate the virtual environment on your platform.

.. code-block::

    pip install -U -r /path/to/your/workspace/directory/OpenNFT/requirements.txt

.. rubric:: Install OpenNFT

Third, OpenNFT is installed:

.. code-block::

    pip install /path/to/your/workspace/directory/OpenNFT/

Additional Notes
++++++++++++++++

For installing in `editable mode <https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs>`_ (development mode), you can use the ``-e/--editable`` option:

.. code-block::

    pip install -e /path/to/your/workspace/directory/OpenNFT/

If there are several MATLAB versions, you have to install requirements and specify the MATLAB root directory during OpenNFT installation.

.. code-block::

    pip install -U pip setuptools wheel
    pip install -U -r /path/to/your/workspace/directory/OpenNFT/requirements.txt
    pip install --install-option "--matlab-root=<MATLABROOT>" /path/to/your/workspace/directory/OpenNFT/

You can use both ``-e/--editable`` and  ``--install-option "--matlab-root=<MATLABROOT>"`` options at the same time:

.. code-block::

    pip install -U pip setuptools wheel
    pip install -U -r /path/to/your/workspace/directory/OpenNFT/requirements.txt
    pip install --install-option "--matlab-root=<MATLABROOT>" -e /path/to/your/workspace/directory/OpenNFT/

.. note::

    If you do not have the write access to ``MATLABROOT``, the installer will try to
    install the "Matlab Engine for Python" with Administrator/root privileges, elevating privileges via UAC/sudo.

.. _check_installation:

Check Installation
------------------

Run the command:

.. code-block::

    pip list

Check the existence of ``matlabengineforpython`` and ``OpenNFT`` names. If the Installation went well, you should see them as:

.. code-block::

    Package               Version    Location
    --------------------- ---------- -----------------------------
    ...
    matlabengineforpython R2017b
    ...
    OpenNFT               1.0.0   c:\workspace\projects\OpenNFT
    ...

.. _run_application:

Run Application
---------------

To start OpenNFT, run the command in the Terminal:

.. code-block::

    opennft

.. _install:

Installing
==========

The installation process has been tested on three x86_64 platforms:

* Linux (Ubuntu 18.04)
* Mac OS
* Windows 10

Prerequisites
-------------

Firstly, the following software should be installed:

* `Git <https://git-scm.com/downloads>`_: for installing SPM, Psychtoolbox and OpenNFT
* MATLAB x86_64 R2017b or above
    - Image Processing Toolbox
    - Statistics and Machine Learning Toolbox
    - `SPM12 <https://github.com/spm/spm12>`_
    - `Psychtoolbox 3 <https://github.com/Psychtoolbox-3/Psychtoolbox-3>`_
    - `JSONlab <https://github.com/fangq/jsonlab>`_
    - `prepNFB <https://github.com/lucp88/prepNFB>`_ (optional)
* `Python <https://www.python.org/downloads/>`_ x86_64 3.6-3.8


Installing OpenNFT
------------------

We recommend using a virtual environment for installing OpenNFT.

Creating Virtual Environment
++++++++++++++++++++++++++++

.. rubric:: Linux

.. code-block:: bash

    sudo apt install python3-venv
    cd /path/to/your/workspace/directory
    python3 -m venv opennft-venv
    source opennft-venv/bin/activate
    python -m pip install -U pip setuptools wheel

.. rubric:: Mac OS

.. todo::

    Add instructions for macos

.. rubric:: Windows

.. code-block:: bat

    cd C:\path\to\your\workspace\directory
    py -3 -m venv opennft-venv
    opennft-venv\Scripts\activate.bat
    python -m pip install -U pip setuptools wheel

Installing from GitHub
++++++++++++++++++++++

.. note::

    It is assumed that the virtual environment has been created and activated.
    Please see above how to create and activate the virual environment on your platform.

Run the command:

.. code-block::

    pip install git+https://github.com/OpenNFT/OpenNFT.git

.. note::

    If you do not have write access in ``MATLABROOT`` the installer will try to
    install "Matlab Engine for Python" with Administrator/root privileges
    (It elevates privileges via UAC/sudo).

Installing from Project Directory
+++++++++++++++++++++++++++++++++

Also you can install OpenNFT from your working directory (OpenNFT project root directory).
It is convenient if you working on the project or you want to contribute.

.. rubric:: Cloning the project repository

Firstly, the project reposiory (or its fork) should be cloned:

.. code-block::

    cd /path/to/your/workspace/directory
    git clone --recurse-submodules https://github.com/OpenNFT/OpenNFT.git


.. rubric:: Install the project dependencies

.. note::

    The virual environment should be activated.
    See above how to create and activate the virual environment on your platform.

.. code-block::

    pip install -U -r /path/to/your/workspace/directory/OpenNFT/requirements.txt


.. rubric:: Install OpenNFT

.. code-block::

    pip install /path/to/your/workspace/directory/OpenNFT/

Also you can use ``-e/--editable`` option for installing in `editable mode <https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs>`_ (mode for development):

.. code-block::

    pip install -e /path/to/your/workspace/directory/OpenNFT/

Also you can specify ``MATLABROOT`` if the installer can't find MATLAB or you have several installed MATLAB versions:

.. code-block::

    pip install --install-option "--matlab-root=<MATLABROOT>" /path/to/your/workspace/directory/OpenNFT/

Where ``MATLABROOT`` is a path to MATLAB root directory.

You can use both ``-e/--editable`` and  ``--install-option "--matlab-root=<MATLABROOT>"`` options at the time.

.. code-block::

    pip install --install-option "--matlab-root=<MATLABROOT>" -e /path/to/your/workspace/directory/OpenNFT/

.. note::

    If you do not have write access in ``MATLABROOT`` the installer will try to
    install "Matlab Engine for Python" with Administrator/root privileges
    (It elevates privileges via UAC/sudo).


Checking Installation
---------------------

Run the command:

.. code-block::

    pip list

If everything went well, you should see something like this:

.. code-block::

    Package               Version    Location
    --------------------- ---------- -----------------------------
    ...
    matlabengineforpython R2017b
    ...
    OpenNFT               1.0.0   c:\workspace\projects\OpenNFT
    ...

Check the existence of ``matlabengineforpython`` and ``OpenNFT`` names.

Running
-------

You can now start OpenNFT. Run the command:

.. code-block::

    opennft

Also you can run shared MATLAB sessions for reusing them before running OpenNFT in separated terminal:

.. code-block::

    run_matlab

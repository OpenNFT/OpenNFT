.. _install_pycharm:

Installation via PyCharm
========================

The installation process is tested on three x86_64 platforms:

* Linux (Ubuntu 18.04)
* Mac OS (High Sierra 10.13.6)
* Windows 10

Prerequisites
-------------

The following software should be installed:

* `Git <https://git-scm.com/downloads>`_: for installing SPM, Psychtoolbox and OpenNFT
* PyCharm `Professional or Community <https://www.jetbrains.com/pycharm/download/>`_
* MATLAB x86_64 R2017b or above
    - Image Processing Toolbox
    - Statistics and Machine Learning Toolbox
    - `SPM12 <https://github.com/spm/spm12>`_
    - `Psychtoolbox 3 <https://github.com/Psychtoolbox-3/Psychtoolbox-3>`_
    - `JSONlab <https://github.com/fangq/jsonlab>`_
    - `prepNFB <https://github.com/lucp88/prepNFB>`_ (optional)
* `Python <https://www.python.org/downloads/>`_ x86_64 3.6.0-3.8.6


Install OpenNFT
---------------

Create Project by cloning from GitHub repository
++++++++++++++++++++++++++++++++++++++++++++++++++

.. image:: _static/pycharminstall_1.png

Use the link to the main repository,

.. code-block::

    https://github.com/OpenNFT/OpenNFT.git

or, if you plan to contribute to the project, create the fork repository and use your own link

.. code-block::

    https://github.com/your_github_name/OpenNFT.git

.. image:: _static/pycharminstall_2.png

Create Virtual Environment
++++++++++++++++++++++++++++

To create virtual environment, go to File -> Settings -> Project Interpreter

.. image:: _static/pycharminstall_3.png

Set the new virtual environment location and choose the interpreter

.. image:: _static/pycharminstall_4.png


Install from Project Directory
++++++++++++++++++++++++++++++

.. rubric:: Default installation.

MATLAB will be found automatically

.. code-block::

    pip install -U pip setuptools wheel
    pip install -e .

.. rubric:: Customized installation.

If there are several MATLAB versions, you have to specify the MATLAB root directory

.. code-block::

    pip install -U pip setuptools wheel
    pip install -U -r requirements.txt

To install ``matlabengineforpython`` you can use one of the following methods.

If ...

.. image:: _static/pycharminstall_5.png

.. code-block::

    pip install --install-option "--matlab-root=<MATLABROOT>" -e .

or, if ...

.. code-block::

    cd /Path/To/Matlab/Root/extern/engines/python/
    python setup.py build --build-base="C:\Path\To\Project\Directory\Venv_directory\Lib\site-packages\MatlabEngineBuild" install
    cd /Path/To/Project/Directory/

Examples of MATLABROOT and build-base paths

.. code-block::

   pip install --install-option "--matlab-root=C:\Program Files\MATLAB\R2018b" -e .

   python setup.py build --build-base="C:\OpenNFT\OpenNFT_venv_36\Lib\site-packages\MatlabEngineBuild" install

Check Installation
------------------

Check the installation before run: :ref:`check_installation`


Run Application
---------------

Before run you need to create Run Configuration

.. image:: _static/pycharminstall_6.png

.. image:: _static/pycharminstall_7.png

Specify Module name as "opennft" (NOT Script path) and Project interpreter according to your venv

.. image:: _static/pycharminstall_8.png

Sometimes you can't create configuration without 'Store as project file' enabled. :ref:`possible_error`

And then press run

.. image:: _static/pycharminstall_9.png


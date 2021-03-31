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

.. rubric:: Default installation

MATLAB will be found automatically

.. code-block::

    pip install -U pip setuptools wheel
    pip install -e .

.. rubric:: Customized installation

If there are several MATLAB versions, you have to install requirements and specify the MATLAB root directory during OpenNFT installation.

.. code-block::

    pip install -U pip setuptools wheel
    pip install -U -r requirements.txt
    pip install --install-option "--matlab-root=<MATLABROOT>" -e .

Check Installation
------------------

Check the installation: :ref:`check_installation`


Run Application
---------------

Create Run Configuration to run OpenNFT:

.. image:: _static/pycharminstall_5.png

.. image:: _static/pycharminstall_6.png

Specify Module name as "opennft" (NOT Script path) and Project interpreter according to your Virtual Environment:

.. image:: _static/pycharminstall_7.png

Here, to create the configuration the checkbox 'Store as project file' may be required. :ref:`possible_error`

Now you can press the Run button, or run commands in the Terminal: : :ref:`run_application`

.. image:: _static/pycharminstall_8.png

